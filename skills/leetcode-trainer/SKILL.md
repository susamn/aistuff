---
name: leetcode-trainer
description: Practice LeetCode problems in a 3-tab mosaic dashboard (Problem, Intuition, Solution — Python + Go). Starter-seeded with 100 classic problems; add, swap, or remove any problem by URL or description. Use when asked to practice LeetCode, add/swap a coding-interview problem, or open the LeetCode practice dashboard.
version: 1.0.0
kind: hybrid
triggers:
  - "practice leetcode"
  - "add this leetcode problem"
  - "swap out a leetcode problem"
  - "open the leetcode dashboard"
  - "leetcode top 100"
intent: execution
config_dir: ~/.config/skill-config/leetcode-trainer
created_at: 2026-08-08
updated_at: 2026-08-08
guardrails:
  - Never copy LeetCode's own problem statement/examples verbatim — paraphrase; keep source_url for the original
  - Both solutions.python and solutions.golang are required and must be correct for the exact approach described in intuition — trace them against the examples before storing
  - Routine adds/removes only ever write under problems/ and rebuild manifest.json — never touch webapp/ or the scripts' own logic as a side effect
resources:
  - <SKILL_PATH>/scripts/lc.sh
  - <SKILL_PATH>/scripts/lc_core.py
  - <SKILL_PATH>/references/schema.md
  - <SKILL_PATH>/references/add-workflow.md
  - <SKILL_PATH>/references/top-100.json
  - <SKILL_PATH>/webapp/app.json
tools:
  - bash
  - python3
---

# leetcode trainer

A mosaic dashboard for practicing LeetCode problems: a full-width list of
authored problems, each opening into a 3-tab detail view — **Problem**
(statement + examples), **Intuition** (plain-language approach + optional
diagram), **Solution** (Python and Go, toggleable). Content lives one JSON
file per problem under mosaic's data home; `scripts/lc.sh` is the only thing
that reads or writes it.

This skill has two kinds of work, kept separate:

- **Judgment (you, the agent)** — authoring a problem's statement paraphrase,
  intuition, and both solutions. Never scripted; see
  `references/add-workflow.md`.
- **Total (the script)** — schema validation, storage, manifest rebuilding,
  listing, and diffing against the starter checklist. Never done by hand;
  see `references/schema.md`.

## Adding, swapping, or removing a problem

This is the routine, ongoing use of this skill — read
`references/add-workflow.md` before doing this, every time. Short version:
author a record against `references/schema.md`, `lc.sh validate` it, then
`lc.sh add` it (adding an existing slug replaces it — that's a "swap").
`lc.sh remove <slug>` deletes one. `lc.sh progress` shows how much of the
starter 100-problem checklist (`references/top-100.json`) is authored yet.

```
<SKILL_PATH>/scripts/lc.sh add <staging-file.json>
<SKILL_PATH>/scripts/lc.sh remove <slug>
<SKILL_PATH>/scripts/lc.sh validate <staging-file.json>
<SKILL_PATH>/scripts/lc.sh list
<SKILL_PATH>/scripts/lc.sh progress
<SKILL_PATH>/scripts/lc.sh rebuild-manifest
```

`list` and `progress` are the summary projections — one line per problem
(or per gap), ending in the artifact path (`manifest.json` or
`top-100.json`). Don't open the individual problem JSON files to answer "how
many are done" — read the projection.

## First-time setup (already done once; see below)

`references/top-100.json` shipped with the skill lists the starter 100.
`webapp/` is onboarded into mosaic — two symlinks, not one:
`~/.local/share/mosaic/apps/leetcode-trainer -> <SKILL_PATH>/webapp` (mosaic
discovers the app) and `<SKILL_PATH>/webapp/data -> ~/.local/share/mosaic/data/leetcode-trainer`
(mosaic's `/data/{path}` route resolves under the app's *own* `webapp/data/`,
so without this second link the app is visible on the dashboard but every
data fetch 404s). `mosaic_onboarded=true` in this skill's config tracks that
both are done. Setting either of those up again is not a routine step —
if it ever needs redoing, `$TOOLS_PATH/mosaic/scripts/onboard.sh <SKILL_PATH>/webapp` does both.

## Delivering to the user

Tell them to start mosaic if it isn't running
(`$TOOLS_PATH/mosaic/quick-start.sh start`, or however they normally run it)
then open `http://localhost:<mosaic-port>/mosaic/apps/leetcode-trainer/`.
There's no report file — the dashboard is the only deliverable.

## Steady state, once onboarded to mosaic

Once `webapp/` is onboarded (symlinked into mosaic's staging directory,
tracked by `mosaic_onboarded` in this skill's config), routine invocations
of this skill are data-producing runs only — they execute `lc.sh`, which
writes new/updated problem records to
`~/.local/share/mosaic/data/leetcode-trainer/`; mosaic serves it
automatically, no separate publish step. Modifying `webapp/app.json`,
`webapp/static/`, the onboarding symlink, or `lc.sh`/`lc_core.py`'s own
logic is a distinct action, done only when the user explicitly asks for it
— never as a side effect of adding, swapping, or removing a problem.

## Read next

| file | when |
|---|---|
| `references/schema.md` | authoring or validating a problem record |
| `references/add-workflow.md` | adding, swapping, or removing a problem — read every time |
| `references/top-100.json` | the starter checklist, and how it was assembled |
