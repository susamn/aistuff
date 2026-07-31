# Adaptation Rules for Imported Skills

When importing an external skill, follow these exact conversion rules to integrate it seamlessly into the local environment.

## 1. Frontmatter Standardization

Ensure YAML frontmatter adheres strictly to the house schema:

```yaml
---
name: kebab-case-name
description: Clear single-line summary ending with "Use when <trigger>."
version: 1.0.0
kind: guidance | pipeline | hybrid
triggers:
  - "natural language trigger phrase"
intent: intent-category (e.g., meta, execution, system, analysis, planning)
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
guardrails:
  - Concise guardrail rule
resources:
  - <SKILL_PATH>/scripts/run.sh
tools:
  - bash
  - git
---
```

### Frontmatter Checks:
- **`name`**: Must be kebab-case (`^[a-z0-9]+(-[a-z0-9]+)*$`).
- **`kind`**: Must be explicitly set to `guidance`, `pipeline`, or `hybrid`.
  - `guidance`: Prose only, zero scripts.
  - `pipeline`: Has script(s) operating on data, outputs compact summary projections + artifact handles.
  - `hybrid`: Cleanly separated guidance and script sections.
- **`tools`**: Must list ONLY real binary executables installed on the system (e.g., `bash`, `python3`, `git`, `jq`, `stow`). Remove LLM tool primitives like `view_file`, `write_to_file`, `read_file`.
- **`resources`**: All skill-relative paths must use `<SKILL_PATH>/...` notation instead of `./` or hardcoded paths.

## 2. Path & Environment Conversions

Replace any hardcoded home paths (`/home/user`, `~`, `/Users/...`) or literal directory paths with official environment variables:

| Original Pattern | Target House Environment Variable / Placeholder |
|---|---|
| `/home/*/workspace/scripts` or `./scripts/` (shared) | `$SCRIPTS_PATH` |
| `/home/*/workspace/tools` or `./tools/` (shared) | `$TOOLS_PATH` |
| `/home/*/workspace` | `$WORKSPACE_PATH` |
| `/home/*/.m2` | `$M2_HOME` |
| Skill-relative script or reference file | `<SKILL_PATH>/scripts/...` or `<SKILL_PATH>/references/...` |

Never bypass shared dependency caches (`$M2_HOME`, `$CARGO_HOME`, `$NPM_CONFIG_CACHE`, `$PIP_CACHE_DIR`, `$GOPATH`).

## 3. Script & Boundary Adjustments

- **Total vs. Judgment**: Ensure counting, parsing, diffing, and formatting live in scripts; reasoning, ranking, recommendations, and failure recovery decisions stay with the agent.
- **Summary Projections**: If the imported skill is `pipeline` or `hybrid`, verify its script emits a single-line summary projection per finding and prints `<artifact>: /path/to/file.json` on the last line.
## 4. Line Budgeting & References

- `SKILL.md` hard ceiling is **200 lines** (target: 100–150 lines).
- **Extraction Rule**: If the imported skill's main markdown file exceeds 200 lines, extract detailed sections, domain documentation, workflows, or templates into `references/<topic>.md` files and link them in a `## Read next` table inside `SKILL.md`.
- **Content Integrity Constraint**: Splitting into `references/` MUST be performed so that **all original content remains 100% intact** without any loss of instructions, details, rules, or logic. Do NOT abbreviate, summarize away, or drop any original text—relocate whole sections into reference markdown files and reference them on demand.

## 5. Data-App / Mosaic Dashboard Adaptation

If the imported skill includes or is chosen to have a Mosaic dashboard tile (see `skill-creator/references/data-app-skills.md`):

- **Manifest**: Must have `webapp/app.json` with `id` set to the exact kebab-case skill `name`, `version`, `entry` (e.g. `index.html`), `name`, and `description`.
- **Data Location**: Output generation script must write runtime data directly to `~/.local/share/mosaic/data/<id>/`.
- **Mosaic Onboarding**: Run `$TOOLS_PATH/mosaic/scripts/onboard.sh <SKILL_PATH>/webapp` (never use `do-stow` or `do-unstow` for webapp onboarding).
- **Prose Note**: Ensure `SKILL.md` includes a "Steady state, once onboarded to mosaic" section explaining that data runs write to `~/.local/share/mosaic/data/<id>/`.

## 6. Registration & Deployment Checklist

1. **Target Path**: Move/copy the adapted skill directory to `~/dotfiles/workspace/aistuff/skills/<skill-name>/`.
2. **Registration**: Add entry to `~/dotfiles/workspace/aistuff/skills/AGENTS-TEMPLATE.md` under `## Available skills`:
   `| `<name>` | `<intent>` | "<triggers>" | YYYY-MM-DD | YYYY-MM-DD | `<source-url>` | Yes |`
3. **Deploy**: Run `bash ~/dotfiles/do-stow.sh`.
4. **Audit**: Run `~/dotfiles/workspace/aistuff/skills/skill-manager/scripts/audit.sh <skill-name>`.
