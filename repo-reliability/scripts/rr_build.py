"""Runner helpers: validate envelopes, collect repo metadata, bundle, stamp report.

Usage:
  rr_build.py validate <envelope.json>
  rr_build.py meta <repo_dir>
  rr_build.py bundle <meta.json> <out.json> <envelope.json>...
  rr_build.py stamp <template.html> <data_dir> <out.html>
"""
import glob
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

BANDS = {"healthy", "warning", "critical", "unknown"}
VISUALS = {"histogram", "line", "scatter", "stacked-bar", "table", "checklist"}
BAND_RANK = {"unknown": 0, "healthy": 1, "warning": 2, "critical": 3}


def validate(path):
    errs = []
    try:
        with open(path) as f:
            e = json.load(f)
    except (json.JSONDecodeError, OSError) as ex:
        return [f"not valid JSON: {ex}"]
    for k in ("schema", "pointer_id", "name", "category", "source", "window",
              "confidence", "summary", "detail"):
        if k not in e:
            errs.append(f"missing top-level key '{k}'")
    s = e.get("summary", {})
    for k in ("value", "unit", "band", "series", "evidence"):
        if k not in s:
            errs.append(f"missing summary key '{k}'")
    if s.get("band") not in BANDS:
        errs.append(f"summary.band '{s.get('band')}' not in {sorted(BANDS)}")
    d = e.get("detail", {})
    if "narrative" not in d or "visuals" not in d:
        errs.append("detail must contain 'narrative' and 'visuals'")
    for v in d.get("visuals", []):
        if v.get("type") not in VISUALS:
            errs.append(f"visual type '{v.get('type')}' not in vocabulary {sorted(VISUALS)}")
        if "title" not in v:
            errs.append("every visual needs a 'title'")
    return errs


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def meta(repo):
    remote = ""
    try:
        remote = git(repo, "config", "--get", "remote.origin.url")
    except subprocess.CalledProcessError:
        pass
    m = re.search(r"(?:github|gitlab|bitbucket)[^/:]*[:/]([^/]+)/([^/]+?)(?:\.git)?/?$", remote)
    if m:
        name, slug = f"{m.group(1)}/{m.group(2)}", f"{m.group(1)}-{m.group(2)}"
    else:
        base = os.path.basename(os.path.abspath(repo))
        name, slug = base, base
    slug = re.sub(r"[^A-Za-z0-9._-]", "-", slug).lower()
    authors = git(repo, "log", "--format=%aN")
    dates = git(repo, "log", "--format=%as").splitlines()
    first, last = (dates[-1], dates[0]) if dates else ("", "")
    age = ""
    if first:
        days = (datetime.now(timezone.utc) - datetime.fromisoformat(first + "T00:00:00+00:00")).days
        age = round(days / 365.25, 1)
    print(json.dumps({
        "name": name, "slug": slug, "remote": remote,
        "branch": git(repo, "rev-parse", "--abbrev-ref", "HEAD"),
        "commits": int(git(repo, "rev-list", "--count", "HEAD") or 0),
        "contributors": len(set(authors.splitlines())),
        "first_commit": first, "last_commit": last, "age_years": age,
        "analyzed_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }))


def bundle(meta_path, out_path, envelope_paths):
    with open(meta_path) as f:
        project = json.load(f)
    pointers = []
    for p in envelope_paths:
        with open(p) as f:
            pointers.append(json.load(f))
    known = [p for p in pointers if p["summary"]["band"] != "unknown"]
    overall = max((p["summary"]["band"] for p in known), key=BAND_RANK.get, default="unknown")
    with open(out_path, "w") as f:
        json.dump({"project": project, "overall_band": overall, "pointers": pointers}, f, indent=1)
    print(out_path)


def summary(bundle_path):
    """Agent-facing projection: one line per pointer, then the artifact handle.

    Exists so the agent never loads a whole bundle — which carries every
    pointer's detail.visuals — just to report a few bands.
    """
    with open(bundle_path) as f:
        b = json.load(f)
    rows = []
    for p in b.get("pointers", []):
        s = p.get("summary", {})
        val = "—" if s.get("value") is None else f"{s['value']} {s.get('unit', '')}".strip()
        rows.append((p.get("pointer_id", "?"), s.get("band", "unknown"), val,
                     (s.get("evidence") or "—").splitlines()[0][:60]))
    rows.sort(key=lambda r: -BAND_RANK.get(r[1], 0))
    w = [max((len(r[i]) for r in rows), default=1) for i in range(3)]
    proj = b.get("project", {})
    print(f"{proj.get('name', '?')}\toverall={b.get('overall_band', 'unknown')}\t"
          f"{proj.get('commits', '?')} commits\t{proj.get('contributors', '?')} contributors")
    for pid, band, val, ev in rows:
        print(f"{pid:<{w[0]}}  {band:<{w[1]}}  {val:<{w[2]}}  {ev}")
    print(f"<artifact>: {os.path.abspath(bundle_path)}")


def stamp(template_path, data_dir, out_path):
    with open(template_path) as f:
        tpl = f.read()
    projects = []
    for p in sorted(glob.glob(os.path.join(data_dir, "*.json"))):
        with open(p) as f:
            projects.append(json.load(f))
    projects.sort(key=lambda b: b["project"]["name"].lower())
    blob = json.dumps(projects).replace("</", "<\\/")
    if "__RR_DATA_JSON__" not in tpl:
        sys.exit("template is missing the __RR_DATA_JSON__ placeholder")
    with open(out_path, "w") as f:
        f.write(tpl.replace("__RR_DATA_JSON__", blob))
    print(f"{out_path} ({len(projects)} project(s))")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "validate":
        errors = validate(sys.argv[2])
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        sys.exit(1 if errors else 0)
    elif cmd == "meta":
        meta(sys.argv[2])
    elif cmd == "bundle":
        bundle(sys.argv[2], sys.argv[3], sys.argv[4:])
    elif cmd == "summary":
        summary(sys.argv[2])
    elif cmd == "stamp":
        stamp(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        sys.exit(__doc__)
