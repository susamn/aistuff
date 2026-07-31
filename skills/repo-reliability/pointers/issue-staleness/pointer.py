"""Untaken issues: staleness of the open backlog and opened-vs-closed trajectory."""
from collections import defaultdict
from datetime import datetime, timezone
import rr_common as rr

STALE_DAYS = 90

open_issues = rr.forge_cache("issues_open.json")
closed_issues = rr.forge_cache("issues_closed.json") or []
if open_issues is None:
    rr.emit_unavailable("Forge data unavailable (no GitHub remote, or gh CLI not authenticated).")
    raise SystemExit(0)
if not open_issues and not closed_issues:
    rr.emit_unavailable("No issues found (issues may be disabled for this repo).")
    raise SystemExit(0)

now = datetime.now(timezone.utc)
for i in open_issues:
    i["ageDays"] = (now - rr.parse_iso(i["createdAt"])).days
    i["idleDays"] = (now - rr.parse_iso(i["updatedAt"])).days

stale = [i for i in open_issues if i["idleDays"] > STALE_DAYS]
stale_pct = round(100 * len(stale) / len(open_issues), 1) if open_issues else 0.0

BUCKETS = [(0, 30, "<30d"), (30, 90, "30-90d"), (90, 180, "90-180d"),
           (180, 365, "180d-1y"), (365, float("inf"), ">1y")]
hist = [{"label": lbl, "value": sum(1 for i in open_issues if lo <= i["ageDays"] < hi)}
        for lo, hi, lbl in BUCKETS]

opened = defaultdict(int)
closed = defaultdict(int)
for i in open_issues + closed_issues:
    opened[i["createdAt"][:7]] += 1
for i in closed_issues:
    if i.get("closedAt"):
        closed[i["closedAt"][:7]] += 1
months = sorted(set(opened) | set(closed))[-18:]
flow = [{"name": "opened", "points": [{"label": m, "value": opened.get(m, 0)} for m in months]},
        {"name": "closed", "points": [{"label": m, "value": closed.get(m, 0)} for m in months]}]

oldest = sorted(open_issues, key=lambda i: -i["idleDays"])[:10]
evidence = (f"#{oldest[0]['number']} untouched for {oldest[0]['idleDays']} days: "
            f"\"{(oldest[0].get('title') or '')[:50]}\"" if oldest else "Backlog is empty.")

band = rr.band_for(stale_pct) if open_issues else "healthy"
rr.emit(
    {
        "value": stale_pct,
        "unit": f"% open issues idle > {STALE_DAYS}d",
        "band": band,
        "series": hist,
        "evidence": evidence,
    },
    {
        "narrative": (
            f"{len(open_issues)} open issues; {len(stale)} ({stale_pct}%) have had no activity for over "
            f"{STALE_DAYS} days — the untaken backlog. Absolute counts mean little (popular repos carry "
            "large backlogs healthily); what matters is the idle share and whether the opened-vs-closed "
            "lines diverge. A widening gap means the project is drowning; closed tracking opened means "
            "someone is home."
        ),
        "visuals": [
            {"type": "line", "title": "Issues opened vs closed per month", "series": flow},
            {"type": "histogram", "title": "Open issue age distribution", "data": hist},
            {"type": "table", "title": "Most-stale open issues",
             "columns": ["issue", "idle days", "age days", "title"],
             "rows": [[f"#{i['number']}", i["idleDays"], i["ageDays"],
                       (i.get("title") or "")[:60]] for i in oldest]},
        ],
    },
    conf=rr.confidence(len(open_issues) + len(closed_issues), 100, 25),
)
