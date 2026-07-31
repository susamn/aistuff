# House conventions

How skills fit this specific setup. A skill that ignores these is technically
valid and still feels foreign. Read before creating or editing any skill.

## Working style

These come from the user directly and outrank politeness:

- **Don't assume.** State assumptions explicitly; if uncertain, ask.
- **Don't hide confusion.** If something is unclear, stop and name what is unclear.
- **Present real alternatives.** If multiple interpretations exist, surface them
  rather than silently picking one. If a simpler approach exists, say so.
- **Push back when warranted** — but don't manufacture objections to look rigorous.
- **Never optimise for agreement.** Disagreement with reasoning is wanted; flattery
  is not.

A skill's instructions should read in this register: direct, tradeoff-aware, no
hedging and no cheerleading.

## Paths: environment variables, never literals

The environment exports these in every shell. Use them; never hardcode the
expansion, and never hardcode `/home/<user>`.

| variable | contents |
|---|---|
| `$WORKSPACE_PATH` | root holding scripts, tools, services, install, sdk |
| `$SCRIPTS_PATH` | shared scripts — invoke them from here |
| `$TOOLS_PATH` | shared tools — invoke them from here |
| `$SERVICES_PATH` / `$INSTALL_PATH` / `$SDK_PATH` | services, installers, SDKs |
| `$M2_HOME` | Maven local repository |
| `$GOPATH` · `$CARGO_HOME` · `$NPM_CONFIG_CACHE` · `$PIP_CACHE_DIR` | language caches |

Two rules that follow:

- **Dependency caches are shared and must not be bypassed.** A build that defaults
  to `~/.m2` while `$M2_HOME` is set re-downloads the world and diverges from every
  other build. Pass it through explicitly:
  `./mvnw -Dmaven.repo.local="$M2_HOME" <goals>`.
- **Skill-local before global.** Reference the skill's own code as
  `<SKILL_PATH>/scripts/<script>`. Use `$SCRIPTS_PATH` / `$TOOLS_PATH` only for
  utilities that genuinely live outside the skill and are shared across skills.

## `tools:` lists binaries, not agent capabilities

Every skill deploys to **five agents** (claude, codex, gemini, cursor, copilot).
So `tools:` must name real executables — `bash`, `git`, `jq`, `python3`, `ffmpeg`,
`gh`, `stow`. Never agent primitives like `write_to_file`, `view_file`, or
`read_file`: those exist under different names per agent, or not at all.

When a skill body needs the agent to read or write a file, say so in capability
terms — "with the host agent's file-write capability" — not by naming one agent's
tool.

## New tools belong in `$TOOLS_PATH`

When a skill generates a standalone tool (a TUI, a utility):

1. Create it at `$TOOLS_PATH/<tool-name>/`.
2. Add a guarded alias in `workspace/.aliases.sh`:
   ```bash
   if [ -d "$TOOLS_PATH/<tool-name>" ]; then
     alias <alias>="$TOOLS_PATH/<tool-name>/<tool-name>.sh"
   fi
   ```
3. **Document the alias in `workspace/.alias_descriptions`** — this is required,
   not optional.
4. Tell the user the path, and mention it can be added as a git submodule.

## Deployment reality

- `skills/` is a **git submodule** (`git@github.com:susamn/skills.git`). Committing
  a skill is two commits: inside the submodule, then the pointer bump in
  `~/dotfiles`.
- `do-stow.sh` symlinks every active skill into every agent's skills directory —
  there is no per-agent selection.
- Agent instruction files are **generated** from `skills/AGENTS-TEMPLATE.md` and
  overwritten on every run. Never edit `~/.claude/CLAUDE.md` directly; the change
  is silently lost. Edit the template.
- A skill is disabled by renaming its directory to `<name>.disabled`. Nothing reads
  the `Enabled` column in the skills table — update it by hand to match.
- A new skill must be registered in the `## Available skills` table of
  `AGENTS-TEMPLATE.md`, or it deploys unlisted.

## Config

`~/.config/skill-config/<skill-name>/skill.properties`, derived from `name` — never
a hand-typed path. Declare `config_dir` only when the skill has real persistent
state. Adding or changing a property requires explicit user approval first, with
the reason and the consuming script named.

## Reuse before writing

`$SCRIPTS_PATH` and `$TOOLS_PATH` already hold a substantial library (git helpers,
SSL and JWT debugging, secure resource generation, rclone config management, fuzzy
finders, system management). Check for an existing script or tool before adding a
new one, and prefer extending one over duplicating it.
