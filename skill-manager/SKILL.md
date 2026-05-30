---
name: skill-manager
description: Audit and standardize agent skills against established repository patterns.
version: 1.0.0
triggers:
  - "audit my skills"
  - "check skill compliance"
  - "manage skills"
  - "standardize skill"
intent: system
guardrails:
  - Do not modify skills without user confirmation for each change.
  - Ensure YAML frontmatter is valid and contains all required fields.
created_at: 2026-05-30
updated_at: 2026-05-30
---

# Skill Manager

Workflow for auditing and standardizing agent skills in the `~/dotfiles/skills/` directory.

## Step 1: List & Select
List all directories in `~/dotfiles/skills/` (excluding hidden ones and the `.agents` file). Present them to the user and ask which one(s) they would like to audit.

## Step 2: Audit Checklist
For each selected skill, read its `SKILL.md` and check for:

### 1. YAML Frontmatter
- **Presence**: Must start and end with `---`.
- **Fields**:
  - `name`: Matches directory name.
  - `description`: Concise summary.
  - `version`: SemVer format.
  - `triggers`: A list of natural language phrases.
  - `intent`: One of (code-review, git, system, debug, media, planning, execution).
  - `created_at`: ISO 8601 format (YYYY-MM-DD).
  - `updated_at`: ISO 8601 format (YYYY-MM-DD).
- **Optional Fields**: `guardrails`, `resources`, `tools`.

### 2. Path Placeholders
- Use `<SKILL_PATH>` for any absolute path references internal to the skill.
- Use `{{AGENT_SKILLS_PATH}}` for global agent-relative paths if necessary.

### 3. Conciseness & Structure
- No "README" or "CHANGELOG" style filler.
- Body must be clear, step-by-step instructions.
- Ensure no duplicate rules or contradictory guidance.

## Step 3: Propose & Fix
Present a summary of findings (Passed/Failed) for each check. If any checks fail, propose the exact `replace` or `write_file` calls needed to fix them and wait for user approval.

## Step 4: Sync
After changes, remind the user to run `./do-stow.sh` (or offer to do it) to deploy the updated skills to the agents.
