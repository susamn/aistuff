"""Bus factor and ownership spread, computed over full history (line contribution)."""
from collections import defaultdict
from datetime import datetime, timezone
import rr_common as rr

author_adds = defaultdict(int)
author_commits = defaultdict(int)
quarter_author = defaultdict(lambda: defaultdict(int))
dir_author = defaultdict(lambda: defaultdict(int))
n_commits = 0

for c in rr.iter_commits():
    n_commits += 1
    a = c["author"]
    author_commits[a] += 1
    dt = datetime.fromtimestamp(c["ts"], timezone.utc)
    quarter_author[f"{dt.year}-Q{(dt.month - 1) // 3 + 1}"][a] += 1
    for path, adds, _ in c["files"]:
        author_adds[a] += adds
        top_dir = path.split("/")[0] if "/" in path else "(root)"
        dir_author[top_dir][a] += adds

if not n_commits:
    rr.emit_unavailable("Repository has no commits.")
    raise SystemExit(0)

total = sum(author_adds.values()) or 1
ranked = sorted(author_adds.items(), key=lambda kv: -kv[1])
cum, bus = 0, 0
for _, adds in ranked:
    cum += adds
    bus += 1
    if cum >= total * 0.5:
        break
top_share = round(100 * ranked[0][1] / total, 1)
bus_share = round(100 * cum / total, 1)

share_series = [{"label": a, "value": round(100 * v / total, 1)} for a, v in ranked[:5]]

quarters = sorted(quarter_author)[-8:]
top_authors = [a for a, _ in ranked[:6]]
stacked = {
    "labels": quarters,
    "series": [{"name": a, "values": [quarter_author[q].get(a, 0) for q in quarters]}
               for a in top_authors]
    + [{"name": "others",
        "values": [sum(v for a2, v in quarter_author[q].items() if a2 not in top_authors)
                   for q in quarters]}],
}

solo = []
for d, owners in dir_author.items():
    d_total = sum(owners.values())
    if d_total < total * 0.01:
        continue
    owner, owned = max(owners.items(), key=lambda kv: kv[1])
    pct = round(100 * owned / d_total, 1)
    if pct >= 80:
        solo.append([d, owner, pct, d_total])
solo.sort(key=lambda r: -r[3])

rr.emit(
    {
        "value": bus,
        "unit": f"bus factor ({bus} own {bus_share}%)",
        "band": rr.band_for(bus),
        "series": share_series,
        "evidence": f"Top author: {ranked[0][0]} — {top_share}% of all contributed lines",
    },
    {
        "narrative": (
            f"{len(author_adds)} contributors over {n_commits} commits. The smallest set of authors "
            f"owning at least half the contributed lines has {bus} member(s) ({bus_share}%). "
            f"{len(solo)} significant top-level directories are effectively single-owner (≥80% one author). "
            "Concentration is normal early on; the risk is concentration that never dilutes as the repo grows."
        ),
        "visuals": [
            {"type": "stacked-bar", "title": "Commits per quarter by author", **stacked},
            {"type": "histogram", "title": "Line-contribution share, top 5 (%)", "data": share_series},
            {"type": "table", "title": "Single-owner directories (≥80% one author)",
             "columns": ["directory", "owner", "ownership %", "lines"],
             "rows": solo[:10]},
        ],
    },
    conf=rr.confidence(n_commits, 300, 60),
)
