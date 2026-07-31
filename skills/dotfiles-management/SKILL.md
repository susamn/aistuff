---
name: dotfiles-management
description: Manage the dotfiles repository, stow packages, and configure agent skills. Use when adding a skill, modifying the stow setup, or working inside ~/dotfiles.
version: 2.0.0
kind: guidance
triggers:
  - "manage dotfiles"
  - "add a skill"
  - "modify stow setup"
  - "work inside dotfiles"
intent: system
guardrails:
  - Do not stow the aistuff/ directory.
  - Do not use absolute paths when environment variables are available.
  - Document any new shell aliases in workspace/.alias_descriptions.
resources:
  - ~/dotfiles/do-stow.sh          # repo root, not skill-relative
  - ~/dotfiles/do-unstow.sh
  - ~/dotfiles/aistuff/skills/AGENTS-TEMPLATE.md
tools:
  - bash
  - stow
  - git
created_at: 2026-05-30
updated_at: 2026-07-29
---
# Dotfiles management

> **Only relevant when you are explicitly helping the user manage their dotfiles**
> (i.e. the user has asked you to add a skill, modify the stow setup, or work inside
> `~/dotfiles/`). If you are helping with any other task, ignore this section.

### Repository layout

```
~/dotfiles/
├── .config/            # app configs (Hyprland, kitty, nvim, waybar, rofi, …)
├── aistuff/            # git submodule — agent assets, NOT stowed to ~
│   ├── mcp/                # MCP server definitions, synced by workspace/scripts/agm.sh
│   └── skills/             # canonical skills
│       ├── .agents             # agent deployment config (4 columns, see below)
│       ├── AGENTS-TEMPLATE.md  # source of every agent's instruction file
│       └── <skill-name>/
│           └── SKILL.md
├── workspace/          # scripts, tools, sdk, services (stowed to ~/workspace/)
├── .ignored            # extra ignore patterns read by do-stow.sh
├── .stow-local-ignore  # stow's ignore list (REPLACES stow's built-in defaults)
├── do-stow.sh          # stow + deploy skills + generate instructions + sync mcp
├── do-unstow.sh        # reverse of do-stow.sh
└── onboard.sh          # first-run machine bootstrap
```

`aistuff/` is excluded from stow via `^aistuff$` in `.stow-local-ignore`, so
neither the skills submodule nor the MCP definitions land in `~`.
`do-stow.sh` then does three things beyond stowing:

1. **Skills** — symlinks every active skill into **every** agent's skills path.
   There is no per-agent skill selection; all agents receive all skills.
2. **Instructions** — *generates* each agent's instruction file from
   `aistuff/skills/AGENTS-TEMPLATE.md`, substituting `{{AGENT_SKILLS_PATH}}` and
   `{{INSTRUCTION_PATH}}`. These are **real files, not symlinks, and they are
   overwritten on every run.** Never edit `~/.claude/CLAUDE.md` directly — the
   change will be silently lost. Edit `aistuff/skills/AGENTS-TEMPLATE.md` instead.
3. **MCP** — runs `workspace/scripts/agm.sh sync`, which merges
   `aistuff/mcp/mcp-servers.json` into each agent's MCP config.

### Enabling and disabling a skill

Deployment is decided by directory name alone: a skill directory suffixed
`.disabled` has its symlink actively removed from every agent and is not
deployed. Nothing reads the `Enabled` column in the skills table — it is
documentation that must be updated by hand to match.

```bash
mv ~/dotfiles/aistuff/skills/<name> ~/dotfiles/aistuff/skills/<name>.disabled  # disable
mv ~/dotfiles/aistuff/skills/<name>.disabled ~/dotfiles/aistuff/skills/<name>  # re-enable
bash ~/dotfiles/do-stow.sh                                                     # apply
```

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

Edit `aistuff/skills/.agents` — four whitespace-separated columns, `-` meaning "none":

| column | meaning |
|---|---|
| `name` | agent identifier |
| `skills_path` | where skill symlinks are deployed |
| `instruction_symlink` | absolute path of the generated instruction file |
| `mcp_config_path` | absolute path for the synced MCP servers JSON |

```
gemini   ~/.gemini/skills   ~/.gemini/GEMINI.md   ~/.gemini/mcp.json
cursor   ~/.cursor/rules    -                     ~/.cursor/mcp.json
```

Then run `./do-stow.sh`. Because `aistuff` is a submodule, committing is
two steps: commit changes inside `~/dotfiles/aistuff`, then
`git add aistuff` in `~/dotfiles` to bump the submodule pointer.
