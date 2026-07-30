---
name: skill-creator
description: Guide for creating effective skills that extend different agents' capabilities. Use when creating new skills or updating existing skills with specialized knowledge, workflows, or tool integrations.
version: 2.4.0
kind: hybrid
triggers:
  - "create a new skill"
  - "add a skill"
intent: meta
config_dir: ~/.config/skill-config/skill-creator
guardrails:
  - Classify the skill before writing it. Guidance skills get zero scripts; pipeline skills keep judgment out of code.
  - A script must never dump raw data into agent context — emit a projection plus a handle to the full artifact.
  - SKILL.md is a router. Detail belongs in references/, loaded on demand.
  - A skill update that changes behavior updates its prompts/ too, if it has one — stale examples are worse than none.
resources:
  - <SKILL_PATH>/scripts/scaffold.sh
  - <SKILL_PATH>/references/frontmatter.md
  - <SKILL_PATH>/references/script-contract.md
  - <SKILL_PATH>/references/guidance-skills.md
  - <SKILL_PATH>/references/data-app-skills.md
  - <SKILL_PATH>/references/webapp-list-view.md
  - <SKILL_PATH>/references/webapp-card-board.md
  - <SKILL_PATH>/prompts/create-data-app-skill.md
  - <SKILL_PATH>/prompts/migrate-to-data-app-skill.md
tools:
  - bash
created_at: 2026-05-30
updated_at: 2026-07-30
---

# Skill Creator

**Read `references/house-conventions.md` first.** It carries the path, tooling,
deployment, and working-style conventions of this setup — a skill that ignores them
is valid and still feels foreign. Optional config:
`~/.config/skill-config/skill-creator/skill.properties` (`default_author`,
`auto_stow_after_creation`), protocol in `references/frontmatter.md`.

## Step 0 — Classify before writing

Every skill is one of three kinds, declared as `kind:` in frontmatter. The kind
determines the entire shape of the skill. Choosing wrong is the most expensive
mistake available here, because it is discovered only after the skill is written.

| kind | test | shape |
|---|---|---|
| `guidance` | Encodes judgment. Nothing to compute at runtime. | Prose only. **Zero scripts.** Router SKILL.md + `references/`. |
| `pipeline` | Operates on real data — files, repos, APIs, metrics. | Thin SKILL.md + `scripts/` + a declared output contract. |
| `hybrid` | Both, in cleanly separable sections. | Declare which sections are which. Suspect it is really two skills. |

If you cannot name the concrete runtime input a script would read, it is
`guidance`. Adding scripts to a guidance skill produces rigid output that is
wrong in every situation the author did not foresee.

## The boundary rule

Do not ask "can this be scripted." Ask whether the operation is **total** or a
**judgment**.

- **Total** — exactly one right answer for every input: counting, parsing,
  filtering, sorting, diffing, aggregating, schema validation, formatting.
  Always a script. An agent doing this is slow, expensive, and wrong at the edges.
- **Judgment** — depends on context: relevance, ranking, causation, what to
  recommend, what to tell the user, and **what to do when a script fails**.
  Always the agent. Freezing judgment into code yields output that is confidently
  wrong wherever the author's guess ran out.

Corollary: **tunable values live in data, the logic applying them lives in code.**
Thresholds, weights, and limits belong in a JSON or properties file beside the
script, never inline. Retuning must be an edit to data, not to logic.

## The two boundaries

A pipeline skill has two places data crosses a line. Both must be designed; only
the first is obvious.

1. **script → script** — intermediate artifacts on disk under a versioned schema.
   These stay out of context entirely.
2. **script → agent** — the one that gets forgotten. The agent must never read a
   full artifact in order to say three sentences about it. Every pipeline skill
   ships a **summary projection** (one compact line per finding) *and* the
   **path to the full artifact** so the agent can drill down when a number looks
   wrong.

Compression is not free — it is inference relocated to authoring time, where you
know less than the agent will at runtime. So compress to preserve
decision-relevant variance, and always leave the escape hatch. A summary with no
handle back to the data is a dead end.

Full contract: `references/script-contract.md`. Read it before writing any
pipeline skill.

## Script granularity

One script with modes beats many single-purpose scripts. Every script is a
contract to keep in sync, so N scripts means N places for schema drift — prefer
`run.sh analyze | summary | verbose` over three separate files.

Two counterweights, both real failure modes:

- **Don't build infrastructure for a one-off.** A task run once needs no artifact
  schema, no threshold file, no projection. Write the ten-line script.
- **Don't overengineer.** Structure earns its place when a second caller or a
  second run demands it, never in anticipation. Unused ceremony is exactly the
  clutter this design exists to remove.

## Budgets

- **Keep SKILL.md lean — a router: what to do, when, and what to read next.**
  Around 100–150 lines is typical; **200 is the hard ceiling.**
- Do not contort prose to hit a line count. If a skill genuinely needs 180 lines of
  always-relevant content, that is fine. Compressing sentences to win three lines
  costs readability and buys nothing.
- Past the ceiling, move whole topics to `references/<topic>.md` rather than
  trimming words. An oversized SKILL.md with no `references/` is the actual failure
  this guards against.

## Process

1. **Classify** — pick the `kind`. State it and the reasoning to the user.
2. **Understand** — gather concrete usage examples. For `pipeline`, name the exact
   runtime input and the decision its output supports. Also ask: does this need
   a live dashboard on mosaic, or is a generated report/artifact enough? If yes,
   it's data-app-backed — `references/data-app-skills.md`.
3. **Scaffold** — `<SKILL_PATH>/scripts/scaffold.sh <name> --kind <kind> [--webapp]`
4. **Write** — fill SKILL.md against the budget. Reference skill-local scripts as
   `<SKILL_PATH>/scripts/<script>`; use `$TOOLS_PATH` / `$SCRIPTS_PATH` only for
   genuinely global utilities living outside the skill.
5. **Prompts** — write `<SKILL_PATH>/prompts/<topic>.md` now, while the skill's
   purpose and triggers are freshest — this is the best time, not an
   afterthought. Short, directly usable example prompts, one file per distinct
   usage scenario. Skip it only when `triggers:` alone already says everything
   there is to say; write it once usage has more than one shape (e.g. "create
   new" vs. "migrate existing") or involves a reusable template worth saving —
   see `skill-creator`'s own `prompts/` for what that looks like.
6. **Register** — add a row to the `## Available skills` table in
   `~/dotfiles/skills/AGENTS-TEMPLATE.md`.
7. **Deploy** — `bash ~/dotfiles/do-stow.sh`
8. **Audit** — `~/dotfiles/skills/skill-manager/scripts/audit.sh <name>`.
   Must pass before committing.
9. **Commit** — `skills/` is a **git submodule**, so this is two commits:
   ```bash
   git -C ~/dotfiles/skills add <name>/ AGENTS-TEMPLATE.md
   git -C ~/dotfiles/skills commit -m "skills: add <name>"
   git -C ~/dotfiles add skills
   git -C ~/dotfiles commit -m "skills: bump submodule for <name>"
   ```
10. **Iterate** — improve from real usage. A behavior change is a prompts
    change too: if `prompts/` exists, revisit it in the same pass. Stale
    examples that no longer match current behavior are worse than no examples
    at all — they get trusted and then fail.

## Enabling and disabling a skill

Rename the directory to `<name>.disabled` and re-run `do-stow.sh` — the suffix is
the only mechanism. Update the table's `Enabled` cell in the same change, or the
two sources drift. Detail: `dotfiles-management`.

## What NOT to include

- README.md, CHANGELOG.md, installation guides, user-facing documentation
- Explanations a competent agent already has
- Config ceremony in a skill with nothing to configure — `config_dir` is
  **optional**, declared only when the skill has real persistent state
- Anything a competent agent already knows. Skills are for agents, not humans.

## Read next

| file | when |
|---|---|
| `references/house-conventions.md` | **always — before writing or editing any skill** |
| `references/frontmatter.md` | writing frontmatter; the config protocol |
| `references/script-contract.md` | any `pipeline` skill — required |
| `references/guidance-skills.md` | any `guidance` skill; splitting an oversized skill |
| `references/data-app-skills.md` | skill needs a live mosaic dashboard, not just a report |
| `references/webapp-list-view.md` | data-app's main view is a manifest-driven list with drill-down |
| `references/webapp-card-board.md` | data-app is a single-page Trello/Keep-style card board |
| `prompts/create-data-app-skill.md` | starting prompts for a brand-new data-app skill |
| `prompts/migrate-to-data-app-skill.md` | reusable template for porting an existing skill onto mosaic |
