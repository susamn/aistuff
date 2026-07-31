# Frontmatter schema and the config protocol

## Full schema

```yaml
---
name: skill-name                    # REQUIRED — must equal the directory name
description: What it does. Use when [trigger].   # REQUIRED — primary trigger
version: 1.0.0                      # REQUIRED — SemVer
kind: guidance | pipeline | hybrid  # REQUIRED — see SKILL.md Step 0
triggers:                           # REQUIRED — natural-language activations
  - "phrase a user would actually say"
intent: code-review | git | system | debug | media | planning | execution | meta | analysis
created_at: YYYY-MM-DD              # REQUIRED — ISO 8601
updated_at: YYYY-MM-DD              # REQUIRED — bump on every substantive edit

# ---- optional below this line ----
config_dir: ~/.config/skill-config/skill-name   # ONLY if real persistent state
guardrails:
  - Do not X
resources:
  - <SKILL_PATH>/scripts/run.sh     # skill-local
  - $TOOLS_PATH/tool-name           # genuinely global tool
tools:
  - bash
  - git
---
```

`description` is the primary triggering mechanism — it decides whether the skill
is selected at all. Write it as *what it does* plus *when to use it*, using the
words a user would actually type.

## Path conventions in `resources:`

| form | means | use for |
|---|---|---|
| `<SKILL_PATH>/scripts/x.sh` | resolved to the skill's own directory at runtime | skill-local scripts — the default |
| `$TOOLS_PATH/x` / `$SCRIPTS_PATH/x` | global workspace utilities | tools shared across skills |
| `~/absolute/path` | a fixed location outside the skill | repo-level files, e.g. `~/dotfiles/do-stow.sh` |

Never write a bare `./x.sh` — it resolves against the caller's working directory,
not the skill, and silently breaks when the skill is reached through its symlink.
Every path in `resources:` must actually exist; `skill-manager` verifies this.

## `config_dir` is optional

Declare it **only** when the skill has real persistent state — cached data,
tuned thresholds, a record of prior runs. A skill with nothing to configure
must not declare it and must not carry any config prose. The ceremony costs
context on every invocation and buys nothing.

Signals you genuinely need it: the skill writes data that outlives a run; the
user tunes behaviour that should survive; the skill must avoid repeating work.

## The config protocol

When `config_dir` is declared, the skill follows this and states it in one line,
not three paragraphs:

- **Location** — `~/.config/skill-config/<skill-name>/skill.properties`
- **Format** — `key=value`, one per line, each with a comment explaining its use
- **Initialization** — create directory and file on first run if absent, telling
  the user what is being created and why
- **Loading** — read on activation and report which properties were loaded
- **Writing** — adding or changing a property requires **explicit user approval
  first**, with the reason and the script that consumes it

Scripts read the properties file directly. The agent does not relay values
between the file and the script.

## Versioning

- Patch — wording, typos, clarifications
- Minor — new capability, new reference, new script
- Major — contract change: renamed script, changed output shape, changed `kind`

Bump `updated_at` whenever `version` changes.
