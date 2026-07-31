# Review criteria

What to look for in each chunk. Act as a senior engineer; be precise and
concise, no filler. Every finding anchors to one physical line — `side:
"RIGHT"` + the new-file line number for an added/context line, `side:
"LEFT"` + the old-file line number for a removed line (see
`references/schema.md` § Line anchoring). Read the chunk's `@@ -a,b +c,d @@`
hunk headers to count line numbers accurately; don't guess. A category with
nothing to report simply gets no findings — do not manufacture filler
findings to cover every category.

### correctness
Does the change match the story/ticket intent? Edge cases, off-by-one
errors, missing null/empty checks, unhandled error/exception paths.

### code-quality
Naming clarity, single-responsibility and DRY violations, unnecessary
complexity, dead or commented-out code, magic numbers/strings that should be
constants.

### security
Injection risks (SQL, command, path traversal), hardcoded secrets/tokens/
credentials, unsafe deserialization, insecure defaults, missing auth/authz
checks, unsanitized external input.

### performance
N+1 queries, missing indexes, unnecessary full-table scans, inefficient
loops or repeated expensive operations, blocking I/O on non-async paths,
unnecessary object creation.

### resource-leak
Unclosed streams/connections/file handles/locks, missing
try-with-resources/defer/finally, goroutine or thread leaks, uncancelled
contexts.

### concurrency
Shared mutable state without synchronization, race conditions, incorrect
lock scope, deadlock potential from lock ordering or nested locks.

### test-coverage
Missing unit/integration tests for new or changed logic, tests that only
cover the happy path, assertions that don't actually assert anything
meaningful, hardcoded environment assumptions in test data.

### maintainability
Non-obvious code without comment, log statements at the wrong level,
missing metrics/traces/events for observability, whether a future reader
would understand the *why*.

### dependency
New dependencies: maintenance status, license compatibility, bloat.
Breaking changes to public APIs/contracts. Migration or
backward-compatibility concerns (DB schema, config keys, serialized
formats).

## Findings file the agent writes

One JSON file per chunk, per `references/schema.md`'s "Agent-authored
findings file" shape — just `findings`
(category/severity/file/side/line/comment) per finding. Severity: `must-fix`
blocks merge, `should-fix` is significant but non-blocking, `suggestion` is
optional polish. An empty `findings` array is a valid, complete result.

## Overall verdict

Once every chunk in a review has been persisted, set one verdict for the
whole PR: `APPROVE`, `REQUEST_CHANGES` if any `must-fix` finding exists (or
judgment calls for it independent of severity tally), or `NEEDS_DISCUSSION`
when a finding needs the author's input rather than a clear fix.
