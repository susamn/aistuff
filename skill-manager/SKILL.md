---
name: skill-manager
description: Audit and standardize agent skills against established repository patterns.
version: 1.1.0
triggers:
  - "audit my skills"
  - "check skill compliance"
  - "manage skills"
  - "standardize skill"
intent: system
config_dir: ~/.config/skill-config/skill-manager
guardrails:
  - Do not modify skills without user confirmation for each change.
  - Ensure YAML frontmatter is valid and contains all required fields.
created_at: 2026-05-30
updated_at: 2026-06-18
---

# Skill Manager

## Skill Configuration

This skill uses `~/.config/skill-config/skill-manager/skill.properties` to track audit history and preferred standards.

Before starting an audit, check if `~/.config/skill-config/skill-manager/` and `skill.properties` exist. If not, create them and notify the user: "Creating configuration directory and default properties file for skill-manager to store your audit history and enforcement standards." Any new property added or saved back to this file MUST be approved by the user beforehand. When loading the file, explicitly report the loaded entries to the user.

### Common Properties
- `last_audit_date`: Timestamp of the last full audit.
- `enforce_strict_config`: `true`/`false`.

Before starting an audit, check `~/.config/skill-config/skill-manager/skill.properties` for enforcement settings.

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
  - `config_dir`: Path to configuration directory (e.g., `~/.config/skill-config/<name>`).
  - `created_at`: ISO 8601 format (YYYY-MM-DD).
  - `updated_at`: ISO 8601 format (YYYY-MM-DD).
- **Optional Fields**: `guardrails`, `resources`, `tools`.

### 2. Path Placeholders
- Use `<SKILL_PATH>` for any absolute path references internal to the skill.
- Use `{{AGENT_SKILLS_PATH}}` for global agent-relative paths if necessary.

### 3. Skill Configuration Loading
- The body MUST include instructions to read `~/.config/skill-config/<skill-name>/skill.properties` upon loading.
- The skill MUST explicitly mention to print/log the loaded properties to the user upon reading them.
- The skill MUST contain instructions to create the config folder and `skill.properties` file if they do not exist, printing a message to the user explaining why they are being created.
- During an audit, check if the config directory and `skill.properties` file actually exist on the current machine. If they do not exist, explicitly notify the user about their absence.
- Check if scripts use these properties and if the skill updates the config file with useful state.
- Ensure the skill body explicitly states that any action to add or save a new property back to `skill.properties` requires explicit user consultation and approval beforehand.

### 4. Conciseness & Structure
- No "README" or "CHANGELOG" style filler.
- Body must be clear, step-by-step instructions.
- Ensure no duplicate rules or contradictory guidance.

## Step 3: Propose & Fix
Present a summary of findings (Passed/Failed) for each check. If any checks fail, propose the exact `replace` or `write_file` calls needed to fix them and wait for user approval.

## Step 4: Sync
After changes, remind the user to run `./do-stow.sh` (or offer to do it) to deploy the updated skills to the agents.
