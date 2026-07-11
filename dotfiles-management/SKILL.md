---
name: dotfiles-management
description: Manage the dotfiles repository, stow packages, and configure agent skills
version: 1.1.0
triggers:
  - "manage dotfiles"
  - "add a skill"
  - "modify stow setup"
  - "work inside dotfiles"
intent: system
config_dir: ~/.config/skill-config/dotfiles-management
guardrails:
  - Do not stow the skills/ directory.
  - Do not use absolute paths when environment variables are available.
  - Document any new shell aliases in workspace/.alias_descriptions.
resources:
  - ./do-stow.sh
  - ./do-unstow.sh
tools:
  - bash
interface:
  input:
    task: "string — description of the dotfiles management task"
  output:
    status: "string — outcome of the operation"
created_at: 2026-05-30
updated_at: 2026-06-18
---
## Dotfiles management

## Skill Configuration

This skill uses `~/.config/skill-config/dotfiles-management/skill.properties` for stow preferences and deployment paths.

Before performing any stow operation, check if `~/.config/skill-config/dotfiles-management/` and `skill.properties` exist. If not, create them and notify the user: "Creating configuration directory and default properties file for dotfiles-management to store your stow and target directory preferences." Any new property added or saved back to this file MUST be approved by the user beforehand. When loading the file, explicitly report the loaded entries to the user.

### Common Properties
- `stow_dir`: (e.g., `~/dotfiles`)
- `target_dir`: (e.g., `~`)

Before performing any stow operation, check `~/.config/skill-config/dotfiles-management/skill.properties` for the correct paths.

> **Only relevant when you are explicitly helping the user manage their dotfiles**
> (i.e. the user has asked you to add a skill, modify the stow setup, or work inside
> `~/dotfiles/`). If you are helping with any other task, ignore this section.

### Repository layout

```
~/dotfiles/
├── .config/          # app configs (Hyprland, kitty, nvim, waybar, rofi, …)
├── workspace/        # scripts, tools, sdk, services (stowed to ~/workspace/)
├── skills/           # canonical skill definitions — NOT stowed to ~
│   ├── .agents       # agent deployment config (skills path + instruction file)
│   └── <skill-name>/
│       └── SKILL.md
├── do-stow.sh        # stow dotfiles + deploy skill and instruction symlinks
├── do-unstow.sh      # reverse of do-stow.sh
└── AGENTS.md         # this file
```

`skills/` is excluded from stow. `do-stow.sh` deploys skill symlinks to each
agent's skills directory and creates instruction file symlinks (e.g.
`~/.claude/CLAUDE.md`) outside the repo.

### Stow commands

```bash
./do-stow.sh          # full setup
./do-unstow.sh        # full teardown
stow -vt ~ .          # manual stow (.stow-local-ignore handles exclusions)
stow -Dvt ~ .         # manual unstow
stow -vt ~ . --adopt  # resolve conflicts
```

### SKILL.md schema

```yaml
---
name: skill-name
description: one-line summary
version: 1.0.0
triggers:
  - "natural language phrase"
intent: code-review | git | system | debug | media | …
config_dir: ~/.config/skill-config/skill-name
guardrails:
  - Do not X
resources:
  - ./scripts/script-name.sh  # Relative to skill directory
  - $TOOLS_PATH/tool-name     # Global tools
tools:
  - bash
interface:
  input:
    param: "type — description"
  output:
    result: "type — description"
---
Markdown body: step-by-step instructions for the agent. Use <SKILL_PATH> placeholder for absolute paths.
```

### Adding a new agent

Edit `skills/.agents` (three columns: name, skills path, instruction file path):

```
gemini   ~/.gemini/skills   ~/.gemini/GEMINI.md
cursor   ~/.cursor/rules    -
```

Then run `./do-stow.sh` and commit `skills/.agents`.
