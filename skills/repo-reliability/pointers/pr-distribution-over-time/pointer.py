"""Monthly PR flow: count and size-class mix over time; flags velocity discontinuities."""
from collections import defaultdict
from statistics import median
import rr_common as rr

CLASSES = [(0, 100, "small"), (100, 500, "medium"), (500, 1000, "large"),
           (1000, float("inf"), "giant")]

prs = rr.forge_cache("prs.json")
if prs is None:
    rr.emit_unavailable("Forge data unavailable (no GitHub remote, or gh CLI not authenticated).")
    raise SystemExit(0)

opened = defaultdict(int)
merged_by_month = defaultdict(lambda: defaultdict(int))
for p in prs:
    opened[p["createdAt"][:7]] += 1
    if p.get("mergedAt"):
        size = (p.get("additions") or 0) + (p.get("deletions") or 0)
        cls = next(lbl for lo, hi, lbl in CLASSES if lo <= size < hi)
        merged_by_month[p["mergedAt"][:7]][cls] += 1

months = sorted(set(opened) | set(merged_by_month))
if len(months) < 3:
    rr.emit_unavailable("Fewer than 3 months of PR history in the fetched window.")
    raise SystemExit(0)

merged_counts = {m: sum(merged_by_month[m].values()) for m in months}
recent = months[-3:]
baseline = months[:-3]
recent_avg = sum(merged_counts[m] for m in recent) / 3

value = round(recent_avg, 1)
if len(baseline) >= 6:
    base_med = median(merged_counts[m] for m in baseline) or 0.5
    ratio = round(recent_avg / base_med, 2)
    band = rr.band_for(ratio)
    giant_recent = sum(merged_by_month[m].get("giant", 0) for m in recent)
    giant_base = sum(merged_by_month[m].get("giant", 0) for m in baseline)
    share_recent = giant_recent / max(1, sum(merged_counts[m] for m in recent))
    share_base = giant_base / max(1, sum(merged_counts[m] for m in baseline))
    if band == "warning" and share_base and share_recent > 2 * share_base and share_recent > 0.1:
        band = "critical"
    trend = f"{ratio}x the trailing monthly median ({base_med:g})"
else:
    ratio, band, trend = None, "unknown", "insufficient baseline (<6 months) for trend judgment"

stacked = {
    "labels": months,
    "series": [{"name": lbl, "values": [merged_by_month[m].get(lbl, 0) for m in months]}
               for _, _, lbl in CLASSES],
}
flow = [{"name": "opened", "points": [{"label": m, "value": opened.get(m, 0)} for m in months]},
        {"name": "merged", "points": [{"label": m, "value": merged_counts[m]} for m in months]}]

anomalies = sorted(
    ([m, merged_counts[m], merged_by_month[m].get("giant", 0),
      round(100 * merged_by_month[m].get("giant", 0) / merged_counts[m], 1) if merged_counts[m] else 0]
     for m in months),
    key=lambda r: (-r[1], -r[2]))[:6]

rr.emit(
    {
        "value": value,
        "unit": "merged PRs/month (3-mo avg)",
        "band": band,
        "series": [{"label": m, "value": merged_counts[m]} for m in months[-12:]],
        "evidence": f"Recent merge velocity is {trend}",
    },
    {
        "narrative": (
            f"{len(prs)} PRs across {len(months)} months. Steady growth in volume is healthy; a "
            "discontinuity — recent velocity several times the historical median, especially with a "
            "rising giant-size share — marks the point where generation speed decoupled from review "
            "capacity. Watch the giant segment of the stacked bars grow month over month."
        ),
        "visuals": [
            {"type": "stacked-bar", "title": "Merged PRs per month by size class", **stacked},
            {"type": "line", "title": "PRs opened vs merged per month", "series": flow},
            {"type": "table", "title": "Busiest months",
             "columns": ["month", "merged", "giant PRs", "giant share %"], "rows": anomalies},
        ],
    },
    conf=rr.confidence(len(prs), 100, 30),
)
