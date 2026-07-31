#!/usr/bin/env python3
"""Batch-update media tags with ffmpeg.

stdout: one line per file acted on (data)   stderr: progress and diagnostics
exit 0 all updated · 1 some failed · 2 cannot run
"""
import json
import os
import shutil
import subprocess
import sys


def update_tags(base_path, mapping_file):
    if not shutil.which("ffmpeg"):
        print('{"status":"error","reason":"ffmpeg not found",'
              '"remedy":"install ffmpeg"}')
        return 2
    try:
        with open(mapping_file) as f:
            files_to_tags = json.load(f)
    except Exception as e:
        print(f'{{"status":"error","reason":"cannot read mapping: {e}"}}')
        return 2

    updated, failed = 0, 0
    for filename, tags in files_to_tags.items():
        file_path = os.path.join(base_path, filename)
        if not os.path.exists(file_path):
            print(f"missing\t{filename}\tno such file")
            failed += 1
            continue

        temp_path = os.path.join(base_path, "temp_" + filename)
        cmd = ["ffmpeg", "-y", "-i", file_path, "-c", "copy"]
        if isinstance(tags, str):
            cmd += ["-metadata", f"artist={tags}"]
            applied = f"artist={tags}"
        elif isinstance(tags, dict):
            for key, value in tags.items():
                cmd += ["-metadata", f"{key}={value}"]
            applied = ",".join(f"{k}={v}" for k, v in tags.items())
        else:
            print(f"skipped\t{filename}\tunsupported mapping type")
            failed += 1
            continue
        cmd.append(temp_path)

        print(f"tagging {filename}", file=sys.stderr)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            os.replace(temp_path, file_path)
            print(f"updated\t{filename}\t{applied}")
            updated += 1
        else:
            # Full ffmpeg stderr stays out of stdout; last line is enough to act on.
            tail = (result.stderr or "").strip().splitlines()
            print(f"failed\t{filename}\t{tail[-1] if tail else 'ffmpeg error'}")
            failed += 1
            if os.path.exists(temp_path):
                os.remove(temp_path)

    print(f"— {updated} updated, {failed} failed", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: batch-tagger.py <directory> <mapping_json>", file=sys.stderr)
        sys.exit(2)
    sys.exit(update_tags(sys.argv[1], sys.argv[2]))
