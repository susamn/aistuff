---
name: pr-review
description: Review a GitHub pull request chunk-by-chunk with inference-driven findings (security, correctness, performance, etc.), persisted per review and browsable as a two-pane diff viewer on the mosaic dashboard. Use when asked to review a PR, generate a PR review, or check past PR review findings.
version: 3.0.0
kind: hybrid
triggers:
  - "review this PR"
  - "review pull request"
  - "review <github-url>"
  - "pr review for <url>"
  - "next chunk"
  - "set verdict for <review>"
intent: code-review
config_dir: ~/.config/skill-config/pr-review
created_at: 2026-05-30
updated_at: 2026-07-30
guardrails:
  - Do not post, comment, or push the review anywhere — findings are persisted locally only, browsable on the mosaic dashboard
  - Do not reproduce secrets/tokens/credentials found in a diff inside a finding's comment — reference that one is present, don't repeat it
  - Every finding must carry a concrete side+line the diff renderer can place — never a free-text line range or description
  - Read-only against the reviewed repo/PR — never push, comment, or merge on GitHub
resources:
  - <SKILL_PATH>/scripts/run.sh
  - <SKILL_PATH>/webapp/app.json
  - <SKILL_PATH>/references/schema.md
  - <SKILL_PATH>/references/review-criteria.md
tools:
  - bash
  - jq
  - gh
  - awk
---

# PR review

Hybrid skill: `scripts/run.sh` handles every deterministic step — fetching a
PR via `gh`, chunking its diff, validating and persisting findings, rolling
up counts into the dashboard manifest. The only judgment call — reading a
diff chunk and writing findings — is the agent's. Diff parsing (unified diff
→ line-numbered two-pane rows) is likewise deterministic and lives entirely
in `webapp/static/js/app.js`, never in the agent's output.

## Workflow

1. **Fetch.**
   ```
   <SKILL_PATH>/scripts/run.sh fetch <PR_URL> [-s <story_file>]
   ```
   Prints `review_id`, `scratch_dir` (holds `chunk_N.diff` files to read),
   `chunks` (count), and the `meta` path. First run onboards the skill into
   mosaic automatically (idempotent after).

2. **Review each chunk** (agent judgment). For chunk `N`:
   - Read `<scratch_dir>/chunk_N.diff` with the host agent's file-read capability.
   - Apply `references/review-criteria.md` — 9 categories, `must-fix` /
     `should-fix` / `suggestion` severities.
   - Anchor every finding to a concrete line per `references/schema.md` §
     Line anchoring (`side: RIGHT` + new-file line for an added/context
     line, `side: LEFT` + old-file line for a removed line) — read the
     chunk's `@@ -a,b +c,d @@` headers to count accurately, don't guess.
   - Write the findings JSON (shape: `references/schema.md` §
     "Agent-authored findings file") to a scratch path, then persist:
     ```
     <SKILL_PATH>/scripts/run.sh persist-chunk <review_id> <N> <findings_file>
     ```
     This validates the shape, merges in the raw diff, and rolls counts
     into `manifest.json`.

3. **Set the overall verdict** once every chunk is persisted:
   ```
   <SKILL_PATH>/scripts/run.sh set-verdict <review_id> <APPROVE|REQUEST_CHANGES|NEEDS_DISCUSSION>
   ```
   Refuses if any chunk is still unreviewed.

4. **Deliver.** Tell the user to start mosaic if it isn't already running
   (`$TOOLS_PATH/mosaic/quick-start.sh start`) then open
   `http://localhost:<mosaic-port>/mosaic/apps/pr-review/` (default port
   47500). There is no standalone file to hand over — the dashboard is the
   only deliverable. A review's detail page is paginated one chunk per page
   — each page lazily fetches only its own `chunk_N.json`, never the whole
   review at once, so a large PR never means loading its entire diff into
   one view. `fetch` writes every chunk's diff immediately (`reviewed:
   false`), so all pages are browsable right away; a page whose chunk
   hasn't been reviewed yet still shows the diff, just with no findings and
   a "not yet reviewed" banner.

5. **Read the digest — never open the raw artifact to summarize it**:
   ```
   <SKILL_PATH>/scripts/run.sh summary [review_id]
   ```
   No argument: one line per review (status, verdict, severity counts,
   repo#PR). With a `review_id`: one line per finding for that review. Both
   end with the artifact path.

## Testing without `gh`

`gh` is **not installed on this machine**. `fetch` accepts a fixture bypass
that skips every network call:
```
<SKILL_PATH>/scripts/run.sh fetch <any-github-pr-url> \
  --pr-json <SKILL_PATH>/fixtures/sample-pr.json --diff <SKILL_PATH>/fixtures/sample.diff
```
The URL is only used to derive `owner/repo/pr_number` and the `review_id`.

## Output

`summary` with no argument:
```
acme_widgets_42   reviewed   REQUEST_CHANGES   3 must-fix, 3 should-fix, 1 suggestions   acme/widgets#42 Add order lookup...
<artifact>: /home/user/.local/share/mosaic/data/pr-review/manifest.json
```

## Steady state, once onboarded to mosaic

`mosaic_onboarded=true` is already set (`~/.config/skill-config/pr-review/skill.properties`).
Routine invocations from here on — `fetch`, `persist-chunk`, `set-verdict` —
are data-producing runs only: they write to
`~/.local/share/mosaic/data/pr-review/`, and mosaic serves it automatically.
Modifying `webapp/app.json`, `webapp/static/`, the onboarding symlink, or
`scripts/run.sh`'s own logic is a distinct action, done only when the user
explicitly asks for it — never as a side effect of reviewing a PR.

## Notes

- Chunking is file-atomic, not a hard byte cap: the `MAX_CHUNK_SIZE`
  threshold (default 100KB, `awk` in `fetch`) is only checked between
  files, never inside one — a file's diff is never split across two
  chunks. A single file bigger than the threshold on its own becomes one
  oversized chunk rather than being split. Deliberate: the webapp's diff
  parser, renderer, and findings index all assume a chunk's files are
  self-contained, so pagination never needs cross-page stitching for one
  file. Tradeoff: one huge file can still overflow the agent's context on
  that chunk's review pass.
- Re-fetching the same PR replaces its scratch chunks and invalidates prior
  per-chunk reviews — same identity tradeoff `repo-reliability` makes: no
  history across re-reviews of one PR.
- This skill replaces the former `pr-review-ui` skill. That skill's
  single-chunk `file://` HTML export is retired in favor of the mosaic
  dashboard, which covers the same ground (diff + inline findings) across
  every review, not just the one just generated.
