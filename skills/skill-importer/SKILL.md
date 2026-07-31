---
name: skill-importer
description: Import external skills from Git repositories, local directories, or web URLs into the local skills library, adapting them to house conventions, auditing, and suggesting cross-skill integrations. Use when importing a skill, bringing in an external skill, or adding a skill from GitHub.
version: 1.0.0
kind: hybrid
triggers:
  - "import a skill"
  - "import skill from"
  - "bring in skill"
  - "add skill from github"
intent: meta
created_at: 2026-07-31
updated_at: 2026-07-31
guardrails:
  - Always read foundation skills (skill-creator, skill-manager, dotfiles-management) before inspecting the candidate skill.
  - Present matching skills, compatibility conflicts, and uniqueness assessment to the user before modifying any skill files.
  - Require user confirmation before saving the adapted skill to the dotfiles repository.
  - Always run skill-manager audit on the imported skill after deployment and resolve any failing checks.
resources:
  - <SKILL_PATH>/scripts/fetch.sh
  - <SKILL_PATH>/references/adaptation-rules.md
  - <SKILL_PATH>/references/cross-skill-matrix.md
tools:
  - bash
  - git
  - curl
---

# Skill Importer

Import external skills from Git repositories, local folders, or remote web URLs into the local agent skill library, ensuring full compliance with house conventions, error-free auditing, and cross-skill lifecycle integration.

## Workflow

### Step 1 — Load House Foundation Skills
Before reading the candidate skill, inspect our core skill foundation to align with current ecosystem conventions:
1. View `skill-creator`: `skill-creator/SKILL.md` & `skill-creator/references/house-conventions.md`.
2. View `skill-manager`: `skill-manager/SKILL.md`.
3. View `dotfiles-management`: `dotfiles-management/SKILL.md`.

### Step 2 — Fetch & Read Candidate Skill
1. Execute the fetch helper script to stage the candidate skill in a temporary workspace:
   ```bash
   <SKILL_PATH>/scripts/fetch.sh <source> [subpath]
   ```
2. Read the staged skill's `SKILL.md`, scripts, references, and manifest files thoroughly.

### Step 3 — Perform Ecosystem & Skill-Creator Impact Analysis
Evaluate the candidate skill against `skill-creator` conventions across five dimensions:
1. **Existing Overlap**: Check `AGENTS-TEMPLATE.md` or `~/dotfiles/workspace/aistuff/skills/` for matching or conflicting skills.
2. **Skill-Creator Kind Classification**: Classify as `guidance` (prose only, zero scripts), `pipeline` (thin `SKILL.md` + `scripts/` + summary projection), or `hybrid`.
3. **Data-App / Mosaic Dashboard Assessment**: Determine if the skill produces visual data/reports that should be backed by a Mosaic dashboard tile (`references/data-app-skills.md`). Check if `webapp/app.json` exists or if adding a webapp tile is beneficial.
4. **House Conventions & Conflicts**: Check YAML frontmatter, line budgets (ceiling 200 lines—if >200 lines, extract into `references/<topic>.md` preserving 100% of original content intact), environment paths (`$WORKSPACE_PATH`, `$SCRIPTS_PATH`, `$TOOLS_PATH`, `<SKILL_PATH>`), executable tools list, and script output contracts.
5. **Uniqueness & Utility**: Assess how unique the new skill is, what functional gap it fills, and how it helps the user/agent ecosystem.

### Step 4 — Present Analysis & Ask Questions
Present a clear summary report to the user containing:
- Candidate skill name & source.
- Overlap with existing skills (if any).
- `skill-creator` classification & Data-App assessment (e.g., whether a Mosaic `webapp/` tile is recommended).
- House convention conflicts & required adaptations (including any reference extractions needed for files >200 lines).
- Uniqueness & value-add assessment.
- **Clarifying Questions**: Ask the user to confirm decisions (e.g. "Do you want to enable a live Mosaic dashboard tile for this skill?").

### Step 5 — Adapt, Register, Deploy & Audit
Upon user confirmation:
1. Copy the skill to `~/dotfiles/workspace/aistuff/skills/<skill-name>/`.
2. Apply conversion rules from [`references/adaptation-rules.md`](file://<SKILL_PATH>/references/adaptation-rules.md) (frontmatter schema, path placeholders, tool verification, permissions). **If `SKILL.md` >200 lines**, extract detailed topics into `references/<topic>.md` while ensuring 100% of original content, logic, and instructions remain fully intact.
3. Register the new skill in `~/dotfiles/workspace/aistuff/skills/AGENTS-TEMPLATE.md` under `## Available skills`, including its original URL/path in the `Source` column.
4. Deploy skill symlinks and update agent instructions:
   ```bash
   bash ~/dotfiles/do-stow.sh
   ```
5. Run the compliance audit:
   ```bash
   ~/dotfiles/workspace/aistuff/skills/skill-manager/scripts/audit.sh <skill-name>
   ```
   Fix any reported audit issues and re-run until clean.

### Step 6 — Recommend Cross-Skill Integrations
1. Analyze existing skills in `AGENTS-TEMPLATE.md` to identify lifecycle integration opportunities using [`references/cross-skill-matrix.md`](file://<SKILL_PATH>/references/cross-skill-matrix.md).
2. Prompt the user with specific recommendations on which existing skills (e.g., `brainstorming`, `pr-review`) could load or reference this new skill during their lifecycle.

## Read next

| file | when |
|---|---|
| `references/adaptation-rules.md` | Adapting frontmatter, paths, budgets, and scripts |
| `references/cross-skill-matrix.md` | Evaluating cross-skill integration opportunities |
| `prompts/import-skill.md` | Example prompts for importing skills from various sources |
