# Framing: Reframe Check and Boundaries

Phases -1 and 0. Run these before any paradigm work — the whole point is that
discovering a flaw here costs one turn, while discovering it in Phase 3 costs
two fully-specified paradigms.

## Phase -1: The Reframe Check

> Run this first. Re-run it every time a significant new constraint surfaces. This phase has no output artifact — only a gate. If all three checks pass, proceed to Phase 0. If any check fails, halt and restate.

### Check 1 — The Problem Statement Audit

State the problem in exactly one sentence. Now state the problem that problem is _actually_ solving.

If those two statements differ in subject, scope, or assumed solution space — you are solving the wrong problem. Restate before continuing.

> **Evidence pattern:** If the problem statement already contains a solution (e.g., "design a REPL-based system for..."), strip the solution and restate in pure problem terms. The solution space opens back up.

### Check 2 — The Abstraction Level Check

Classify the problem into exactly one primary level:

|Level|Description|
|---|---|
|`DATA MODEL`|The structure, shape, or contract of data at rest or in motion|
|`PROTOCOL`|How two components communicate — format, ordering, acknowledgment|
|`DEPLOYMENT`|Where components run, how they are isolated, how they discover each other|
|`ALGORITHM`|How a computation is performed, sequenced, or optimized|
|`BOUNDARY`|Where one system's responsibility ends and another begins|

Mixing abstraction levels produces false paradigm comparisons. If the problem spans multiple levels, decompose it and solve each level in order, starting with `DATA MODEL` or `BOUNDARY` — they constrain everything above them.

### Check 3 — The Invalidation Test

Name one assumption that, if wrong, scraps the entire design direction. Ask: is that assumption verified or inferred?

If inferred — state it explicitly in the Assumption Graveyard (Phase 3) before proceeding. Do not defer it.

---

## Phase 0: Define the Boundaries

> Execute fully. Halt if any section cannot be completed — name what is missing.

### Section A — The Trust Anchor

What system holds the indisputable source of truth? Define it for:

- **Data at rest** (what is the canonical store?)
- **Schema / contract** (who owns the definition of valid data?)
- **Execution decisions** (what component has final authority to accept or reject an operation?)

There is exactly one trust anchor per concern. If you identify two, you have a consistency problem that the architecture must resolve — not paper over.

### Section B — Hard Constraints

Define the non-negotiables:

|Constraint Type|Value|
|---|---|
|Compute budget|(CPU, memory ceiling)|
|Latency envelope|(acceptable response window per operation)|
|Technology mandates|(required languages, runtimes, platforms)|
|Deployment topology|(same machine / same network / distributed?)|
|Compliance / regulatory|(data residency, audit requirements)|

Any paradigm in Phase 1 that cannot satisfy these constraints is eliminated immediately — it does not enter the comparison matrix.

### Section C — Failure Tolerance

Define behavior at each failure tier:

|Failure Type|Expected Behavior|
|---|---|
|Node panic (single operation fails)|die / retry N times / skip and continue / compensate|
|Malformed input at boundary|reject with error / dead-letter / pass through with flag|
|Upstream data source goes stale|block / use stale + warn / recompute / surface to caller|
|Full process restart|state lost / state recovered from store / state reconstructed|

Unspecified failure behavior is not neutral — it defaults to undefined, which means the first real failure will be a surprise.

### Section D — Principal Trust Map

For every actor that touches the system, define its trust level and hard limits. A design is incomplete if any principal's boundaries are undefined.

|Principal|Trust Level|What It Can Do|What It Cannot Do|
|---|---|---|---|
|[Actor 1]|Untrusted / Trusted / System|...|...|
|[Actor 2]|...|...|...|

> **Flag immediately** if two principals share a capability boundary — that overlap is where privilege escalation, injection, and unintended side effects live. Name the overlap; do not assume it away.

### Section E — Boundary Data Contracts

For every system boundary identified above, define the contract **before** selecting any paradigm. A paradigm that cannot satisfy a defined contract is eliminated in Phase 1, not discovered broken in Phase 3.

For each boundary:

```
Boundary: [Component A] → [Component B]
  What crosses:    (key, schema, wire format — not "some JSON")
  Who validates:   (producer validates before sending / consumer validates on receipt)
  Malformed data:  (reject + error detail / dead-letter / panic)
  Versioning:      (how does this contract evolve without breaking either side?)
```

Repeat for every boundary in the system. If a boundary's contract cannot be stated in concrete terms, that boundary is the design's highest-risk point. Note it explicitly.

---

