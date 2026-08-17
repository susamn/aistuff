# Personal systemd services: ownership and deployment flow

How `personal-services.target` and the units grouped under it are owned, deployed,
and discovered. Read when adding a personal service or timer, moving one between
scopes, or diagnosing why one is not showing up.

The failures in this area are all **silent** — systemd accepts the broken
configuration and simply never runs anything. None of them surface as an error.

---

## 1. Two scopes, two targets, one name

`personal-services.target` exists **twice**, once per systemd manager. They are
not duplicates: the system and user managers share no namespace, so these are
unrelated units that happen to share a name. They are distinguished by directory.

| | system scope | user scope |
|---|---|---|
| canonical file | `$TOOLS_PATH/linux-system-manager/services/personal-services.target` | `$TOOLS_PATH/linux-system-manager/services/user/personal-services.target` |
| `WantedBy=` | `multi-user.target` | `default.target` |
| installed to | `/etc/systemd/system/` | `~/.config/systemd/user/` |
| installed by | `sudo ./install.py` (copies, root-owned) | stow, from the dotfiles symlink |
| runs without login | yes | no |
| use for | daemons, boot-time work | anything needing `$HOME`, session D-Bus, per-user rclone config |

> **Never "de-duplicate" these by deleting one.** `multi-user.target` does not
> exist in the user manager. A user unit declaring `WantedBy=multi-user.target`
> does not error — `systemctl --user enable` accepts it, writes the symlink, and
> the unit then never activates. That is quieter than a failure and much harder
> to spot.

Choosing the scope is the only judgment call here: if the unit needs `$HOME`, a
login session, or a per-user credential, it is user scope. Otherwise system.

---

## 2. Ownership: linux-system-manager owns content, dotfiles owns placement

```
linux-system-manager/services/user/personal-services.target   ← canonical content
                    ▲
                    │  relative symlink, checked into dotfiles
dotfiles/.config/systemd/user/personal-services.target
                    ▲
                    │  symlink created by do-stow.sh
~/.config/systemd/user/personal-services.target               ← what systemd reads
```

- **linux-system-manager owns the file.** Edits go there. It is a submodule of
  dotfiles, so dotfiles still pins the version via the gitlink — "tracked by
  dotfiles" stays true, just transitively.
- **dotfiles owns only the placement** — an ~80-byte symlink recording *where* the
  unit should land. No content is duplicated, so nothing can drift.
- `install.py` **skips** any destination already symlinked to its own source and
  reports it as externally managed, so stow keeps ownership of user scope.

The system-scope target never touches `~/.config`. It is copied to
`/etc/systemd/system/` by `install.py` and is root-owned — outside stow's reach
entirely. A copy there is correct, not drift.

---

## 3. Deployment flow — and the step that is easy to miss

```
1. ./do-stow.sh
     places the unit FILE at ~/.config/systemd/user/ (symlink chain).
     systemd does not notice yet.

2. systemctl --user daemon-reload
     rescans the unit dir; target goes not-found → loaded.
     ← REQUIRED. Stow alone is never enough.

3. systemctl --user enable personal-services.target
     adds it to default.target.wants/ so it comes up at login.

4. membership — already declared by the units themselves (see below)

5. linux-system-manager Section 5 then discovers it:
     systemctl --user list-dependencies personal-services.target
```

## 4. Membership comes from the member, not the target

The target does not list what belongs to it. **Each unit** claims it, in its own
`[Install]` section:

```ini
# music-playlists.timer
[Install]
WantedBy=timers.target personal-services.target
```

`systemctl --user enable <unit>` reads that line and writes a symlink into
`personal-services.target.wants/` — **whether or not the target exists.** `enable`
does not validate that the wanted target resolves.

Consequence: a `.wants` directory full of links pointing into nothing is the
normal symptom of "units enabled before the target was deployed." Adding the
target file does not create the membership; it makes membership that was already
declared finally resolve.

---

## 5. Diagnosing

```bash
# Does the target exist in the scope you think it does?
systemctl --user show personal-services.target -p LoadState -p UnitFileState -p FragmentPath
systemctl        show personal-services.target -p LoadState -p UnitFileState -p FragmentPath

# What does it actually group?
systemctl --user list-dependencies personal-services.target --plain --no-legend

# Dangling members: links in .wants that resolve to nothing
for f in ~/.config/systemd/user/personal-services.target.wants/*; do
  [ -e "$f" ] || echo "DANGLING: $f"
done

# User units wanting a target that cannot exist in user scope
grep -l 'WantedBy=.*multi-user.target' ~/.config/systemd/user/*.{service,timer} 2>/dev/null
```

| symptom | cause |
|---|---|
| `LoadState=not-found` after stowing | no `daemon-reload` |
| target loaded, `UnitFileState=disabled` | never enabled; will not come up at login |
| `.wants` populated but target not-found | units enabled before the target was deployed |
| user unit enables fine but never runs | `WantedBy=multi-user.target` in user scope |
| unit invisible to Section 5 | wrong scope, or membership never declared in `[Install]` |

Note that linux-system-manager also lists **system**-scope units from its own
`services/` directory as a fallback, so those appear whether or not the system
target exists. User scope has no such fallback for units living in dotfiles —
`list-dependencies` against the target is their only discovery path.

---

## 6. Adding a new personal unit

1. Decide the scope (§1). Personal config units live in
   `dotfiles/.config/systemd/user/`; units that ship *with the tool* live in
   `linux-system-manager/services/` or `services/user/`.
2. Declare membership in the unit's own `[Install]`:
   `WantedBy=timers.target personal-services.target`.
3. `./do-stow.sh`, then `systemctl --user daemon-reload`.
4. `systemctl --user enable --now <unit>`.
5. Confirm with `systemctl --user list-dependencies personal-services.target`.

**Never `sudo systemctl --user`.** That addresses root's user manager, not yours —
the unit is enabled for the wrong account and reports success.
