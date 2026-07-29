---
name: tui-creator
description: Guide and engine specification for building index-based tree/subtree Terminal User Interfaces (TUIs). Use when creating indexed menu tools (e.g. 11, 1a, 23), subtree drill-downs, theme selection with color swatches, or task-executing terminal interfaces.
version: 3.0.0
kind: hybrid
triggers:
  - "create indexed TUI"
  - "build TUI script"
  - "create a TUI"
  - "build indexed menu interface"
  - "create subtree menu TUI"
  - "design indexed TUI"
intent: system
created_at: 2026-07-28
updated_at: 2026-07-29
guardrails:
  - ALWAYS use the canonical template engine at <SKILL_PATH>/assets/tui_template.py. Do NOT write menu loops or ANSI rendering code from scratch.
  - ALWAYS place newly created TUI tools inside $TOOLS_PATH/<tui-name>/.
  - ALWAYS bind the main TUI runner script to a shell alias in workspace/.aliases.sh and document it in workspace/.alias_descriptions.
  - ALWAYS inform the user of the tool's path in $TOOLS_PATH/ and notify them that it can optionally be added as a git submodule to their dotfiles repo.
  - Do not hardcode absolute paths; use $SCRIPTS_PATH, $TOOLS_PATH, or $WORKSPACE_PATH environment variables.
  - Do not display monolithic single-screen menus when total options exceed clamp_threshold; clamp into top-level parent categories and subtrees.
  - Pass terminal input/output (stdin/stdout/stderr) cleanly when executing sub-tasks.
  - Always support clean exit (0) and back navigation (b or 0) in submenus.
resources:
  - <SKILL_PATH>/assets/tui_template.py
  - <SKILL_PATH>/scripts/scaffold_tui.py
  - <SKILL_PATH>/references/ANIMATIONS_AND_ICONS.md
  - <SKILL_PATH>/references/MENU_SCHEMA.json
tools:
  - bash
---

# TUI Creator

## Defaults

- `theme` — `obsidian` (also `dracula`, `nord`, `cyberpunk`, `emerald`)
- `clamp_threshold` — `10`; above this many options on one screen, clamp into
  parent categories and subtrees
- `language` — `python` (also `bash`)

Confirm these with the user at the start rather than assuming.

## Output

`scripts/scaffold_tui.py` writes the spec and prints one line to stdout with the
item count and the generated path; errors go to stderr. That path is the handle —
read the generated file only if something needs checking.

```
✓ Generated TUI spec with 12 items at: /path/to/tool/menu.json
```

---

## TUI Deployment & Shell Alias Standard

Whenever creating a new Indexed TUI tool:

1. **Target Directory**:
   Create a dedicated directory under `$TOOLS_PATH/<tui-name>/` (e.g. `$TOOLS_PATH/docker-manager/`).

2. **Notify User & Submodule Option**:
   Explicitly inform the user upon creation:
   > *"Created new TUI at `$TOOLS_PATH/<tui-name>/`. If desired, you can add this folder as a Git submodule to your dotfiles repository."*

3. **Shell Alias Registration**:
   Add a conditional alias block in `workspace/.aliases.sh`:
   ```bash
   if [ -d "$TOOLS_PATH/<tui-name>" ]; then
     alias <alias_name>="$TOOLS_PATH/<tui-name>/<tui-name>.sh"
   fi
   ```
   And document the alias in `workspace/.alias_descriptions`:
   ```
   <alias_name>=<Short description of the TUI tool>
   ```

---

## Canonical Engine Foundation

Agents **MUST NOT** write custom menu rendering or input loops from scratch. Always use the canonical Python engine:
* **Canonical Runner**: [`<SKILL_PATH>/assets/tui_template.py`](file://<SKILL_PATH>/assets/tui_template.py)
* **Auto-Discovery Scaffolder**: [`<SKILL_PATH>/scripts/scaffold_tui.py`](file://<SKILL_PATH>/scripts/scaffold_tui.py)
* **Spec Schema**: [`<SKILL_PATH>/references/MENU_SCHEMA.json`](file://<SKILL_PATH>/references/MENU_SCHEMA.json)
* **Animations & Icons Guide**: [`<SKILL_PATH>/references/ANIMATIONS_AND_ICONS.md`](file://<SKILL_PATH>/references/ANIMATIONS_AND_ICONS.md)

---

## Engine Features & Capabilities

1. **Indexed Shortcuts (`11`, `1a`, `21`)**: Direct keyboard shortcuts mapping section + item key.
2. **Subtree Clamping**: Automatically clamps to parent categories when overall options exceed `clamp_threshold`.
3. **Single-Key Raw Mode**: Instant menu selection without needing `ENTER`.
4. **Dry-Run Inspection Mode (`d`)**: Pressing `d` toggles dry-run mode to inspect commands/directories before running.
5. **Organic `fzf` List Filtering**: Setting `"use_fzf": true` pipes list outputs into theme-matched `fzf` (`--border=rounded`, dynamic ANSI palette).
6. **Integrated Output Paging**: Automatically pipes long command outputs (>25 lines) into `bat` or `less -R`.
7. **Semantic Color Engine**: 5 Bootstrap-style roles (`Primary`, `Success`, `Info`, `Warning`, `Danger`) across 5 dark themes. Theme selector (`t`) renders live role swatches.
8. **Dependency Auditing**: Auto-checks presence of `fzf`, `rg`, `fd`, `bat`, `jq` and displays install recommendations.

---

## Input Methods for Creating TUIs

Users can request TUIs via 3 simple methods:

* **Method 1: Conversational / Scratchpad**
  Describe tasks in chat text or bullet points. The agent generates the `menu.json` structure.
* **Method 2: Declarative Spec File (`menu.json`)**
  Provide a JSON file conforming to [`MENU_SCHEMA.json`](file://<SKILL_PATH>/references/MENU_SCHEMA.json) and run `python3 tui_template.py menu.json`.
* **Method 3: Directory Auto-Discovery**
  Point the agent to a folder of scripts and run:
  ```bash
  python3 <SKILL_PATH>/scripts/scaffold_tui.py --dir $SCRIPTS_PATH --out menu.json
  ```
