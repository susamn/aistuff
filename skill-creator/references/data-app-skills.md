# Data-app skills (mosaic)

Orthogonal to `kind`. A `pipeline` (or `hybrid`) skill is **data-app-backed**
when its output should also be browsable as a live dashboard tile on
mosaic, not just written to a report file. A skill can be `kind: pipeline`
and data-app-backed at the same time — this is an add-on capability, never a
fourth `kind`.

Detection is structural, not a frontmatter flag: a data-app skill has a
`webapp/app.json` in its own directory. `scaffold.sh <name> --kind pipeline
--webapp` generates the skeleton; `skill-manager` audits it whenever the file
is present.

## Ask before writing

When scaffolding a `pipeline`/`hybrid` skill, ask the user: does this need a
live mosaic dashboard, or is a generated report/artifact enough? Don't infer
the answer from what another skill happens to do — another skill's current
shape reflects a point-in-time choice, not a verdict on which approach is
better. Only add `webapp/` when the user actually says yes.

## `webapp/` is a thin static view, not an app

**A data-app skill does not ship a server.** `webapp/static/` is plain HTML,
CSS, and client-side JS — mosaic is the only process serving anything.
"Data-app" describes a *shape* many pipeline skills already have: run a
script, produce data, optionally render something. Becoming data-app-backed
means that output lands in mosaic's data home and a few KB of static JS
renders it, not a rewrite into a full application.

## How to build one

1. **The generation script doesn't change its nature.** Whatever already
   computes the skill's output (a `pipeline` skill's `scripts/run.sh analyze`,
   or equivalent) keeps doing exactly that.
2. **Point its output at the centralized data home**:
   `~/.local/share/mosaic/data/<id>/`, creating it defensively
   (`mkdir -p`) — see the data-home contract below. For a skill that already
   writes a JSON artifact, this is usually a path change, not new logic.
3. **Add `webapp/app.json` + `webapp/static/index.html`** (`scaffold.sh
   --webapp` generates the skeleton). Good practice: keep `index.html` as an
   actual template file — static structure, separate from the data — rather
   than a script that builds up an HTML string each run; the page's own JS
   can `fetch("data/...")` against whatever step 2 wrote and render into that
   fixed structure. That's a recommendation, not a requirement — rendering is
   entirely the skill's own decision: fill a template, build DOM
   programmatically, reach for a small library, whatever fits. Mosaic has no
   opinion here and never will; it only serves files.
4. **Onboard itself** — `mkdir -p` + a symlink into mosaic's staging
   directory (below), not a manual step the user has to remember. Track it
   in `skill.properties`: see "Onboard
   itself, and track it" below.
5. Optional: a Playwright suite against the onboarded app — mosaic's own
   test suite is the pattern to follow (fixture app copied to a temp dir per
   run, onboard → assert → unboard).

## The `webapp/` contract

```
<skill>/webapp/
├── app.json           # required: {id, name, description, version, entry}
└── static/             # required: served at /mosaic/apps/<id>/...

    # everything below is one EXAMPLE layout, not a contract — see note below
    ├── index.html       # the template — structure only, no inline data
    ├── js/
    │   └── app.js        # fetch("data/...") + render into index.html
    ├── css/
    │   └── style.css
    └── assets/           # optional — icons, images, fonts; anything else static
```

`app.json` fields: `id` (kebab-case, **must equal the skill's directory
name**, no exceptions — the staging symlink is named from `id`, so the chain
skill-directory → `app.json.id` → staging symlink name must be the same
string throughout; `skill-manager` errors on a mismatch), `name`,
`description` (one line, shown on the dashboard tile), `version` (SemVer),
`entry` (relative path under `static/`, defaults `index.html`).

**Only `app.json` and `static/` themselves are required.** The `index.html` +
`js/` + `css/` breakdown inside `static/` is a suggestion, nothing more —
`entry` can point anywhere, `skill-manager` never looks inside `js/` or
`css/`, and no part of this doc takes away a data-app skill's full liberty
over both **how it renders** (template-filled, programmatic DOM, a library,
anything) **and how it organizes its own files**. It's offered only because
content is written once at authoring time (changes on a version bump) and
from then on only the data changes as scripts run — so a shared *default*
layout makes many skills' `webapp/` folders easier to navigate at a glance.
Ignore it entirely if a skill's rendering approach doesn't fit it.

No `data/` directory here, and never commit one with real files — see below.

## The data-home contract (this is the part that's easy to get wrong)

The skill's own generation script writes data directly to:

```
~/.local/share/mosaic/data/<id>/
```

not into `webapp/data/`. This is mosaic's centralized data root — one path
every app writes under, so the whole tree can be backed up with a single
`rclone sync ~/.local/share/mosaic/data <remote>`, regardless of where each
skill's source lives on disk.

Hard requirements for the generation script:

- **Create the directory defensively** (`mkdir -p ~/.local/share/mosaic/data/<id>`)
  before writing. Mosaic itself may not be installed yet on this machine —
  the skill must not depend on mosaic, or on `onboard.sh` having run, to
  produce its own data.
- **Write a `manifest.json`** listing available datasets — `{id,
  generated_at, schema_version, tier: "hot"|"cold"}` per entry. This is what
  the app's own frontend JS reads for pagination, archival tiers, and
  graying out data an older/newer app version can't read (compare each
  entry's `schema_version` against what the currently-loaded `webapp/`
  supports). Mosaic itself never interprets this file — it's serving it as a
  plain static file, the app-side JS owns all meaning.
- Sub-paths under `data/` beyond the manifest are **entirely up to the
  app** — one flat file or many nested paths. Mosaic imposes no structure
  beyond the `data/` prefix.

## Onboarding — a fixed staging directory, never mosaic's install path

**A data-app skill never needs to know where mosaic is installed.** Mosaic
discovers apps from one fixed, install-independent staging directory — a
sibling of the data home above, under the same root:

```
~/.local/share/mosaic/
├── apps/            # staging symlinks only — never rclone this
│   └── <id> -> <skill-path>/webapp
└── data/             # the actual data — rclone this, and only this
    └── <id>/
```

`apps/<id>` and `data/<id>` are always the same string, not just by
convention — both come from `app.json.id`, and `skill-manager` errors if it
ever drifts from the skill's own directory name (see the `webapp/` contract
above).

`apps/` holds only symlinks pointing back at wherever each skill's `webapp/`
actually lives on *this* machine — syncing it to another machine would just
produce broken links there, which is why it's excluded from the `rclone`
command above on purpose. A second machine wanting the same dashboard needs
its own local `apps/` staging (each skill onboards itself there too, same as
the first time) but can pull the identical `data/` tree from the same rclone
remote.

Onboarding is two filesystem operations against the staging path, nothing
else — no `$TOOLS_PATH`, no reference to mosaic's own script tree:

```bash
mkdir -p ~/.local/share/mosaic/apps
ln -sfn <skill-path>/webapp ~/.local/share/mosaic/apps/<id>
```

`mkdir -p` is idempotent — the first app to run it creates
`~/.local/share/mosaic/apps` (and `~/.local/share/mosaic` itself if this is a
fresh machine); every run after that is a no-op against what's already
there. Mosaic does the same defensively on its own startup, so an empty or
missing staging directory is never an error on either side.

`do-stow.sh`/`do-unstow.sh` symlink skills into agents' skill directories —
a completely different concern, and never involved here either. **Never
mention do-stow/do-unstow, or mosaic's own install path, in a data-app
skill's onboarding instructions**; `skill-manager`'s audit treats the former
as an error, and the latter reintroduces exactly the install-path coupling
this contract exists to avoid — a skill's onboarding step should reference
only the fixed staging path above, nothing about where mosaic itself lives.

Mosaic's own repo ships `onboard.sh` / `unboard.sh` scripts that wrap the
same two operations with validation (kebab-case `id`, valid JSON) and
clearer errors, plus a data-migration fallback for `webapp/data` that
already has local content (the case where a skill ran before ever being
redirected to the centralized data home — see below). They're a convenience
for interactive use and for migrating an existing skill's leftover local
data, **not** something a compliant skill's own workflow depends on —
depending on them means depending on mosaic's install location existing at
some particular path, which the two-line version above avoids entirely.

### Onboard itself, and track it

Once `webapp/` is finalized, **the skill onboards itself** — run the two
commands above, don't leave this as a manual step the user has to remember.
Track whether it's already happened in the skill's own config, same as any
persistent skill state:

```
~/.config/skill-config/<skill-name>/skill.properties
mosaic_onboarded=true   # set once this skill's webapp/ has been symlinked into mosaic's staging dir
```

Workflow: check the property first; if it's not `true`, onboard, then set
it. If it's already `true`, skip — re-running is harmless (`ln -sfn`
overwrites cleanly), but there's no need to. This is a normal
`skill.properties` addition, so the usual rule still applies: confirm the
new key with the user before writing it, and comment the line so a future
read of the file explains itself (see `references/house-conventions.md` §
Config).

## What mosaic guarantees, and doesn't

Two generic routes only — `GET /mosaic/apps/<id>/{path}` (static passthrough)
and `GET /mosaic/apps/<id>/data/{path}` (data passthrough), both refusing to
resolve outside the app's own directory. **No per-app backend code, ever** —
anything dynamic is the app's own client-side JS reading its `data/` files.
Don't propose adding server-side logic to mosaic for a specific app; if the
generic contract can't express what's needed, that's a mosaic design
conversation, not a workaround in one app.

Mosaic itself is the reference implementation of all of the above, including
the Playwright pattern named in "How to build one."
