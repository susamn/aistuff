---
name: repo-reliability
description: Analyze a git repository's development-process health and fragility — commit patterns, code churn, contributor concentration, PR flow vs review depth, issue responsiveness — via extensible per-pointer scripts that emit JSON envelopes, aggregated into a persistent multi-project dashboard on mosaic. Use when asked to assess a repo's reliability, maturity, commit/PR patterns, or how fragile a project is.
version: 3.0.0
kind: pipeline
triggers:
  - "analyze this repo"
  - "repo reliability report"
  - "how reliable/fragile is this project"
  - "analyze commit patterns"
  - "run repo reliability on <repo>"
intent: analysis
config_dir: ~/.config/skill-config/repo-reliability
created_at: 2026-07-28
updated_at: 2026-07-30
guardrails:
  - Read-only against the analyzed repository — never modify, commit, or push to it
  - Forge (GitHub) pointers need an authenticated gh CLI; when unavailable, skip them gracefully and still deliver the git-only report — never block on forge access
  - Metrics measure process health, a proxy for reliability — present bands with their evidence, never as verdicts on code quality
resources:
  - <SKILL_PATH>/scripts/run-report.sh
  - <SKILL_PATH>/scripts/rr_build.py
  - <SKILL_PATH>/scripts/rr_common.py
  - <SKILL_PATH>/webapp/app.json
  - <SKILL_PATH>/references/envelope.md
tools:
  - bash
  - git
  - gh
  - jq
  - python3
---

# Repo reliability

Runs every pointer under `pointers/` against a repo. Each pointer is a
self-contained folder (`pointer.json` definition + `run.sh` script) that emits
one JSON envelope (schema: `references/envelope.md`). The runner stores one
bundle per project in mosaic's centralized data home and refreshes a
manifest; `webapp/` is a mosaic dashboard tile (data-app-backed skill, see
`skill-creator/references/data-app-skills.md`) rendering **all** analyzed
projects: a project list, per-project card dashboard, and click-through
detail visuals per card.

## Configuration

`~/.config/skill-config/repo-reliability/skill.properties` — created with
defaults on first run; report loaded values to the user:

- `data_home` (default `~/.local/share/repo-reliability`) — clones of
  URL-analyzed repos, in `clones/`. Project bundles and the manifest the
  webapp reads live in mosaic's own data home instead
  (`~/.local/share/mosaic/data/repo-reliability/`), not here.
- `window_months` (default 12) — analysis window for time-boxed pointers
- `forge_pr_limit` / `forge_issue_limit` (default 300) — API fetch caps
- `mosaic_onboarded` — internal flag set once the webapp has been symlinked
  into mosaic's staging dirs; not user-tunable

Do not add new properties without explicit user approval.

## Workflow

1. Identify the target: a local path or a repo URL (URL → the runner clones
   into `<data_home>/clones/`). Rerunning on the same remote replaces that
   project's stored JSON — project identity is keyed on the remote URL.
2. Run: `<SKILL_PATH>/scripts/run-report.sh --repo <path-or-url>`
   Useful flags: `--months N`, `--no-forge`, `--render-only` (rebuild
   `manifest.json` from stored data without analyzing), `--open`.
3. The runner onboards itself into mosaic on first run (idempotent after)
   and prints the project's data file plus the dashboard URL
   (`http://localhost:<mosaic-port>/mosaic/apps/repo-reliability/`, default
   port 47500). Relay both to the user.
4. Deliver: tell the user to start mosaic if it isn't already running
   (`$TOOLS_PATH/mosaic/quick-start.sh start`) then open the dashboard URL.
   `--open` does this automatically via `xdg-open`. There is no standalone
   report file to hand over — mosaic is the only rendering surface.
5. Read the digest — **never open the bundle to summarize it**:

   ```bash
   python3 <SKILL_PATH>/scripts/rr_build.py summary <data-file>
   ```

   Relay those lines: overall band, worst pointers first with their evidence, and
   any skipped (e.g. no forge access). Never present a band without its evidence.

## Output

`summary` emits a project header, one line per pointer sorted worst-first, and
the artifact path as the last line:

```
demo	overall=critical	412 commits	3 contributors
contributor-concentration  critical  1 bus factor      a4f21c9
commit-size-discipline     warning   18.2 % >1000 LOC  PR #412
<artifact>: /home/user/.local/share/mosaic/data/repo-reliability/demo.json
```

The bundle carries every pointer's `detail.visuals` — scatter sets up to 300
points each. Open it only to investigate a specific line that looks wrong; the
handle on the last line is how you get there.

## Steady state, once onboarded to mosaic

`mosaic_onboarded=true` is already set
(`~/.config/skill-config/repo-reliability/skill.properties`). Routine
invocations of `run-report.sh` from here on are data-producing runs only:
they write project bundles to
`~/.local/share/mosaic/data/repo-reliability/`, and mosaic serves it
automatically — no separate publish step. Modifying `webapp/app.json`,
`webapp/static/`, the onboarding symlink, or the pointer/runner scripts'
own logic (including adding a new pointer, below) is a distinct action,
done only when the user explicitly asks for it — never as a side effect of
analyzing a repo.

## Adding a new pointer

Ongoing process — pointers are meant to accumulate. The contract:

1. `cp -r <SKILL_PATH>/pointers/_template <SKILL_PATH>/pointers/<new-id>`
   (folders starting with `_` are skipped by the runner).
2. Fill `pointer.json`: id (= folder name), name, category, `source`
   (`git`|`forge`|`content`), `requires` (`forge-cache` makes the runner skip
   it when no forge data exists), `order`, and `thresholds` with `direction`.
3. Implement the script. `run.sh` is the entrypoint contract (any language
   behind it); the scaffold wires `pointer.py` to the shared helpers in
   `scripts/rr_common.py` (`iter_commits`, `forge_cache`, `band_for`, `emit`,
   `emit_unavailable`). Read `references/envelope.md` before writing.
4. Hard rule: detail visuals only from the closed vocabulary — `histogram`,
   `line`, `scatter`, `stacked-bar`, `table`, `checklist`. A pointer needing a
   new chart type is a `webapp/static/js/app.js` change first, discussed with
   the user.
5. Verify: `<SKILL_PATH>/scripts/run-report.sh --validate <SKILL_PATH>/pointers/<new-id> --repo <some-repo>`
   then a full run to confirm the card renders and expands.
6. Reference implementations: `commit-size-discipline` (git source),
   `pr-size-review-depth` (forge source).

## Notes

- Thresholds are opinionated defaults; tune them in `pointer.json` per user
  feedback, never inline in scripts.
- The forge cache is fetched once per run and shared by all forge pointers;
  new forge pointers should read `RR_FORGE_CACHE` files, not call `gh`
  themselves. If a new pointer needs data not in the cache, extend the fetch
  in `run-report.sh` (one place).
- Replacing a project's JSON discards its previous run (no history) — a known
  tradeoff; if the user wants trend-over-runs, that is a storage-layout change.
