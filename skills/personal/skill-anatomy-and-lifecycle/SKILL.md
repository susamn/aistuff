---
name: skill-anatomy-and-lifecycle
description: Reference template for the shape of a skill — directory layout, full frontmatter schema, required fields, and what changes per kind. Use when scaffolding a skill by hand, checking whether one is shaped correctly, or asking "what does a skill look like."
version: 1.0.0
kind: meta
triggers:
  - "skill template"
  - "skill anatomy"
  - "skill lifecycle"
  - "what does a skill look like"
  - "SKILL.md schema"
created_at: 2026-08-01
updated_at: 2026-08-01
---

# Skill anatomy

The template every skill is shaped from. This is the reference. Read it to know what a correct skill looks like.

## Skill template

```yaml
---
name: skill-name                    # REQUIRED — must equal the directory name
description: What it does. Use when [trigger].   # REQUIRED — primary trigger
version: 1.0.0                      # REQUIRED — SemVer
kind: data | guidance | system | media | meta | debug # REQUIRED
triggers:                           # REQUIRED — natural-language activations
  - "phrase a user would actually say"
created_at: YYYY-MM-DD              # REQUIRED — ISO 8601
updated_at: YYYY-MM-DD              # REQUIRED — bump on every substantive edit

# ---- optional below this line ----
intent:                               # REQUIRED, one or more
  - code-review
  - planning
  - analysis
  - lifecycle
  - preparation
  - generation
config_dir: ~/.config/skill-config/skill-name   # ONLY if real persistent state
guardrails:
  - Do not X
resources:
  - <SKILL_PATH>/scripts/run.sh     # skill-local — the default
  - ~/absolute/path                 # a fixed location outside the skill if the skill needs it
tools:
  - bash
  - git
  - python
  - node
  - docker
  - kubectl
  - curl
  - jq
  - gh
  - brew
  - etc...
onchange:
  - "Update the skill's version and the updated_at timestamp in SKILL.md"
  - "Update the _TIMELINE.yaml_ in the {{INSTRUCTION_DIR}} entry for this skill"
    - The new path if the skill was moved
    - Other changes to the skill's triggers, intent, or kind
    - If the skill was disabled, remove it from the TIMELINE
    - If the skill was enabled, add it to the TIMELINE
    - If the skill depends on other skills, add them to the TIMELINE
    - Others....
depends_on:
  - skill-name
markforreview:
  - "Example only: The skill is not compatible with house rules as it mentions to read a secured resource."
---

Then the rest of the SKILL.md is freeform, but should be structured markdown.

```

## Directory layout

```
skills/<category>/<skill-name>/
├── SKILL.md            # required — router: what to do, when, what to read next
├── scripts/             # pipeline/hybrid only — executable, one entrypoint w/ modes
├── references/          # detail moved out of SKILL.md, loaded on demand
├── prompts/              # optional — example prompts, one per usage scenario
├── fixtures/            # optional — sample data for testing the skill itself
├── webapp/              # optional — only if data-app
└── evals/              # optional — contains skill-specific evaluation scripts
```

`<category>` is one of
- engineering/ 
- productivity/
- misc/ 
- personal/ 
- in-progress/
- deprecated/


## Budget

SKILL.md itself: ~100–150 lines typical, **200 is the hard ceiling**. Past that,
move a whole topic to `references/<topic>.md` rather than trimming sentences to
win lines.

## Shape by kind

See table to determine the skill kind when authoring a new skill or auditing an existing one. The `test` column describes how to verify that a skill is shaped correctly for its kind. 

| kind | test |
|---|---|
| `guidance` | Judgment only, nothing to compute. SKILL.md + `references/`. **Zero scripts.** |
| `system` | Deals with system-level operations. For example in linux, windows or macos. This type of skill will produce results by means of executing scripts.|
| `debug` | This type of skill is used to debug a system or a codebase. It will produce results by means of executing scripts and interracting with external systems via terminal or IDE. |
| `media` | Handles media-related tasks. Media like photos, music, videos or any kids. Programatic exection may require *ffmpeg* installation. |
| `meta` | This type of skill works on skills themselves. They may create, modify, audit or evaluate other skills. |
| `data` | This type of skill is used to analyze data or information. It will produce results by means of executing scripts and interacting with external systems via terminal or IDE. |



# Skill lifecycle

## Versioning

- Patch — wording, typos, clarifications
- Minor — new capability, new reference, new script
- Major — contract change: renamed script, changed output shape


## Lifecycle management

Here are some points about a skill's lifecycle. A skill must follow these rules to be considered well-formed and maintainable.

- The `kind` is the adjective of the skill. The `intent` is the verb of the skill.
- Determinable work out of inference, raw data out of context.
- If a skill is mainly dealing with data and has a lot of scripts, the data processing must be done mostly by scripts. The skill should not load too much data into context. If the data generated or processed by one script is needed by another script, it should be written to disk and read by the next script. A good skill keeps the context lean and only expose the data the context needs to make a decision.
- A skill can have configuration, but it is optional. If not, don't declare a `config_dir` in its frontmatter.Signals you genuinely need it: 
  - The skill writes data that outlives a run
  - The user tunes behaviour that should survive
  - The skill must avoid repeating work.
- When `config_dir` is declared, a skill will follow this config protocol:
  - **Location** — `~/.config/skill-config/<skill-name>/skill.properties`
  - **Format** — `key=value`, one per line, each with a comment explaining its use
  - **Initialization** — Creates directory and file on first run if absent, telling
    the user what is being created and why
  - **Loading** — Reads on activation and report which properties were loaded
  - **Writing** — Requests **explicit user approval
    first**, with the reason and the script that consumes it when adding or changing a property.
- Here are some points on good scripts for a skill. A skill must follow these rules to be considered well-formed and maintainable.
  - Resolves own location, dosen't assume cwd (skills are symlinked):
    - `SKILL_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"`
  - Declares external binaries in frontmatter `tools:`; check + exit `2` if missing
  - Every script must have one entrypoint with multiple modes, not multiple single-purpose scripts.
  - Streams protocol, a good script follows this:
    - **stdout**: Data only (projection or artifact path), machine-parseable
    - **stderr**: Diagnostics/progress, never parsed
    - **exit code**: `0` success · `1` violations found · `2` could not run

  - Failures notification protocol:
    - Never crashes with a raw stack trace on stdout — emits structured JSON instead:
      `{"status":"error","id":"...","reason":"one line","log":"/path/to.log","remedy":"optional"}`
    - `remedy` only for failures the script recognizes (missing binary, no auth, etc). Never guesses a remedy for unexpected errors.
    - Partial failure ≠ abort. Returns what succeeded + one error entry for what didn't.
    - The script reports failure; the **agent** decides what to do about it (retry/skip/fallback/ask).




