---
name: skill-creator
description: Guide for creating effective skills that extend different agents' capabilities. Use when creating new skills or updating existing skills with specialized knowledge, workflows, or tool integrations.
version: 1.1.0
triggers:
  - "create a new skill"
  - "add a skill"
intent: meta
config_dir: ~/.config/skill-config/skill-creator
created_at: 2026-05-30
updated_at: 2026-06-18
---

# Skill Creator

## Skill Configuration

This skill uses `~/.config/skill-config/skill-creator/skill.properties` for templates and standard fields.

Before creating a skill, check if `~/.config/skill-config/skill-creator/` and `skill.properties` exist. If not, create them and notify the user: "Creating configuration directory and default properties file for skill-creator to store your skill templates and default author information." Any new property added or saved back to this file MUST be approved by the user beforehand. When loading the file, explicitly report the loaded entries to the user.

### Common Properties
- `default_author`: Name to use in `created_at` or `updated_at` (optional).
- `auto_stow_after_creation`: `true`/`false`.

Before creating a skill, check `~/.config/skill-config/skill-creator/skill.properties` for standard templates.

Guide for creating effective skills that extend different agents' capabilities.

## About Skills

Skills are modular, self-contained packages that extend different agents' capabilities by providing specialized knowledge, workflows, and tools. Think of them as "onboarding guides" for specific domains.

### What Skills Provide

1. **Specialized workflows** - Multi-step procedures for specific domains
2. **Tool integrations** - Instructions for working with specific file formats or APIs
3. **Domain expertise** - Company-specific knowledge, schemas, business logic
4. **Bundled resources** - Scripts, references, and assets for complex tasks

## Core Principles

### Concise is Key

The context window is a public good. Only add context the agent doesn't already have.

**Default assumption: Agents is already very smart.** Challenge each piece of information: "Does the agent really need this explanation?"

Prefer concise examples over verbose explanations.

### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/      - Skill-specific scripts (preferred)
    ├── references/   - Documentation
    └── assets/       - Templates, images
```

## SKILL.md Components

### Frontmatter (YAML)

```yaml
---
name: skill-name
description: What the skill does. Use when [activation trigger].
version: 1.0.0
triggers:
  - "natural language phrase that activates this skill"
intent: code-review | git | system | debug | media | ...
config_dir: ~/.config/skill-config/skill-name
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
guardrails:
  - Do not X
resources:
  - ./scripts/script-name.sh  # Relative to skill directory
  - $TOOLS_PATH/tool-name     # For global tools
tools:
  - bash
---
```

The `description` is the primary triggering mechanism. Always include `created_at` and `updated_at` timestamps in ISO 8601 format (YYYY-MM-DD). The `config_dir` field specifies where the skill's persistent configuration and state are stored.

Store skill-specific logic in `./scripts/` within the skill folder. Only use `$SCRIPTS_PATH` for truly global, shared utilities. This minimizes the "security blast radius" and makes skills portable.

### Body (Markdown)

Instructions and guidance. Use `<SKILL_PATH>` as a placeholder if you need to reference the absolute path to the skill's directory during execution.

## Skill Configuration

Skills MUST support persistent configuration via a `skill.properties` file located in their `config_dir`. The skill scripts may use these properties in it. The skills should decide when to add a useful property back to the properties file, but they MUST explicitly consult with the user and obtain approval BEFORE saving or adding any new properties to the `skill.properties` file. When requesting approval, give a clear indication why we need to add this property and which script will use it. While saving an approved property, give proper comments per key=value mapping, so that the agents can understand what is this property.

### Configuration Standard
- **Location**: `~/.config/skill-config/<skill-name>/skill.properties`
- **Format**: `key=value` (one per line)
- **Loading**: The skill MUST read this file upon activation to load defaults, environment settings (e.g., `git_provider=github`), or previously taken actions to avoid redundancy. Upon reading, the skill MUST explicitly print/notify the user which properties have been loaded from the file.
- **Initialization**: If the config directory or `skill.properties` file does not exist, the skill MUST automatically create them, informing the user with a clear message explaining why the folder and file are being created and what they are used for.

### Example Usage in Body
"Check if `~/.config/skill-config/<skill-name>/` and `skill.properties` exist. If not, create them and output a clear message to the user: 'Creating configuration directory and default properties file for <skill-name> to store persistent preferences and state.' Then read the file to determine the preferred `git_provider`..."

## Bundled Resources

### Scripts (`./scripts/`)

Executable code for tasks requiring deterministic reliability. Store these inside the skill directory for better security and portability.

### References (`references/`)

Documentation loaded as needed into context.

### Assets (`assets/`)

Files used in output (templates, images, fonts).

## Progressive Disclosure

Skills use three-level loading:

1. **Metadata** - Always in context (~100 words)
2. **SKILL.md body** - When skill triggers (<5k words)
3. **Bundled resources** - As needed

Keep SKILL.md under 500 lines. Split content when approaching this limit.

## Skill Creation Process

1. **Understand** - Gather concrete usage examples
2. **Plan** - Identify reusable scripts, references, assets
3. **Initialize** - `mkdir -p ~/dotfiles/skills/<name>`
4. **Edit** - Write `~/dotfiles/skills/<name>/SKILL.md` referencing scripts via `$SCRIPTS_PATH` or `$TOOLS_PATH`.
5. **Register** - Add the new skill to the `## Available skills` table in `~/dotfiles/templates/AGENTS.md.template`.
6. **Deploy** - Run `bash ~/dotfiles/do-stow.sh` — this generates agent-specific instruction files from the template and symlinks the skill into every agent's skills directory.
7. **Commit** - `git add skills/<name>/ templates/AGENTS.md.template && git commit -m "skills: add <name>"`
8. **Iterate** - Improve based on real usage

## What NOT to Include

- README.md
- INSTALLATION_GUIDE.md
- CHANGELOG.md
- User-facing documentation

Skills are for AI agents, not humans. Only include what the agent needs to do the job.