"""Giant-PR share and the rubber-stamp cluster: PR size against review activity."""
import rr_common as rr

GIANT = 1000

prs = rr.forge_cache("prs.json")
if prs is None:
    rr.emit_unavailable("Forge data unavailable (no GitHub remote, or gh CLI not authenticated).")
    raise SystemExit(0)

merged = [p for p in prs if p.get("mergedAt")]
if not merged:
    rr.emit_unavailable("No merged PRs found in the fetched window.")
    raise SystemExit(0)

for p in merged:
    p["size"] = (p.get("additions") or 0) + (p.get("deletions") or 0)
    p["reviewActivity"] = len(p.get("reviews") or []) + len(p.get("comments") or [])
    created, done = rr.parse_iso(p["createdAt"]), rr.parse_iso(p["mergedAt"])
    p["mergeMins"] = round((done - created).total_seconds() / 60)

giant = [p for p in merged if p["size"] > GIANT]
giant_pct = round(100 * len(giant) / len(merged), 1)
zero_review = [p for p in merged if p["reviewActivity"] == 0]
zero_pct = round(100 * len(zero_review) / len(merged), 1)
rubber = [p for p in giant if p["reviewActivity"] == 0]

BUCKETS = [(0, 100, "<100"), (100, 500, "100-500"), (500, 1000, "500-1k"),
           (1000, 2000, "1k-2k"), (2000, float("inf"), ">2k")]
hist = [{"label": lbl, "value": sum(1 for p in merged if lo <= p["size"] < hi)}
        for lo, hi, lbl in BUCKETS]

scatter = [{"x": p["size"], "y": p["reviewActivity"], "label": f"#{p['number']}"}
           for p in sorted(merged, key=lambda p: -p["size"])[:300]]
top = sorted(merged, key=lambda p: -p["size"])[:10]

if rubber:
    b = max(rubber, key=lambda p: p["size"])
    evidence = f"PR #{b['number']}: {b['size']:,} LOC, merged in {b['mergeMins']} min, 0 review activity"
else:
    b = top[0]
    evidence = f"Largest PR #{b['number']}: {b['size']:,} LOC, {b['reviewActivity']} review interactions"

rr.emit(
    {
        "value": giant_pct,
        "unit": f"% merged PRs > {GIANT} LOC",
        "band": rr.band_for(giant_pct),
        "series": hist,
        "evidence": evidence,
    },
    {
        "narrative": (
            f"{len(merged)} merged PRs analyzed. {giant_pct}% exceed {GIANT} LOC; {zero_pct}% merged with "
            f"zero review activity; {len(rubber)} PRs are both giant and unreviewed — the rubber-stamp "
            "cluster where AI-generated volume outruns human review capacity. In the scatter, healthy repos "
            "show review activity rising with size; a flat bottom edge at y=0 is the failure mode."
        ),
        "visuals": [
            {"type": "scatter", "title": "PR size vs review activity",
             "axes": {"x": "PR size (LOC)", "y": "reviews + comments"}, "data": scatter},
            {"type": "histogram", "title": "Merged PR size distribution", "data": hist},
            {"type": "table", "title": "10 largest merged PRs",
             "columns": ["PR", "LOC", "review activity", "mins to merge", "title"],
             "rows": [[f"#{p['number']}", p["size"], p["reviewActivity"], p["mergeMins"],
                       (p.get("title") or "")[:60]] for p in top]},
        ],
    },
    conf=rr.confidence(len(merged), 100, 30),
)
