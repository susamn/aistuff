# The pipeline script contract

Required reading before writing a `kind: pipeline` skill. Everything here exists
to keep determinable work out of inference and raw data out of context.

## Stream discipline

| stream | carries | rule |
|---|---|---|
| stdout | **data only** — the projection or artifact path | machine-parseable, nothing conversational |
| stderr | diagnostics, progress, warnings | never parsed; safe to be verbose |
| exit code | `0` success · `1` violations found · `2` could not run | the agent branches on this before reading anything |

A script that mixes progress chatter into stdout forces the agent to parse prose
to find the data. Keep them separate and the agent can trust stdout blindly.

## Failure is a value, not a crash

An unhandled traceback is itself a context dump — the exact thing this contract
prevents. Catch failures and emit a structured value instead:

```json
{ "status": "error", "id": "<pointer/step id>", "reason": "one line, no stack",
  "log": "/abs/path/to/full-error.log",
  "remedy": "gh auth login" }
```

The agent sees one line and knows where the detail is. Never print a stack trace
to stdout; write it to the log path and reference it.

`remedy` is **optional, and only for enumerated failures the script recognizes** —
a missing binary, an unauthenticated CLI, an absent config key. For those the fix
is deterministic and the script author knows it better than the agent can infer
at runtime, so stating it saves a diagnostic round trip.

Never attach a `remedy` to an unexpected error. A confidently wrong suggestion is
worse than none: it aims the agent at the wrong fix with the authority of the
tool that just failed. Unknown failure means `reason` plus `log`, nothing more.

Partial failure must not abort the run. A pipeline of ten steps where step four
fails should return nine results plus one structured error, not nothing.

## Recovery is the agent's call

A script *reports* failure; it does not decide the response. Retrying with
different arguments, skipping the step, falling back to another data source, or
stopping to ask the user are judgment calls that depend on what the user is
trying to achieve — context the script does not have and cannot be given.

This is also why partial failure must return partial results: the agent needs to
see what succeeded before it can sensibly choose what to do about what didn't.

## The summary projection (mandatory)

Every pipeline skill ships a command whose only job is the script→agent boundary.
Without it, the agent reads a full artifact to write three sentences — the most
common way this whole design gets defeated in practice.

```
<script> summary <artifact>
```

emits **one line per finding**, and nothing else:

```
commit-size-discipline   warning   18.2% commits >1000 LOC   PR #412
contributor-concentration critical  bus factor 1             a4f21c9
issue-staleness          ok        median 3.1d               —
<artifact>: /home/user/.local/share/<skill>/data/<project>.json
```

Rules:

- One line per finding. If there are more than ~30 findings, the projection
  itself must rank and truncate, and say how many were withheld.
- Every line carries **evidence** — a commit hash, PR number, file path, row id.
  A number without evidence cannot be verified or explained by the agent.
- The last line is always the **handle**: the absolute path of the full artifact.
  This is the escape hatch. It is not optional.

## Handles: the escape hatch

Compression is inference relocated to authoring time. You are guessing, at
authoring time, what will matter at runtime — and anomalies hide in exactly what
you filtered out. The handle is what makes that guess recoverable.

A handle is any of: an absolute artifact path, a re-run command with narrower
scope, or a file path plus line range. Every compressed output carries one.

When the agent sees a number that looks wrong, it follows the handle rather than
reasoning about a summary it cannot verify.

## Tunables live in data

Logic in code, thresholds in data — always separable:

```json
{ "thresholds": { "metric": "giant_commit_pct", "direction": "higher_is_worse",
                  "warning": 5, "critical": 15 } }
```

```python
band = band_for(value, cfg["thresholds"])   # logic — total, in code
```

Retuning a threshold must never require touching logic. If a user says "15 is too
aggressive," that is a one-line data edit, and the change is visible in a diff.

Determinism is not correctness. A frozen heuristic run a thousand times is
reproducibly wrong, with the false authority of a number. Keep the thresholds in
data so they stay visibly a choice, and always present a band together with its
evidence, never as a verdict.

## Modes, not multiplication

One entrypoint with subcommands, rather than a directory of single-purpose files:

| mode | emits | for |
|---|---|---|
| `analyze <target>` | artifact path only | the run itself |
| `summary <artifact>` | one line per finding + handle | the agent, by default |
| `verbose <artifact>` | full detail | drill-down after a suspect summary |
| `validate <artifact>` | nothing, exit code only | CI and pre-commit checks |

Every script is a contract someone has to keep in sync with its callers. Five
scripts sharing an artifact format means five places for schema drift; one script
with five modes means one. Split out a second entrypoint only when it is
independently useful to a caller that does not want the first.

The counterweights from `SKILL.md` apply here hardest. A one-off analysis needs a
ten-line script, not an artifact schema and a threshold file. Add modes when a
second caller actually appears — the cost of collapsing two scripts later is far
lower than the cost of maintaining infrastructure nobody uses.

## Chaining steps

When one script feeds another:

- Intermediate artifacts go **to disk**, not through the agent. The agent
  orchestrates by passing paths, never contents.
- Every artifact carries a `schema` version integer. A consumer that reads an
  unexpected version exits `2` with a clear reason rather than misinterpreting.
- Each step is independently runnable against a stored artifact, so a failure is
  debuggable without re-running the whole chain.

A chain the agent cannot observe is a black box: when the last step is wrong,
nothing can localize the fault. Independently runnable steps plus versioned
artifacts are what buy back that observability.

## Environment

Scripts resolve their own location rather than assuming a working directory —
skills are reached through symlinks, so `$0` may be anywhere:

```bash
SKILL_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
```

Declare every external binary in frontmatter `tools:`. Check for it and exit `2`
with a clear reason if missing, rather than failing deep in a pipe.

## Checklist

Before a pipeline skill is done:

- [ ] stdout carries data only; diagnostics on stderr
- [ ] exit codes 0/1/2 used as specified
- [ ] failures emit a structured error with a log path; no stack traces on stdout
- [ ] `remedy` present only on failures the script actually recognizes
- [ ] partial failure returns partial results, so the agent can choose a fallback
- [ ] modes on one entrypoint rather than several single-purpose scripts
- [ ] no schema/threshold/projection scaffolding built for a one-off
- [ ] a `summary` projection exists and is documented in SKILL.md
- [ ] every summary line carries evidence
- [ ] the artifact handle is printed
- [ ] thresholds live in data, not code
- [ ] intermediate artifacts are versioned and stay out of context
