"""Shared helpers for repo-reliability pointer scripts.

Every pointer script imports this module, computes its metric, and calls
emit() with a summary block and a detail block. The envelope contract is
documented in references/envelope.md.
"""
import json
import math
import os
import subprocess
from datetime import date, datetime, timedelta, timezone

BANDS = ("healthy", "warning", "critical", "unknown")
VISUAL_TYPES = ("histogram", "line", "scatter", "stacked-bar", "table", "checklist")


def env(name, default=None):
    return os.environ.get(name, default)


def repo_dir():
    return env("REPO_DIR", os.getcwd())


def load_pointer_def():
    with open(os.path.join(os.environ["POINTER_DIR"], "pointer.json")) as f:
        return json.load(f)


def thresholds():
    return load_pointer_def().get("thresholds", {})


def band_for(value, th=None):
    """Map a value to a band using the pointer.json thresholds block."""
    th = th or thresholds()
    if value is None or "warning" not in th:
        return "unknown"
    if th.get("direction", "higher_is_worse") == "higher_is_worse":
        if value >= th["critical"]:
            return "critical"
        if value >= th["warning"]:
            return "warning"
    else:
        if value <= th["critical"]:
            return "critical"
        if value <= th["warning"]:
            return "warning"
    return "healthy"


def window():
    frm = env("RR_WINDOW_FROM")
    to = env("RR_WINDOW_TO") or date.today().isoformat()
    if not frm:
        months = int(env("RR_WINDOW_MONTHS", "12"))
        frm = (date.today() - timedelta(days=months * 30)).isoformat()
    return frm, to


def iter_commits(since=None, until=None):
    """Yield {hash, ts, author, subject, files:[(path, adds, dels)]} oldest-last.

    Merge commits are excluded so sizes reflect authored change, not integration.
    """
    fmt = "@@%H|%at|%aN|%s"
    args = ["git", "-C", repo_dir(), "log", "--numstat", "--no-merges", f"--format={fmt}"]
    if since:
        args.append(f"--since={since}")
    if until:
        args.append(f"--until={until}")
    out = subprocess.run(args, capture_output=True, text=True, check=True).stdout
    commit = None
    for line in out.splitlines():
        if line.startswith("@@"):
            if commit:
                yield commit
            h, ts, an, s = line[2:].split("|", 3)
            commit = {"hash": h, "ts": int(ts), "author": an, "subject": s, "files": []}
        elif line.strip() and commit is not None:
            parts = line.split("\t")
            if len(parts) == 3:
                a, d, p = parts
                commit["files"].append(
                    (p, int(a) if a.isdigit() else 0, int(d) if d.isdigit() else 0)
                )
    if commit:
        yield commit


def month_of(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m")


def parse_iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def percentile(vals, p):
    vals = sorted(vals)
    if not vals:
        return 0
    k = (len(vals) - 1) * p
    f, c = math.floor(k), math.ceil(k)
    if f == c:
        return vals[int(k)]
    return vals[f] + (vals[c] - vals[f]) * (k - f)


def confidence(n, high, medium):
    return "high" if n >= high else ("medium" if n >= medium else "low")


def forge_cache(name):
    d = env("RR_FORGE_CACHE")
    if not d:
        return None
    p = os.path.join(d, name)
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


def emit(summary, detail, conf="high"):
    pd = load_pointer_def()
    frm, to = window()
    for v in detail.get("visuals", []):
        if v.get("type") not in VISUAL_TYPES:
            raise ValueError(f"visual type '{v.get('type')}' not in vocabulary {VISUAL_TYPES}")
    if summary.get("band") not in BANDS:
        raise ValueError(f"band '{summary.get('band')}' not in {BANDS}")
    print(json.dumps({
        "schema": 1,
        "pointer_id": pd["id"],
        "name": pd["name"],
        "category": pd["category"],
        "source": pd["source"],
        "window": {"from": frm, "to": to},
        "confidence": conf,
        "summary": summary,
        "detail": detail,
    }))


def emit_unavailable(reason):
    """Standard output when a pointer's data source is not reachable."""
    emit(
        {"value": None, "unit": "", "band": "unknown", "series": [], "evidence": reason},
        {"narrative": reason, "visuals": []},
        conf="low",
    )
