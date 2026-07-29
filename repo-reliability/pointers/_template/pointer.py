"""TODO: one line on what this pointer measures and why it signals fragility.

Copy this folder to pointers/<your-id>/, fill in pointer.json, implement below.
Contract: emit exactly one envelope JSON on stdout (rr_common.emit does this).
Detail visuals may ONLY use: histogram, line, scatter, stacked-bar, table, checklist.
Data sources: rr.iter_commits() for git, rr.forge_cache("prs.json" |
"issues_open.json" | "issues_closed.json") for forge (returns None when absent —
then call rr.emit_unavailable and exit 0).
"""
import rr_common as rr

frm, to = rr.window()

value = None
if value is None:
    rr.emit_unavailable("TODO: pointer not implemented yet.")
    raise SystemExit(0)

rr.emit(
    {
        "value": value,
        "unit": "TODO unit shown next to the number",
        "band": rr.band_for(value),
        "series": [],
        "evidence": "TODO one concrete example backing the number",
    },
    {
        "narrative": "TODO two-three sentences interpreting the metric.",
        "visuals": [],
    },
    conf="low",
)
