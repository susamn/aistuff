---
name: dotfiles-management
description: Manage the dotfiles repository, stow packages, and configure agent skills. Use when adding a skill, modifying the stow setup, or working inside ~/dotfiles.
version: 2.2.0
kind: guidance
triggers:
  - "manage dotfiles"
  - "add a skill"
  - "modify stow setup"
  - "work inside dotfiles"
intent: system
guardrails:
  - Do not stow the workspace/aistuff/ directory.
  - Do not use absolute paths when environment variables are available.
  - Document any new shell aliases in workspace/.alias_descriptions.
resources:
  - ~/dotfiles/do-stow.sh          # repo root, not skill-relative
  - ~/dotfiles/do-unstow.sh
  - ~/dotfiles/workspace/aistuff/skills/AGENTS-TEMPLATE.md
  - <SKILL_PATH>/references/personal-systemd-services.md
  - <SKILL_PATH>/references/music-sync-and-mpd.md
tools:
  - bash
  - stow
  - git
created_at: 2026-05-30
updated_at: 2026-08-16
---
# Dotfiles management

> **Only relevant when you are explicitly helping the user manage their dotfiles**
> (i.e. the user has asked you to add a skill, modify the stow setup, or work inside
> `~/dotfiles/`). If you are helping with any other task, ignore this section.

### Repository layout

```
~/dotfiles/
├── .config/            # app configs (Hyprland, kitty, nvim, waybar, rofi, …)
├── workspace/          # scripts, tools, sdk, services (stowed to ~/workspace/)
│   ├── aistuff/            # git submodule — agent assets, NOT stowed to ~
│   │   ├── mcp/                # MCP server definitions, synced by workspace/scripts/agm.sh
│   │   └── skills/             # canonical skills
│   │       ├── .agents             # agent deployment config (4 columns, see below)
│   │       ├── AGENTS-TEMPLATE.md  # source of every agent's instruction file
│   │       └── <skill-name>/
│   │           └── SKILL.md
├── .ignored            # extra ignore patterns read by do-stow.sh
├── .stow-local-ignore  # stow's ignore list (REPLACES stow's built-in defaults)
├── do-stow.sh          # stow + deploy skills + generate instructions + sync mcp
├── do-unstow.sh        # reverse of do-stow.sh
└── onboard.sh          # first-run machine bootstrap
```

`workspace/aistuff/` is excluded from stow via `^workspace/aistuff$` in `.stow-local-ignore`, so
neither the skills submodule nor the MCP definitions land in `~`.
`do-stow.sh` then does three things beyond stowing:

1. **Skills** — symlinks every active skill into **every** agent's skills path.
   There is no per-agent skill selection; all agents receive all skills.
2. **Instructions** — *generates* each agent's instruction file from
   `workspace/aistuff/skills/AGENTS-TEMPLATE.md`, substituting `{{AGENT_SKILLS_PATH}}` and
   `{{INSTRUCTION_PATH}}`. These are **real files, not symlinks, and they are
   overwritten on every run.** Never edit `~/.claude/CLAUDE.md` directly — the
   change will be silently lost. Edit `workspace/aistuff/skills/AGENTS-TEMPLATE.md` instead.
3. **MCP** — runs `workspace/scripts/agm.sh sync`, which merges
   `workspace/aistuff/mcp/mcp-servers.json` into each agent's MCP config.

### Enabling and disabling a skill

Deployment is decided by directory name alone: a skill directory suffixed
`.disabled` has its symlink actively removed from every agent and is not
deployed. Nothing reads the `Enabled` column in the skills table — it is
documentation that must be updated by hand to match.

```bash
mv ~/dotfiles/workspace/aistuff/skills/<name> ~/dotfiles/workspace/aistuff/skills/<name>.disabled  # disable
mv ~/dotfiles/workspace/aistuff/skills/<name>.disabled ~/dotfiles/workspace/aistuff/skills/<name>  # re-enable
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

Edit `workspace/aistuff/skills/.agents` — four whitespace-separated columns, `-` meaning "none":

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

Then run `./do-stow.sh`. Because `workspace/aistuff` is a submodule, committing is
two steps: commit changes inside `~/dotfiles/workspace/aistuff`, then
`git add workspace/aistuff` in `~/dotfiles` to bump the submodule pointer.

### Personal systemd services

Stow places unit *files*; it does not make systemd aware of them. `do-stow.sh`
must be followed by `systemctl --user daemon-reload`, and membership in
`personal-services.target` is declared by each unit's own `[Install]` section —
not by the target. The target itself is owned by `linux-system-manager` and only
symlinked from dotfiles.

The failure modes here are silent: systemd accepts the broken configuration and
runs nothing. Read `references/personal-systemd-services.md` before adding a
personal service or timer, moving one between scopes, or diagnosing one that
"enabled fine" but never runs.

### Music sync and MPD

`~/.config/mpd/mpd.conf` is **generated**, not stowed — `mpdc configure` rebuilds
it from the version-controlled `mpd.conf.bak` template plus two rclone-sync
profiles, so direct edits to `mpd.conf` are silently discarded. A profile's
`LOCAL_PATH` is the single source of truth for where music lives; changing it
without re-running `mpdc configure` leaves MPD pointed at the old directory.

Read `references/music-sync-and-mpd.md` before editing a sync profile, moving the
library, or debugging a sync that ran but changed nothing.

### Read next

| file | when |
|---|---|
| `references/personal-systemd-services.md` | adding/moving/debugging a personal service or timer, or touching `personal-services.target` |
| `references/music-sync-and-mpd.md` | rclone sync profiles, `mpd.conf` generation, music library paths |
