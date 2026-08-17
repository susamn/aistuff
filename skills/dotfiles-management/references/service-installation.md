# Installing and managing services

How background services and timers get onto a machine, who owns what, and how to
add one. Read before installing on a new machine, adding a sync or service, or
working out why something is not running.

---

## 1. Who owns what

`linux-system-manager` is an **in-tree tool** at `$TOOLS_PATH/linux-system-manager`
— absorbed from its former standalone repo, no longer a submodule. Its history is
preserved on the `lsm-history/*` branches of this repo.

| thing | lives at | notes |
|---|---|---|
| the tool | `$TOOLS_PATH/linux-system-manager` | installs and manages; ships no policy |
| unit files + engines | `$SERVICES_PATH` (`workspace/services/`) | flat files, stowed to `~/workspace/services` |
| rclone profiles | `~/.config/rclone-sync-profiles/*.conf` | stowed from dotfiles |
| rclone backends | `~/.config/rclone/rclone.conf` | assembled by `rclc` from the GPG-encrypted `_secured` submodule |

The tool reads `$SERVICES_PATH`, falling back to a workspace-relative path —
necessary because `sudo` strips the variable via `env_reset`, and package-manager
hooks run with almost no environment at all.

---

## 2. Installing, from the menu

`asm` → **Section 5**:

| key | does | root |
|---|---|---|
| **54** | Show Installed / Available Services | no |
| **55** | Install or Update Services | yes, but only after you choose |

54 is a read-only survey. Every installable item is reported as:

| state | meaning |
|---|---|
| `✓ installed` | present and byte-identical to its source |
| `~ outdated` | present but differs from the source |
| `✗ not installed` | missing entirely |
| `○ installed, disabled` | unit exists but its timer is not enabled |

55 shows the same list, then accepts `1 3 5`, ranges `1-4`, `a` for all, `p` for
just the ones needing attention, or Enter to cancel.

Equivalent CLI:

```bash
./install.py --status        # survey only, no root
./install.py --interactive   # choose, then escalate
sudo ./install.py            # everything, non-interactive
```

**Installation is additive and idempotent.** Re-running never disables, removes,
or downgrades anything; items already current are skipped. The corollary is that
there is **no uninstall path** — deleting a profile leaves its `/etc` units and
drop-ins behind, and they must be removed by hand.

---

## 3. New machine, in order

```bash
git clone --recurse-submodules git@github.com:susamn/dotfiles.git ~/dotfiles
cd ~/dotfiles && ./do-stow.sh     # profiles → ~/.config, tool → ~/workspace
rclc                              # assemble ~/.config/rclone/rclone.conf
asm                               # → 54 to review, 55 to install
```

> **`rclc` before installing is not optional.** The installer validates every
> profile before activating it — `rclone listremotes` for the backend, `rclone lsf`
> for the remote path, plus a local-path check. Without `rclone.conf` every profile
> fails validation, nothing is enabled, and you get manual instructions instead of
> an error. It fails quietly, not loudly.

Two steps the installer deliberately leaves to you:

```bash
sudo systemctl enable --now sys-manager-cleanup.timer   # weekly backup prune — it deletes files
mpdc configure                                          # only on a machine that plays music
```

---

## 4. What installation actually does

| from | to |
|---|---|
| `$SERVICES_PATH/*.{service,timer,target}` | `/etc/systemd/system/` |
| `rclone-sync.sh`, `rclone-mount.sh`, `cleanup-backups.sh` | `/usr/local/bin/` |
| each profile in `~/.config/rclone-sync-profiles/` | `rclone-sync@<name>.timer.d/override.conf` (`OnCalendar=` from `SCHEDULE`), `<name>.service.d/user.conf` (`User=`), then enables the timer |
| distro hooks | pacman/apt package-operation triggers |

`@USER@` in `rclone-sync@.service` and `rclone-mount@.service` is substituted from
`SUDO_USER` at install time. The survey compares those **after** substitution —
the raw source never equals the installed file, so a naive diff would report them
permanently outdated.

---

## 5. Adding a sync

A sync needs a **profile and nothing else**. Do not write per-profile unit files:
the profile name becomes the systemd instance, so `rclone-sync@music-tracks.service`
runs `rclone-sync.sh music-tracks`.

```bash
vim ~/dotfiles/.config/rclone-sync-profiles/<name>.conf
cd ~/dotfiles && ./do-stow.sh
asm   # → 55, pick the new profile
```

Profile fields: `REMOTE`, `REMOTE_PATH`, `LOCAL_PATH`, `SYNC_TYPE` (`one` |
`bidirectional` | `mount`), `DIRECTION`, `SCHEDULE`, `USER`, `RCLONE_OPTS`.
`SYNC_TYPE="one"` is `rclone sync`, which **deletes at the destination** to match
the source.

## 6. Adding a non-rclone service

1. Put the unit files in `$SERVICES_PATH` as flat files.
2. Declare membership: `WantedBy=timers.target personal-services.target` — see
   `personal-systemd-services.md` for why the target matters and how membership
   actually works.
3. `./do-stow.sh`, then `asm` → 55.

Units belonging to the tool itself (e.g. `sys-manager-cleanup`) deliberately do
**not** claim `personal-services.target`: that target means "services this user
owns", not "everything the tool manages".
