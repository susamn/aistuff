"""Early-churn rate: share of added lines whose file is reworked within 30 days.

File-level approximation: a commit's added lines count as "churned" when the
same file is modified again within CHURN_DAYS. Line-level tracking would be
exact but is orders of magnitude slower; at repo scale the approximation ranks
identically.
"""
import time
from collections import defaultdict
import rr_common as rr

CHURN_DAYS = 30
SECS = CHURN_DAYS * 86400
NOISE = {".lock", ".min.js", ".map", ".svg", ".json"}

frm, to = rr.window()
touches = defaultdict(list)
n_commits = 0
for c in rr.iter_commits(since=frm, until=to):
    n_commits += 1
    for path, adds, dels in c["files"]:
        if any(path.endswith(s) for s in NOISE):
            continue
        touches[path].append((c["ts"], adds, dels))

if not n_commits:
    rr.emit_unavailable("No commits found in the analysis window.")
    raise SystemExit(0)

now = time.time()
total_adds = churned_adds = 0
monthly_total = defaultdict(int)
monthly_churned = defaultdict(int)
hotspots = defaultdict(lambda: [0, 0])

for path, lst in touches.items():
    lst.sort()
    for i, (ts, adds, _) in enumerate(lst):
        if adds == 0 or ts > now - SECS:
            continue
        total_adds += adds
        m = rr.month_of(ts)
        monthly_total[m] += adds
        if any(t2 - ts <= SECS for t2, _, _ in lst[i + 1:]):
            churned_adds += adds
            monthly_churned[m] += adds
            hotspots[path][0] += adds
            hotspots[path][1] += 1

if total_adds == 0:
    rr.emit_unavailable(f"Not enough history: no additions older than {CHURN_DAYS} days in the window.")
    raise SystemExit(0)

churn_pct = round(100 * churned_adds / total_adds, 1)
months = sorted(monthly_total)
churn_line = [{"label": m,
               "value": round(100 * monthly_churned[m] / monthly_total[m], 1) if monthly_total[m] else 0}
              for m in months]
top = sorted(hotspots.items(), key=lambda kv: -kv[1][0])[:10]
evidence = (f"{top[0][0]}: {top[0][1][0]:,} lines reworked within {CHURN_DAYS}d"
            if top else "No churn hotspots detected.")

rr.emit(
    {
        "value": churn_pct,
        "unit": f"% lines reworked within {CHURN_DAYS}d",
        "band": rr.band_for(churn_pct),
        "series": churn_line[-12:],
        "evidence": evidence,
    },
    {
        "narrative": (
            f"Of {total_adds:,} lines added in the window (excluding the last {CHURN_DAYS} days), "
            f"{churn_pct}% belong to files reworked within {CHURN_DAYS} days of the addition. "
            "High early churn means code is not surviving contact with reality — the signature of "
            "generated code landing faster than it is understood. File-level approximation; "
            "lockfiles and generated assets are excluded."
        ),
        "visuals": [
            {"type": "line", "title": f"Monthly {CHURN_DAYS}-day churn rate (%)",
             "series": [{"name": "churn %", "points": churn_line}]},
            {"type": "table", "title": "Churn hotspot files",
             "columns": ["file", "lines churned", "rework events"],
             "rows": [[p, v[0], v[1]] for p, v in top]},
        ],
    },
    conf=rr.confidence(n_commits, 200, 50),
)
