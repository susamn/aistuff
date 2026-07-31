"""LOC-per-commit distribution: giant-commit share, revert rate, size over time."""
from collections import defaultdict
import rr_common as rr

GIANT = 1000
BUCKETS = [(0, 50, "<50"), (50, 200, "50-200"), (200, 1000, "200-1k"),
           (1000, 5000, "1k-5k"), (5000, float("inf"), ">5k")]

frm, to = rr.window()
commits = []
for c in rr.iter_commits(since=frm, until=to):
    size = sum(a + d for _, a, d in c["files"])
    commits.append({**c, "size": size})

if not commits:
    rr.emit_unavailable("No commits found in the analysis window.")
    raise SystemExit(0)

sizes = [c["size"] for c in commits]
giant = [c for c in commits if c["size"] > GIANT]
giant_pct = round(100 * len(giant) / len(commits), 1)
reverts = [c for c in commits if c["subject"].lower().startswith("revert")]
revert_pct = round(100 * len(reverts) / len(commits), 1)

hist = [{"label": lbl, "value": sum(1 for s in sizes if lo <= s < hi)}
        for lo, hi, lbl in BUCKETS]

monthly = defaultdict(list)
for c in commits:
    monthly[rr.month_of(c["ts"])].append(c["size"])
months = sorted(monthly)
median_line = [{"label": m, "value": round(rr.percentile(monthly[m], 0.5))} for m in months]
p90_line = [{"label": m, "value": round(rr.percentile(monthly[m], 0.9))} for m in months]

top = sorted(commits, key=lambda c: -c["size"])[:10]
biggest = top[0]
evidence = f"{biggest['hash'][:8]}: {biggest['size']:,} LOC — \"{biggest['subject'][:60]}\""

rr.emit(
    {
        "value": giant_pct,
        "unit": f"% commits > {GIANT} LOC",
        "band": rr.band_for(giant_pct),
        "series": hist,
        "evidence": evidence,
    },
    {
        "narrative": (
            f"{len(commits)} non-merge commits in the window. Median {round(rr.percentile(sizes, 0.5))} LOC, "
            f"p90 {round(rr.percentile(sizes, 0.9))} LOC. {giant_pct}% exceed {GIANT} LOC "
            f"(unreviewable-chunk territory); revert rate {revert_pct}%. "
            "A rising median or fattening tail over time marks code landing faster than it can be understood."
        ),
        "visuals": [
            {"type": "line", "title": "Commit size over time (LOC)",
             "series": [{"name": "median", "points": median_line},
                        {"name": "p90", "points": p90_line}]},
            {"type": "histogram", "title": "Commit size distribution", "data": hist},
            {"type": "table", "title": "10 largest commits",
             "columns": ["commit", "LOC", "files", "subject"],
             "rows": [[c["hash"][:8], c["size"], len(c["files"]), c["subject"][:70]] for c in top]},
        ],
    },
    conf=rr.confidence(len(commits), 200, 50),
)
