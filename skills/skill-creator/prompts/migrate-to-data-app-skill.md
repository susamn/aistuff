# Migrate an Existing Skill to a Data-App Skill — Prompts

For a skill that already runs scripts and produces output (a report file, a
CLI summary, anything) and should also get a live mosaic dashboard tile. The
generation logic never needs to change — only where its output lands and how
it's shown. This is real work, comparable in size to building the skill in
the first place; do it in a fresh session with full context budget, not
squeezed into the end of an unrelated one.

- "Migrate `<skill-name>` to a data-app skill onboarded to mosaic."
- "Give `<skill-name>` a mosaic dashboard alongside what it already produces."

## Reusable template

Fill in `<skill-name>` and the "What `<skill-name>` currently does" section,
then paste as the opening message of a fresh session:

```
Migrate the <skill-name> skill (~/dotfiles/aistuff/skills/<skill-name>/) into a
data-app skill onboarded to mosaic (~/dotfiles/workspace/tools/mosaic/),
following skill-creator's references/data-app-skills.md contract. Load the
skill-creator skill first and read that reference doc before starting.

## What <skill-name> currently does
- <generation logic: scripts, what they compute, current output location
  and shape>
- <current "rendering" if any — a report file, a CLI summary, nothing>
- <what must NOT change: the generation logic stays exactly as-is; only
  where output lands and how it's shown changes>
- <testing constraints — missing credentials/CLIs, hard-to-produce data,
  synthetic fixtures needed>

## What mosaic currently is
- Host at ~/dotfiles/workspace/tools/mosaic/ (own git repo, run
  ./quick-start.sh start to bring it up on :47500, dashboard at /mosaic/).
- Apps discovered from ~/.local/share/mosaic/apps/*/app.json — a skill
  symlinks its webapp/ there directly (mkdir -p + ln -sfn; see
  data-app-skills.md for the exact commands and the app.json shape).
- Data goes to ~/.local/share/mosaic/data/<id>/ — the skill's own generation
  script should write there directly (mkdir -p defensively).
- Mosaic has its own Playwright test suite (tests/) — follow the same
  pattern (fixture app copied to a temp dir, onboard -> assert -> unboard)
  if you add tests for the migrated skill.

## Open question — resolve with the user before deciding
Does <skill-name> already produce something worth keeping as a parallel
export option, or should it be fully retired in favor of the mosaic
dashboard? Don't assume — ask.

## Housekeeping
- Don't push or run gh pr create — SSH key is passphrase-protected and gh
  isn't installed; commit locally and hand off the push command.
- skills/ is a git submodule of dotfiles — commit changes there, but don't
  bump the dotfiles pointer unless explicitly asked.
- Add a "Steady state, once onboarded to mosaic" section to <skill-name>'s
  own SKILL.md (scaffold.sh writes this automatically for brand-new skills;
  a migration has to add it by hand — see data-app-skills.md's "Steady-state"
  section for the exact wording to adapt). This is what tells a future agent
  invoking <skill-name> that routine runs are data-producing only, and that
  touching webapp/ or the generation script's logic requires an explicit ask.
- Run skill-manager's audit.sh against <skill-name> before calling it done.
```

## Worked example: repo-reliability

Same template — only the "What it currently does" section and the open
question differ; the "What mosaic currently is" and "Housekeeping" sections
above are unchanged and not repeated here. This is a snapshot from
2026-07-30 — verify against the actual files before relying on it, since
repo-reliability's structure may have moved on since.

```
## What repo-reliability currently is
- Pointer/envelope architecture: pointers/<id>/{pointer.json,run.sh} emit a
  JSON envelope (schema in references/envelope.md) with summary (value, unit,
  band, series, evidence) and detail (narrative, visuals — closed vocabulary:
  histogram, line, scatter, stacked-bar, table, checklist).
- Runner: scripts/run-report.sh discovers pointers, runs them, calls
  scripts/rr_build.py (validate/meta/bundle/summary/stamp subcommands).
- Persistent store: ~/.local/share/repo-reliability/data/<project-slug>.json,
  bundle shape {project, overall_band, pointers: [envelope, ...]}.
- Rendering: template/report.html is a SELF-CONTAINED file — data gets
  inlined via a __RR_DATA_JSON__ placeholder (rr_build.py stamp), because it
  was built before mosaic existed and had no server to fetch from. It already
  contains a full generic rendering engine for the envelope schema: card grid
  (project list -> dashboard -> click-through detail), and JS functions for
  all six visual types. This is the thing to port/adapt into webapp/, not
  rewrite from scratch.
- Pointer generation scripts (rr_common.py, individual pointer.py files)
  should NOT change — only where output lands and how it's rendered changes.
- gh CLI is not installed on this machine, so forge-sourced pointers
  (pr-size-review-depth, pr-distribution-over-time, issue-staleness) can't be
  tested against live GitHub — use git-only pointers, or build a synthetic
  forge-cache fixture, for end-to-end verification.

## Open question — resolve with the user before deciding
Should the existing self-contained template/report.html (single-file,
inlined data, no server needed) be kept as a parallel export option, or
retired in favor of the mosaic dashboard? Don't assume — ask.
```
