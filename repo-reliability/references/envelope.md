# The pointer envelope contract (schema 1)

Every pointer's `run.sh` prints exactly one JSON object to stdout. The report
template consumes only this shape — it never knows what any individual metric
means. `scripts/rr_build.py validate <file>` enforces it.

```json
{
  "schema": 1,
  "pointer_id": "kebab-case-id",
  "name": "Human name",
  "category": "commits | contributors | pull-requests | issues | releases | hygiene",
  "source": "git | forge | content",
  "window": { "from": "YYYY-MM-DD", "to": "YYYY-MM-DD" },
  "confidence": "high | medium | low",
  "summary": {
    "value": 18.2,
    "unit": "% merged PRs > 1000 LOC",
    "band": "healthy | warning | critical | unknown",
    "series": [ { "label": "2026-01", "value": 12 } ],
    "evidence": "One concrete example backing the number (PR #, commit hash, file)"
  },
  "detail": {
    "narrative": "2-3 sentences interpreting the metric for this repo.",
    "visuals": [ ]
  }
}
```

- `summary` renders the card face: value + unit headline, band badge, `series`
  as the mini bar strip (≤24 points), `evidence` as the footer line.
- `detail` renders the click-through panel: narrative paragraph, then visuals
  stacked in order.
- `value: null` with `band: "unknown"` means "could not compute" (use
  `rr_common.emit_unavailable`). Never invent a band from thin data — emit
  `unknown` and a low `confidence` instead.

## Visual vocabulary (closed set — never extend without changing the template)

| type | required fields |
|---|---|
| `histogram` | `data: [{label, value}]` |
| `line` | `series: [{name, points: [{label, value}]}]` — labels sort lexically (use `YYYY-MM`) |
| `scatter` | `data: [{x, y, label?}]`, `axes: {x, y}` (≤300 points) |
| `stacked-bar` | `labels: [..]`, `series: [{name, values: [..]}]` (values align with labels) |
| `table` | `columns: [..]`, `rows: [[..]]` (≤10 rows) |
| `checklist` | `items: [{label, ok, note?}]` |

Every visual also carries a `title` string.

## Bands and thresholds

Thresholds live in `pointer.json`, never in code:

```json
"thresholds": { "metric": "giant_commit_pct", "direction": "higher_is_worse",
                "warning": 5, "critical": 15 }
```

`rr_common.band_for(value)` applies them (`direction` may be
`lower_is_worse`, e.g. bus factor). Tuning a band is an edit to
`pointer.json` only.

## Environment a pointer runs in

| var | meaning |
|---|---|
| `REPO_DIR` | absolute path of the repo to analyze (defaults to cwd standalone) |
| `POINTER_DIR` | the pointer's own folder (set by its `run.sh`) |
| `RR_WINDOW_MONTHS` / `RR_WINDOW_FROM` / `RR_WINDOW_TO` | analysis window |
| `RR_FORGE_CACHE` | dir containing `prs.json`, `issues_open.json`, `issues_closed.json` — unset when forge data is unavailable |
| `RR_LIB` | path to `scripts/` (rr_common.py); run.sh falls back to `../../scripts` |

## Project bundle (what the runner stores per project)

`<data_home>/data/<slug>.json`:

```json
{ "project": { "name", "slug", "remote", "branch", "commits", "contributors",
               "first_commit", "last_commit", "age_years", "analyzed_at" },
  "overall_band": "worst non-unknown band across pointers",
  "pointers": [ envelope, envelope, ... ] }
```

The template receives a JSON array of these bundles inlined at the
`__RR_DATA_JSON__` placeholder.
