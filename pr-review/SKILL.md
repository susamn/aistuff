---
name: pr-review
description: Generate a structured, LLM-ready PR review prompt from a GitHub pull request — fetches metadata, diff, and file list, injects optional story/ticket context, and writes a review-ready markdown file.
version: 2.0.0
kind: pipeline
triggers:
  - "review this PR"
  - "review pull request"
  - "generate PR review prompt"
  - "pr review for <url>"
  - "review <github-url>"
intent: code-review
guardrails:
  - Do not post or submit the review anywhere — output to a local file only
  - Do not proceed without a valid GitHub PR URL confirmed by the user
  - Do not include secrets, tokens, or credentials in the generated output
  - Warn if the diff exceeds ~500 KB (LLM context limits)
resources:
  - <SKILL_PATH>/scripts/pr-review-gen.sh
tools:
  - bash
  - gh
  - jq
created_at: 2026-05-30
updated_at: 2026-07-29
---

# PR review

Extracts a PR's diff and metadata into a structured review prompt, split into
~100 KB chunks to stay inside LLM context limits. Chunks are consumed by hand or
iterated automatically by the `pr-review-ui` skill.

## Workflow

1. Confirm the PR URL with the user.
2. Optionally take a story/ticket file for context (`-s <path>`); the script
   prompts interactively if omitted.
3. Run:

   ```bash
   bash "<SKILL_PATH>/scripts/pr-review-gen.sh" [-s <story_file>]
   ```

4. Relay the prompts directory to the user. Do not read the chunks into context
   unless asked — they are deliberately sized for a separate review pass.

## Output

stdout carries two tab-separated fields; all progress and decoration go to stderr.

```
prompts_dir	/tmp/pr-review/<id>/prompts/
chunks	3
```

`prompts_dir` is the handle. Each chunk file (`p1.txt`, `p2.txt`, …) contains the
PR title, story context, description, commits, changed files, that chunk's diff,
and review instructions covering correctness, code quality, security,
performance, resource leaks, concurrency, test coverage, maintainability, and
dependency changes.

## Dependencies

`gh` (authenticated) and `jq`. The script exits with a clear error if either is
missing. Note `gh` is **not currently installed on this machine** — the skill
cannot run until it is.

## Notes

- Prompts live under `/tmp/pr-review/<random-id>/` to stay out of the workspace.
- `pr-review-ui` depends on this exact directory layout.
