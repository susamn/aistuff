---
name: skill-manager
description: Audit and standardize agent skills against the authoring contract — frontmatter validity, progressive-disclosure budgets, script/prose boundary, resource resolution, and registration/enabled-state consistency. Use when auditing skills, checking skill compliance, or standardizing a skill.
version: 2.0.0
kind: pipeline
triggers:
  - "audit my skills"
  - "check skill compliance"
  - "manage skills"
  - "standardize skill"
intent: system
guardrails:
  - Never modify a skill without showing the finding and getting confirmation for that specific change.
  - Report findings from the audit output only — do not re-derive them by reading every SKILL.md.
  - A failing check is evidence, not a verdict; some findings are deliberate choices.
resources:
  - <SKILL_PATH>/scripts/audit.sh
  - <SKILL_PATH>/scripts/audit.py
tools:
  - bash
  - python3
created_at: 2026-05-30
updated_at: 2026-07-29
---

# Skill Manager

Auditing is a total operation — every check has one right answer for a given
skill — so it lives in code. Run the audit, then spend judgment on what to do
about the findings, not on finding them.

## Workflow

1. **Audit.** Whole set, or named skills:

   ```bash
   ~/dotfiles/skills/skill-manager/scripts/audit.sh
   ~/dotfiles/skills/skill-manager/scripts/audit.sh java-generic obsidian
   ```

   Output is one line per finding — `SEV  skill  check  message` — and nothing
   else. Counts go to stderr. Exit `0` clean, `1` errors present, `2` unable to run.

2. **Triage.** Errors are contract violations. Warnings are judgment calls that
   may be deliberate — say so rather than mechanically "fixing" them.

3. **Propose.** Group findings by root cause, not by file. Show the exact edit
   for each and get confirmation per change. Several skills failing the same
   check usually means one shared fix.

4. **Deploy.** After edits, `bash ~/dotfiles/do-stow.sh`, then re-run the audit to
   confirm clean.

Read a skill's SKILL.md only when a finding needs interpretation. The audit line
plus the file path is the handle; opening all twenty files defeats the purpose.

## What the checks mean

| check | error condition |
|---|---|
| `frontmatter` | missing/unterminated block, or a missing required field |
| `kind` | invalid value; `guidance` skill carrying scripts; `pipeline` skill with none |
| `contract` | `pipeline` skill with no summary projection — the agent would have to read the full artifact |
| `budget` | SKILL.md over 200 lines; an **error** when there is no `references/` to split into |
| `resources` | a declared path that does not resolve, or a bare `./` relative path |
| `registration` | not listed in `AGENTS-TEMPLATE.md` |
| `enabled` | table `Enabled` cell disagrees with the `.disabled` directory suffix |
| `config` | describes `skill.properties` while declaring no `config_dir` |
| `scripts` | a shell script that is not executable |

The full authoring contract these enforce lives in `skill-creator`:
`references/frontmatter.md`, `references/script-contract.md`, and
`references/guidance-skills.md`. Consult those when a fix is not obvious.

## Adding a check

Checks are total operations and belong in `scripts/audit.py` — never as prose
instructions here. Add a call inside `audit()`, use `add("ERR"|"WARN", name,
check, msg)`, and keep the message to one line naming the specific offending
value. A check that cannot be decided mechanically is not a check; it is
guidance, and belongs in `skill-creator`.
