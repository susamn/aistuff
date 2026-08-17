# Working on linux-system-manager itself

For *using* the tool see `service-installation.md`. This is for changing it —
adding a menu capability, supporting a new distro, or touching the installer.

## Read the tool's own guide first

**`$TOOLS_PATH/linux-system-manager/SKILL.md`** is the authoritative maintainer
guide and lives beside the code so it cannot drift from it. Read it on demand
before any change to the tool. It covers the architecture, how to replicate a
capability across distros, hook registration, the testing contract, and the
developer guardrails.

This file exists only so an agent working in dotfiles knows that guide is there —
the tool is an in-tree directory, not a registered skill, so nothing else points
at it.

## Orientation

| | |
|---|---|
| tool | `$TOOLS_PATH/linux-system-manager` (in-tree; history on `lsm-history/*` branches) |
| unit files + engines | `$SERVICES_PATH` — **not** inside the tool |
| menu definition | `distros/<id>/menu.json` |
| capability scripts | `distros/<id>/*.sh`, one copy per distro, usually byte-identical |
| orchestrator | `linux-system-manager.sh` — Python despite the extension |
| installer | `install.py` |
| tests | `test_sys_manager.py`, `test_menu_config.py`, `test_regressions.py` |
| CI | `~/dotfiles/.github/workflows/linux-system-manager.yml`, path-filtered |

## The traps that have actually bitten

Each of these shipped and cost real debugging time. They are pinned by tests in
`test_regressions.py`; read that file before assuming a behaviour is incidental.

- **`linux-system-manager.sh` is Python with a `.sh` extension.** `import` and
  `importlib` fail on it; tests must `compile()`/`exec()` the source.
- **`$SERVICES_PATH` is a stow symlink.** `find` does not descend into a symlinked
  start path — use `find -L`, or the directory scan silently returns nothing.
- **`sudo` strips `$SERVICES_PATH`** via `env_reset`, so every resolution needs a
  workspace-relative fallback. Package-manager hooks run with almost no
  environment at all.
- **`${name%.*}` on a template** yields `rclone-sync@`, whose glob matches both
  `.service` and `.timer` instances. Carry the suffix.
- **`sudo systemctl --user`** addresses *root's* user manager. Never use it; route
  state changes through the scope-aware wrapper.
- **A timer-driven `Type=oneshot` service is inactive between runs.** Listing it
  beside its timer reports healthy work as stopped — filter on `TriggeredBy`.
- **New profiles belong in the dotfiles repo**, not `~/.config`. A real file among
  stow symlinks works on one machine and is absent on the next.

## Contract for any change

1. Every capability script is duplicated per distro — change all of them, and keep
   them byte-identical unless the distro genuinely differs.
2. Add a `test_regressions.py` case for any bug you fix, and **verify it fails
   against the pre-fix code**. A regression test that passes on the broken version
   manufactures confidence.
3. Run the suite: `python3 -m unittest discover -s . -p 'test_*.py'`.
4. Shell lint: `shellcheck --severity=warning --exclude=SC2155 distros/*/*.sh $SERVICES_PATH/*.sh`.
5. Conventional Commits, **no AI branding or credit signatures** — the tool's
   `SKILL.md` §7 requires this and it overrides the usual default.
