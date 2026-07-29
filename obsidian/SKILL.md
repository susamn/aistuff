---
name: obsidian
description: Work with Obsidian vaults (plain Markdown notes on disk) and automate via obsidian-cli. Use when reading, creating, searching, or refactoring notes in an Obsidian vault.
version: 2.0.0
kind: guidance
triggers:
  - "work with obsidian"
  - "notes in obsidian"
intent: notes
guardrails:
  - Do not edit `.obsidian/` workspace or plugin settings from scripts.
  - Prefer `obsidian-cli move` over `mv` — it rewrites wikilinks across the vault.
tools:
  - bash
  - obsidian-cli
created_at: 2026-05-30
updated_at: 2026-07-29
---

# Obsidian

An Obsidian vault is a normal folder on disk. Notes are plain Markdown and can be
edited with any editor — reach for direct file edits when that is simpler, and
Obsidian will pick the change up.

`obsidian-cli` is **not currently installed on this machine**; the command
recipes below assume it is present. Enable it via Settings → General → Command
line interface.

## Vault layout

- `*.md` — notes, plain Markdown
- `.obsidian/` — workspace and plugin settings; leave alone
- `*.canvas` — canvases, JSON
- attachments — whatever folder is configured in Obsidian settings

## Finding the active vault

Obsidian tracks vaults in a config file, which is the source of truth:

- **Linux/WSL2** — `~/.config/obsidian/obsidian.json`
- **macOS** — `~/Library/Application Support/obsidian/obsidian.json`

The vault name is normally the folder name. To resolve it quickly, use
`obsidian-cli print-default --path-only` if a default is set; otherwise read the
config file and take the entry with `"open": true`.

Set the default once with `obsidian-cli set-default "<vault-folder-name>"` —
this is obsidian-cli's own mechanism, so the skill keeps no separate config.

## Commands

Search:

```bash
obsidian-cli search "query"          # note names
obsidian-cli search-content "query"  # inside notes, with snippets and line numbers
```

Create, move, delete:

```bash
obsidian-cli create "Folder/New note" --content "..." --open
obsidian-cli move "old/path/note" "new/path/note"
obsidian-cli delete "path/note"
```

`move` updates `[[wikilinks]]` and Markdown links across the vault — that is the
main reason to prefer it over `mv`.

## Constraints

- `create` and `move` need the Obsidian URI handler, which requires the desktop
  app running. On Linux/WSL2 without a display, edit files directly or use
  `obsidian-web`.
- Avoid creating notes under dot-folders via URI; Obsidian may refuse.
