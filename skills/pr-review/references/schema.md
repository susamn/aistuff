# Data schema

All persisted JSON carries `"schema": 1`. A consumer that reads an unexpected
version exits `2` rather than misinterpreting the file.

## Enums

- `category`: `correctness` `code-quality` `security` `performance`
  `resource-leak` `concurrency` `test-coverage` `maintainability` `dependency`
- `severity`: `must-fix` `should-fix` `suggestion`
- `side`: `LEFT` (old file) `RIGHT` (new file) — GitHub's own PR-comment anchor
  model, reused because the agent already reasons in these terms when reading
  a diff
- `verdict`: `APPROVE` `REQUEST_CHANGES` `NEEDS_DISCUSSION`
- `status`: `pending_review` → `in_progress` → `awaiting_verdict` → `reviewed`

## Line anchoring

A finding anchors to one physical line in one file version, not a range and
not a loose description:

- `side: "RIGHT"`, `line: <new-file line number>` — for an added or
  unchanged (context) line. This is the common case.
- `side: "LEFT"`, `line: <old-file line number>` — for a removed line, which
  has no line number on the new side.

The two-pane diff renderer places the comment row directly under that line
on that side. Diff parsing (unified diff → line-numbered rows) is
deterministic and lives entirely in `webapp/static/js/app.js`, never in the
agent's output — the agent only has to point at a line it can already see in
the chunk it read.

## `manifest.json` — `~/.local/share/mosaic/data/pr-review/manifest.json`

One entry per review. The webapp's list view reads only this file — no
per-review fetch needed to render the list.

```json
{
  "schema": 1,
  "datasets": [
    {
      "id": "owner_repo_123",
      "generated_at": "2026-07-30T12:00:00Z",
      "schema_version": 1,
      "tier": "hot",
      "repo": "owner/repo",
      "pr_number": 123,
      "title": "Add feature X",
      "author": "octocat",
      "status": "reviewed",
      "verdict": "REQUEST_CHANGES",
      "must_fix": 2,
      "should_fix": 3,
      "suggestions": 1,
      "updated_at": "2026-07-30T12:04:00Z"
    }
  ]
}
```

## `<review_id>/meta.json` — one per review

```json
{
  "schema": 1,
  "review_id": "owner_repo_123",
  "repo": "owner/repo",
  "pr_number": 123,
  "url": "https://github.com/owner/repo/pull/123",
  "title": "Add feature X",
  "author": "octocat",
  "base_branch": "main",
  "head_branch": "feature/x",
  "additions": 120,
  "deletions": 30,
  "changed_files": 5,
  "labels": ["backend"],
  "commits": ["Add feature X", "Fix lint"],
  "files": [{"path": "a.py", "additions": 10, "deletions": 2}],
  "story": "As a user I want ...",
  "chunk_count": 3,
  "chunks_reviewed": 0,
  "status": "pending_review",
  "verdict": null,
  "created_at": "2026-07-30T12:00:00Z",
  "updated_at": "2026-07-30T12:00:00Z"
}
```

## `<review_id>/chunk_<n>.json` — one per chunk, one page in the webapp

`fetch` writes every chunk's stub immediately — `diff` and `files` derived
mechanically from the chunk's own diff text, `findings: []` and `reviewed:
false` — so a large PR's pages are all browsable while review is still in
progress. `persist-chunk` later merges the agent's findings into this same
file and flips `reviewed` to `true`; nothing else in the file changes.

```json
{
  "schema": 1,
  "chunk": 1,
  "files": ["a.py", "b.py"],
  "diff": "diff --git a/a.py b/a.py\n...",
  "findings": [
    {
      "category": "correctness",
      "severity": "must-fix",
      "file": "a.py",
      "side": "RIGHT",
      "line": 44,
      "comment": "Off-by-one: loop should be < len, not <= len."
    }
  ],
  "reviewed": true,
  "reviewed_at": "2026-07-30T12:02:00Z"
}
```

## Agent-authored findings file (input to `persist-chunk`, not persisted as-is)

The agent writes only this — category/severity/file/side/line/comment per
finding. `files` is not part of it: the script already derived that
mechanically at fetch time, since it's a total operation (grep the chunk's
own `diff --git` headers), not a judgment call.

```json
{
  "findings": [
    {"category": "security", "severity": "must-fix", "file": "b.py", "side": "RIGHT", "line": 10, "comment": "Hardcoded API key."}
  ]
}
```
