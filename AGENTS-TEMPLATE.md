# Global Guidelines 

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

**Don't assume. Don't hide confusion. Surface tradeoffs that are real. Don't try to make me happy, if you think otherwise, elaborate.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.
- Ask questions, while not being stubborn or obnoxious trying to proof your point or raise a point just for the sake of it.

# Agent Context

This file gives you context about the user's environment and available tooling.
It is managed by the user's dotfiles repo — you do not need to be inside that repo
to use the skills and scripts described here.

---

## Loading this file
Always load and retain global skills from {{INSTRUCTION_PATH}} for every session.

When inside a repository:
- treat {{INSTRUCTION_PATH}} as the base instruction set.
- treat repo specific agent file as additional guidance.
- do not replace global skills with repo-local instructions unless there is explicit conflict.

## Environment variables

These are exported in every shell session and must be used when referencing scripts
or tools — never hardcode absolute paths.

| Variable            | Path                                  | Notes                                                                         |
| ------------------- | ------------------------------------- | ----------------------------------------------------------------------------- |
| `$WORKSPACE_PATH`   | `~/workspace`                         | The folder that contains codebase, scripts, tools, services, install, and sdk |
| `$SCRIPTS_PATH`     | `~/workspace/scripts`                 | Contains scripts and scripts must be invoked using this path                  |
| `$TOOLS_PATH`       | `~/workspace/tools`                   | Contains tools and tools must be invoked using this path                      |
| `$SERVICES_PATH`    | `~/workspace/services`                | Contains services                                                             |
| `$INSTALL_PATH`     | `~/workspace/install`                 | Contains install scripts                                                      |
| `$SDK_PATH`         | `~/workspace/sdk`                     | Contains sdk                                                                  |
| `$M2_HOME`          | `~/workspace/sdk/repositories/m2`     | Contains maven cache                                                          |
| `$CARGO_HOME`       | `~/workspace/sdk/repositories/cargo`  | Contains cargo cache                                                          |
| `$NPM_CONFIG_CACHE` | `~/workspace/sdk/repositories/npm`    | Contains npm cache                                                            |
| `$PIP_CACHE_DIR`    | `~/workspace/sdk/repositories/pip`    | Contains pip cache                                                            |
| `$GOPATH`           | `~/workspace/sdk/repositories/gopath` | Contains go cache                                                             |

---

## Available skills

Skills are modular packages. Skill-specific scripts are stored within the skill folder (e.g., `skills/name/scripts/`) to ensure encapsulation and minimize security blast radius. Only enable scripts that are `Enabled` in the following table.

**Rule for accessing skill scripts:** All skill resources are located at `{{AGENT_SKILLS_PATH}}/<skill-name>/`. When a skill references a script like `<SKILL_PATH>/scripts/run.sh` or `./scripts/run.sh` or `scripts/run.sh`, you must execute it using its absolute path: `{{AGENT_SKILLS_PATH}}/<skill-name>/scripts/run.sh`.

| Skill                           | Intent      | Trigger examples                                                                                                       | Created | Updated | Enabled |
| ------------------------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------- | ------- | ------- | ------- |
| `pr-review`                     | code-review | "review this PR", "generate PR review prompt"                                                                          | 2026-05-30 | 2026-05-30 | Yes     |
| `openapi-schema-creator`        | api-design  | "create an OpenAPI schema", "design an API"                                                                            | 2026-05-30 | 2026-05-30 | Yes     |
| `skill-creator`                 | meta        | "create a new skill", "add a skill"                                                                                    | 2026-05-30 | 2026-05-30 | Yes     |
| `music-tagger`                  | media       | "update media tags", "batch tag songs"                                                                                 | 2026-05-30 | 2026-05-30 | Yes     |
| `obsidian`                      | notes       | "work with obsidian", "notes in obsidian"                                                                              | 2026-05-30 | 2026-05-30 | Yes     |
| `model-usage`                   | metrics     | "model usage", "cost data"                                                                                             | 2026-05-30 | 2026-05-30 | No      |
| `skill-manifestor`              | meta-skill  | "manifest a new skill hierarchy", "use skill-manifestor"                                                               | 2026-05-30 | 2026-05-30 | No      |
| `dotfiles-management`           | system      | "manage dotfiles", "add a skill"                                                                                       | 2026-05-30 | 2026-05-30 | Yes     |
| `java-generic`                  | execution   | "work on java project", "create java class"                                                                            | 2026-05-30 | 2026-05-30 | Yes     |
| `python-generic`                | execution   | "work on python project", "create python script"                                                                       | 2026-05-30 | 2026-05-30 | Yes     |
| `java-spring-framework-generic` | execution   | "work on java spring framework project", "create java spring framework class"                                          | 2026-05-30 | 2026-05-30 | Yes     |
| `java-vulnerability-manager`    | execution   | "fix vulnerabilities in java project", "run cve scan", "fix transitive dependency", "owasp dependency check"           | 2026-05-30 | 2026-05-30 | Yes     |
| `ai-lsp-query`                  | execution   | "find all references to", "who calls this function", "what type is this", "lsp query"                                  | 2026-05-30 | 2026-05-30 | Yes     |
| `skill-manager`                | system      | "audit my skills", "check skill compliance", "manage skills"                                                           | 2026-05-30 | 2026-05-30 | Yes     |
| global-applications-guidelines  | execution   | "want to build a new app", "lets work on a project", "lets create a new app"                                          | 2026-05-30 | 2026-05-30 | Yes     |
| brainstorming                   | planning    | "lets brainstorm on an idea", "lets plan an idea", "lets plan a project", "lets think about an idea", "I have an idea" | 2026-05-30 | 2026-05-30 | Yes     |

More skills will appear here as they are added to the dotfiles.

### Skill Selection & Loading
When the user asks to "load skills", "select a skill", or "show skills":
1. **Fetch**: Use `list_directory` on `{{AGENT_SKILLS_PATH}}` to identify all available skill folders.
2. **Present**: Display a numbered, paginated list (max 10 items per page) of skills found in the `Available skills` table above. Include the skill name and its one-line description.
3. **Activate**: When the user selects a skill by number or name, call the `activate_skill` tool.
4. **Confirm**: Confirm to the user that the skill is loaded and ready.

### Skill Loading Scenarios
To ensure the correct specialized tools and guardrails are applied, agents **MUST** automatically load and utilize the following skills under these specific scenarios:
- **Dotfiles Management:** When working inside the `~/dotfiles/` directory, load the `dotfiles-management` skill.
- **Skill Management:** When tasked with auditing, checking compliance, or managing agent skills, load the `skill-manager` skill.
- **Skill Creation:** When tasked with creating a new skill or expanding the skill framework, load the `skill-creator` skill.
- **Openapi Schema Creation:** When tasked with creating an OpenAPI schema, load the `openapi-schema-creator` skill.
- **Obsidian:** When tasked with working with obsidian, load the `obsidian` skill.
- **Language/Framework Tasks:** When starting work on a specific language or framework (e.g., Java or Python), check the `{{AGENT_SKILLS_PATH}}/` directory and load the relevant generic skill (e.g., `java-generic`, `python-generic`) to establish baseline guardrails. Then load other relevant skills if any.
- **Music Tasks:** When tasked with working with music (e.g. updating media tags), load the `music-tagger` skill.
- **Semantic Code Intelligence:** When tasked with deep semantic codebase queries (e.g., finding references, determining type signatures, extracting call hierarchies), load the `ai-lsp-query` skill to gain precise, IDE-level codebase context.

While loading skills, if there is any conflict between the skills, notify user and ask for clarification.

---

## Available scripts

Located at `$SCRIPTS_PATH`. Invoke with `bash "$SCRIPTS_PATH/<script>"`.

| Script | Alias | What it does |
|---|---|---|
| `git-stash-manager.sh` | `gsh` | Interactive git stash manager |
| `git-hard-reset.sh` | `ghr` | Hard reset current branch with safety prompts |
| `gch.sh` | `gch` | Interactive git checkout across branches |
| `gitb.sh` | `gitb` | Git branch utilities |
| `arch-system-manager.sh` | `asm` | Arch Linux system manager (update, boot safety, timeline) |
| `ssl-debugger.sh` | — | Debug SSL/TLS certificates |
| `jwtd.sh` | `jwtd` | Decode and inspect JWT tokens |
| `generate-ssh-keys.sh` | `gsk` | Generate SSH key pairs |
| `ytd.sh` | `ytd` | Download YouTube videos/audio via yt-dlp |
| `video-merger.sh` | — | Merge video files |
| `als.sh` | `als` | Search/browse shell aliases interactively |
| `ffo.sh` | `ff` | Fuzzy file finder (fd + fzf) |
| `uff.sh` | `uff` | Fuzzy file finder with preview |
| `pkg-listing.sh` | `pkgs` | List installed packages |
| `cht.sh` | `cht` | Cheatsheet lookup |

## Available tools

Located at `$TOOLS_PATH`. Each tool has a `quick-start.sh` entry point.

| Tool | Alias | What it does |
|---|---|---|
| `media-trimmer/` | `mt` | Web UI for trimming audio/video files |
| `api-testing-tool/` | `att` | API testing tool |
| `performance-manager/` | `pfm` | System performance monitor |
| `helpful-tools-v2/` | `ht2` | Collection of helpful utilities |
| `file-explorer/` | — | Remote file explorer (SFTP) |
