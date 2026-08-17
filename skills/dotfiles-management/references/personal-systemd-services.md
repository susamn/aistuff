# personal-services.target and scope semantics

What the target is, how membership works, and the silent failure modes around it.
Read when adding a personal service or timer, or diagnosing one that "enabled
fine" but never runs.

For *installing* services, see `service-installation.md`.

The failures in this area are all **silent** — systemd accepts the broken
configuration and runs nothing. None of them surface as an error.

---

## 1. What the target is

`personal-services.target` is a grouping unit meaning **"services this user
owns"**, as distinct from OS-level services. It carries no behaviour: nothing
depends on it running, it exists so `linux-system-manager` Section 5 can answer
"what background work is mine?"

It ships in `$SERVICES_PATH/personal-services.target` and is installed to
`/etc/systemd/system/` — system scope, `WantedBy=multi-user.target`.

The tool's **own** units (`sys-manager-cleanup`) deliberately do not claim it.
The target describes your services, not the tool's maintenance jobs.

---

## 2. Two managers, no shared namespace

systemd runs a **system** manager and a per-user manager, and they share nothing.
A unit name in one is unrelated to the same name in the other.

| | system scope | user scope |
|---|---|---|
| units in | `/etc/systemd/system/` | `~/.config/systemd/user/` |
| managed with | `sudo systemctl …` | `systemctl --user …` |
| valid `WantedBy` | `multi-user.target` | `default.target` |
| runs without a login session | yes | only with lingering enabled |

> **`multi-user.target` does not exist in the user manager.** A user unit
> declaring `WantedBy=multi-user.target` does **not** error — `systemctl --user
> enable` accepts it, writes the symlink, and the unit then never activates.
> That is quieter than a failure and much harder to spot.

**Never `sudo systemctl --user`.** That addresses *root's* user manager, not
yours: the unit is enabled for the wrong account and reports success.

Section 5 queries **both** managers and tags each result `[system]` or `[user]`,
so a unit in either shows up. In practice everything currently lives in system
scope, with `User=` set to the owning account.

---

## 3. Membership comes from the member, not the target

The target does not list what belongs to it. **Each unit** claims it, in its own
`[Install]` section:

```ini
[Install]
WantedBy=timers.target personal-services.target
```

`systemctl enable <unit>` reads that line and writes a symlink into
`personal-services.target.wants/` — **whether or not the target exists.** `enable`
does not validate that the wanted target resolves.

Consequence: a `.wants` directory full of links pointing at nothing is the normal
symptom of "units enabled before the target was installed". Installing the target
does not create the membership; it makes membership that was already declared
finally resolve.

---

## 4. How Section 5 discovers units

Two sources, merged and de-duplicated:

1. **Target dependencies** — `systemctl list-dependencies personal-services.target`
   in both managers. This is what is actually *enabled*.
2. **`$SERVICES_PATH` directory scan** — unit files that ship but may not be
   enabled yet, so a fresh checkout still lists what it has.

Three filters keep that listing honest:

- A **template** from the directory scan is suppressed when the target already
  contributed its live instances — otherwise every instance lists twice.
- A template's glob carries the unit suffix, so `rclone-sync@` does not match both
  `.service` and `.timer` instances.
- A **timer-driven `Type=oneshot` service is pulled out of the main list**,
  because it is inactive between runs by design and listing it beside its own
  timer reports a healthy sync as "stopped". The filter keys on `TriggeredBy`, so
  a oneshot whose timer is *disabled* stays in the main list — that one is a real
  problem.

`--failed-personal` and `--manage-personal` deliberately do **not** apply that
last filter: a failed oneshot is exactly what the failed view exists to surface,
and a manual run is still useful.

### Cross-referencing, not hiding

Pulling those services out entirely left "where is the service?" with no answer.
The status view now marks the timer and accounts for what it activates in a
second section:

```
● [system] rclone-sync@music-tracks.timer (active/running) ──activates──▶ (B)

Timer-activated units:
  (B) [system] rclone-sync@music-tracks.service
      ✗ last run FAILED (exit-code) at Mon 2026-08-17 16:00:00 EDT · next 16:30:00
```

The second section is what makes a *failed* oneshot visible in the ordinary
status view rather than only under `--failed-personal`. Nothing prints when no
timer-driven unit was filtered, so a listing without timers is unchanged.

Two implementation notes, both pinned by `test_regressions.py`:

- The marker generator increments a global. Reading it back through `$( )` runs
  the increment in a subshell, and every timer comes out as `(A)` pointing at one
  detail line. It must be called for its side effect.
- `systemctl show -p A -p B --value` returns values in **systemd's** property
  order, not the order of the arguments. Batching silently transposes the fields;
  query one property per call.

---

## 5. Diagnosing

```bash
# Does the target exist in the scope you think it does?
systemctl        show personal-services.target -p LoadState -p UnitFileState -p FragmentPath
systemctl --user show personal-services.target -p LoadState -p UnitFileState -p FragmentPath

# What does it actually group?
systemctl list-dependencies personal-services.target --plain --no-legend

# Dangling members: links in .wants that resolve to nothing
for f in /etc/systemd/system/personal-services.target.wants/*; do
  [ -e "$f" ] || echo "DANGLING: $f"
done

# A user unit wanting a target that cannot exist in user scope
grep -l 'WantedBy=.*multi-user.target' ~/.config/systemd/user/*.{service,timer} 2>/dev/null
```

| symptom | cause |
|---|---|
| `LoadState=not-found` after installing | no `daemon-reload` |
| target loaded, `UnitFileState=disabled` | never enabled; will not come up at boot |
| `.wants` populated but target not-found | units enabled before the target was installed |
| user unit enables fine but never runs | `WantedBy=multi-user.target` in user scope |
| unit invisible to Section 5 | wrong scope, or membership never declared in `[Install]` |
| oneshot shows "inactive/stopped" | normal **if** its timer is enabled; a real problem if not |

---

## 6. Lingering

`loginctl enable-linger <user>` starts the user manager at boot and keeps it
running after logout. Without it, user units only run while you are logged in.

It is **enabled** on this machine, but buys little in the current layout: the
rclone syncs and mounts are system units and never needed it. It matters only for
`mpd.service` and `battery-manager.timer`, and would matter a great deal if
anything moved to user scope.
