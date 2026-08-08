# Adding, swapping, or removing a problem

This is the part of the skill that's ongoing, not one-time setup. The user
will ask for this in two shapes:

- **"Add \<LeetCode URL\>"** — e.g. `https://leetcode.com/problems/3sum/`.
- **"Add a problem about \<description\>"** — e.g. "the one where you rotate
  an array in place" or "median of two sorted arrays".

Both produce the same thing: one JSON record written to
`problems/<slug>.json` via `lc.sh add`. There's no separate "swap" command —
adding a record whose `slug` already exists **replaces** it in place, so
swapping out a problem is just adding a different one to the same slug, or
adding a new slug and `lc.sh remove`-ing the old one.

## Steps

1. **Resolve identity.** From a URL, the slug is the last path segment
   (`/problems/<slug>/`). From a description, use your own knowledge to name
   the canonical LeetCode problem — if more than one problem plausibly
   matches, list the candidates and ask which one, don't guess silently.
2. **Check for a collision.** `lc.sh list` shows what's already stored. If
   the slug exists, say so and confirm the intent is to replace it before
   overwriting — this is the user's own local practice data, so no special
   permission gate beyond a quick confirmation that it's the problem they meant.
3. **Author the record** against `references/schema.md`. This is the
   judgment-heavy part — nothing here is scriptable:
   - `problem.statement_md` / `examples` / `constraints` — **your own
     paraphrase**, never copied verbatim from LeetCode's page (copyright).
     Keep `source_url` pointing at the original so the user can cross-check.
   - `intuition.summary_md` / `approach_md` — simple, not exhaustive. State
     the key insight in a sentence or two, then the approach in a short
     paragraph or a few bullets. Add `intuition.diagram` only when a small
     ASCII sketch or inline SVG actually clarifies the idea (index walks,
     pointer movement, a small tree/graph shape) — most problems don't need
     one, and a diagram that just restates the prose is worse than none.
   - `solutions.python` and `solutions.golang` — both required, working,
     idiomatic, and implementing the exact approach described in
     `intuition`. Mentally trace both against the examples before writing
     them down; a wrong solution defeats the whole point of the app.
4. **Validate before storing:**
   `<SKILL_PATH>/scripts/lc.sh validate <staging-file>`
5. **Store it:** `<SKILL_PATH>/scripts/lc.sh add <staging-file>` — writes to
   the data home (keyed by `slug`, from the JSON content, not the staging
   filename), rebuilds `manifest.json`, and prints the artifact path.
6. **Report** the slug, difficulty, and the dashboard link
   (`http://localhost:<mosaic-port>/mosaic/apps/leetcode-trainer/`) — mosaic
   picks up the new file automatically, no separate publish step.

## Removing a problem

`<SKILL_PATH>/scripts/lc.sh remove <slug>` deletes the stored record and
rebuilds the manifest. (The app's own delete button in the dashboard UI does
the same thing through mosaic's generic `DELETE /mosaic/apps/leetcode-trainer/data/{path}`
route.)

## Tracking progress against the starter checklist

`references/top-100.json` is the starter list this skill shipped with — see
its own `note` field for how it was assembled and why it isn't a live scrape.
`<SKILL_PATH>/scripts/lc.sh progress` diffs what's stored against that
checklist: one `missing` line per unauthored entry (id, slug, difficulty),
plus any `extra` slugs stored that aren't on the checklist (e.g. custom
additions). This is informational, not a constraint — add whatever the user
actually wants to practice; the checklist is a suggestion to work through,
not a whitelist.
