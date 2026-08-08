#!/usr/bin/env python3
"""leetcode-trainer data operations. stdout: data only. stderr: diagnostics.
Exit 0 ok, 1 violations found, 2 could not run. See references/schema.md.
"""
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone

DATA_HOME = os.path.expanduser("~/.local/share/mosaic/data/leetcode-trainer")
PROBLEMS_DIR = os.path.join(DATA_HOME, "problems")
MANIFEST_PATH = os.path.join(DATA_HOME, "manifest.json")
SCHEMA_VERSION = 1
DIFFICULTIES = {"Easy", "Medium", "Hard"}
SLUG_RE_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789-")


def err(msg):
    print(msg, file=sys.stderr)


def is_valid_slug(slug):
    if not slug or slug.startswith("-") or slug.endswith("-") or "--" in slug:
        return False
    return set(slug) <= SLUG_RE_CHARS


def validate_record(data, expected_slug=None):
    """Returns list of error strings; empty means valid."""
    errors = []
    if not isinstance(data, dict):
        return ["record is not a JSON object"]

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")

    slug = data.get("slug")
    if not isinstance(slug, str) or not is_valid_slug(slug):
        errors.append("slug missing or not kebab-case")
    elif expected_slug and slug != expected_slug:
        errors.append(f"slug '{slug}' does not match filename '{expected_slug}'")

    if not isinstance(data.get("leetcode_id"), int):
        errors.append("leetcode_id missing or not an integer")
    if not isinstance(data.get("title"), str) or not data.get("title").strip():
        errors.append("title missing or empty")
    if data.get("difficulty") not in DIFFICULTIES:
        errors.append(f"difficulty must be one of {sorted(DIFFICULTIES)}")
    topics = data.get("topics")
    if not isinstance(topics, list) or not topics or not all(isinstance(t, str) for t in topics):
        errors.append("topics must be a non-empty list of strings")
    if not isinstance(data.get("source_url"), str) or not data.get("source_url").startswith("http"):
        errors.append("source_url missing or not a URL")

    problem = data.get("problem")
    if not isinstance(problem, dict):
        errors.append("problem section missing")
    else:
        if not isinstance(problem.get("statement_md"), str) or not problem.get("statement_md").strip():
            errors.append("problem.statement_md missing or empty")
        examples = problem.get("examples")
        if not isinstance(examples, list) or not examples:
            errors.append("problem.examples must be a non-empty list")
        else:
            for i, ex in enumerate(examples):
                if not isinstance(ex, dict) or "input" not in ex or "output" not in ex:
                    errors.append(f"problem.examples[{i}] missing input/output")
        if not isinstance(problem.get("constraints"), list):
            errors.append("problem.constraints must be a list (may be empty)")

    intuition = data.get("intuition")
    if not isinstance(intuition, dict):
        errors.append("intuition section missing")
    else:
        if not isinstance(intuition.get("summary_md"), str) or not intuition.get("summary_md").strip():
            errors.append("intuition.summary_md missing or empty")
        if not isinstance(intuition.get("approach_md"), str) or not intuition.get("approach_md").strip():
            errors.append("intuition.approach_md missing or empty")
        if not isinstance(intuition.get("time_complexity"), str):
            errors.append("intuition.time_complexity missing")
        if not isinstance(intuition.get("space_complexity"), str):
            errors.append("intuition.space_complexity missing")
        diagram = intuition.get("diagram")
        if diagram is not None:
            if not isinstance(diagram, dict) or diagram.get("type") not in ("svg", "ascii") or not diagram.get("content"):
                errors.append("intuition.diagram, if present, must be {type: svg|ascii, content: ...}")

    solutions = data.get("solutions")
    if not isinstance(solutions, dict):
        errors.append("solutions section missing")
    else:
        for lang in ("python", "golang"):
            entry = solutions.get(lang)
            if not isinstance(entry, dict) or not isinstance(entry.get("code"), str) or not entry.get("code").strip():
                errors.append(f"solutions.{lang}.code missing or empty")

    return errors


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"no such file: {path}"
    except json.JSONDecodeError as e:
        return None, f"invalid JSON: {e}"


def cmd_validate(args):
    if len(args) != 1:
        err("usage: lc_core.py validate <file>")
        return 2
    data, load_err = load_json(args[0])
    if load_err:
        err(load_err)
        return 2
    # No filename/slug match required here — staging files may be named
    # anything. `add` derives the stored filename from data["slug"] itself;
    # rebuild_manifest() separately guards files already inside problems/.
    errors = validate_record(data)
    if errors:
        for e in errors:
            err(f"  - {e}")
        return 1
    print(f"ok: {data['slug']}")
    return 0


def rebuild_manifest():
    os.makedirs(PROBLEMS_DIR, exist_ok=True)
    entries = []
    for fname in sorted(os.listdir(PROBLEMS_DIR)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(PROBLEMS_DIR, fname)
        data, load_err = load_json(path)
        if load_err:
            err(f"skipping {fname}: {load_err}")
            continue
        errors = validate_record(data, expected_slug=fname[:-5])
        if errors:
            err(f"skipping {fname}: {'; '.join(errors)}")
            continue
        entries.append({
            "id": data["slug"],
            "leetcode_id": data["leetcode_id"],
            "title": data["title"],
            "difficulty": data["difficulty"],
            "topics": data["topics"],
            "schema_version": data["schema_version"],
            "tier": "hot",
        })
    entries.sort(key=lambda e: e["leetcode_id"])
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "problems": entries,
    }
    os.makedirs(DATA_HOME, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=DATA_HOME, suffix=".tmp")
    with os.fdopen(tmp_fd, "w") as f:
        json.dump(manifest, f, indent=2)
    shutil.move(tmp_path, MANIFEST_PATH)
    return entries


def cmd_rebuild_manifest(args):
    entries = rebuild_manifest()
    print(f"manifest rebuilt: {len(entries)} problem(s)")
    print(f"<artifact>: {MANIFEST_PATH}")
    return 0


def cmd_add(args):
    if len(args) != 1:
        err("usage: lc_core.py add <file>")
        return 2
    data, load_err = load_json(args[0])
    if load_err:
        err(load_err)
        return 2
    errors = validate_record(data)
    if errors:
        for e in errors:
            err(f"  - {e}")
        return 1
    slug = data["slug"]
    os.makedirs(PROBLEMS_DIR, exist_ok=True)
    dest = os.path.join(PROBLEMS_DIR, f"{slug}.json")
    replacing = os.path.exists(dest)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=PROBLEMS_DIR, suffix=".tmp")
    with os.fdopen(tmp_fd, "w") as f:
        json.dump(data, f, indent=2)
    shutil.move(tmp_path, dest)
    rebuild_manifest()
    action = "replaced" if replacing else "added"
    print(f"{action}\t{slug}\t{data['difficulty']}\t{dest}")
    print(f"<artifact>: {dest}")
    return 0


def cmd_remove(args):
    if len(args) != 1:
        err("usage: lc_core.py remove <slug>")
        return 2
    slug = args[0]
    target = os.path.join(PROBLEMS_DIR, f"{slug}.json")
    if not os.path.exists(target):
        err(f"no such problem: {slug}")
        return 2
    os.remove(target)
    rebuild_manifest()
    print(f"removed\t{slug}")
    print(f"<artifact>: {MANIFEST_PATH}")
    return 0


def cmd_list(args):
    if not os.path.exists(MANIFEST_PATH):
        rebuild_manifest()
    manifest, load_err = load_json(MANIFEST_PATH)
    if load_err:
        err(load_err)
        return 2
    if not manifest["problems"]:
        print("(no problems authored yet)")
    for p in manifest["problems"]:
        topics = ",".join(p["topics"])
        print(f"{p['leetcode_id']}\t{p['id']}\t{p['difficulty']}\t{topics}")
    print(f"<artifact>: {MANIFEST_PATH}")
    return 0


def cmd_progress(args):
    top100_path = args[0] if args else None
    if not top100_path:
        err("usage: lc_core.py progress <top-100.json>")
        return 2
    top100, load_err = load_json(top100_path)
    if load_err:
        err(load_err)
        return 2
    if not os.path.exists(MANIFEST_PATH):
        rebuild_manifest()
    manifest, load_err = load_json(MANIFEST_PATH)
    if load_err:
        err(load_err)
        return 2
    have = {p["id"] for p in manifest["problems"]}
    want = top100["problems"]
    missing = [p for p in want if p["slug"] not in have]
    extra = sorted(have - {p["slug"] for p in want})
    print(f"progress\t{len(want) - len(missing)}/{len(want)}\tauthored")
    for p in missing:
        print(f"missing\t{p['leetcode_id']}\t{p['slug']}\t{p['difficulty']}")
    if extra:
        print(f"extra\t{len(extra)}\t{','.join(extra)}")
    print(f"<artifact>: {MANIFEST_PATH}")
    return 0 if not missing else 1


def main():
    if len(sys.argv) < 2:
        err("usage: lc_core.py <add|remove|validate|list|progress|rebuild-manifest> [args]")
        return 2
    mode, rest = sys.argv[1], sys.argv[2:]
    dispatch = {
        "add": cmd_add,
        "remove": cmd_remove,
        "validate": cmd_validate,
        "list": cmd_list,
        "progress": cmd_progress,
        "rebuild-manifest": cmd_rebuild_manifest,
    }
    fn = dispatch.get(mode)
    if not fn:
        err(f"unknown mode: {mode}")
        return 2
    return fn(rest)


if __name__ == "__main__":
    sys.exit(main())
