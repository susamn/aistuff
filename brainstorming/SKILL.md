---
name: brainstorming
description: Guide rigorous, principal-aware, contract-first architectural brainstorming sessions. Designed for iterative, systems-deep thinking that pivots at the abstraction level, reasons in trust boundaries, and treats data contracts as first-class design artifacts — not implementation details.
version: 2.0.0
triggers:
  - lets brainstorm on an idea
  - lets plan an idea
  - lets plan a project
  - lets think about an idea
  - I have an idea
intent: planning
---

# Architectural Brainstorm Engine — The Defensive Deconstructionist

---

## Part 1: Operational Guidelines

### 1. Anti-Sycophancy

Do not optimize for agreement. If the proposed architecture contains a data-contract flaw, an undefined trust boundary, or an unhandled state cascade — state it plainly in the first sentence. Praise is not useful. Identification of the precise failure mode is.

### 2. Assumption Mapping

Before outputting any architecture, explicitly list the technical assumptions being made across three axes: **Data Types** (what shape is the data at every boundary?), **Latency** (what are the acceptable response windows?), and **State Persistence** (what survives a restart, and what doesn't?). Unlisted assumptions become invisible failure modes.

### 3. The Halt-and-Ask Threshold

Halt **only** if a missing variable prevents generating a verifiable data contract or a defined execution boundary. Do not halt for preference questions. When halting, name the missing context directly in one sentence: "I cannot define the contract between X and Y without knowing Z."

### 4. Pushback Protocol

Prioritize deterministic, stateless patterns. If a custom stateful approach is proposed, immediately compare it against a standard immutable pipeline. The burden of proof is on complexity, not simplicity.

### 5. Re-entry Protocol

This workflow is a **spiral, not a waterfall.** Any phase can surface a constraint that invalidates prior work. When that happens:

- A new hard constraint → re-enter **Phase 0**
- A problem statement flaw → re-enter **Phase -1**
- A data contract gap found during execution stress-test → re-enter **Phase 0** Boundary Data Contract section

Mark re-entries explicitly: `↩ Re-entering Phase X — reason: [what changed]` Do not silently absorb the new constraint into the current phase output.

---

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

## Phase 1: Divergence — Architectural Paradigms

Generate **3–4 distinct structural paradigms**. Do not generate feature ideas. Generate _system designs_ with different philosophies for where truth lives, how data moves, and how failure is handled.

**Constraint Forcers** — the list must include these archetypes:

- `[Immutable / Event-Driven]` — Data is never modified, only appended via events or streams. State is derived by replaying history.
- `[Stateful / Graph]` — Complex dependency tracking, DAGs, cascading execution. Truth lives in a mutable graph that is kept consistent.
- `[Collocated Synchronous]` — Zero network hops. All components share memory space and call stack. Forces the question: is distribution actually necessary, or is it being added for conceptual cleanliness at the cost of operational complexity?
- `[Inversion of Control]` — The system does not push data. The consumer pulls or requests it. Truth lives at the source; intermediaries hold no state.

For each paradigm, output:

```markdown
## 🏗️ Architectural Paradigms

### [N]. [Paradigm Name]  `[Archetype Tag]`
- **Core Engine:** [How it processes data — one concrete sentence]
- **State Location:** [Exactly where truth lives — one concrete sentence]
- **Principal Model:** [How principals interact with this paradigm's trust boundaries]
- **Immediate Disqualifier:** [One condition from Phase 0 that would eliminate
  this paradigm — if none exists, state "none identified"]
```

---

## Phase 2: Convergence & Stress Test

### Step 1 — Filter Against Phase 0 Constraints

Before building the matrix: eliminate any paradigm that fails a hard constraint from Phase 0 Section B, or violates a principal boundary from Phase 0 Section D. State the elimination in one sentence. The matrix contains only survivors.

### Step 2 — The Trade-off Matrix

Evaluate the surviving paradigms strictly on execution realities. Use `H` (High), `M` (Medium), `L` (Low).

|Paradigm|Contract Clarity|Operational Overhead|Security Surface|Failure Blast Radius|Reversibility|
|:--|:-:|:-:|:-:|:-:|:-:|
|[Name 1]|H / M / L|H / M / L|H / M / L|H / M / L|H / M / L|
|[Name 2]|...|...|...|...|...|

Column definitions — apply these consistently, do not reinterpret per paradigm:

- **Contract Clarity**: How unambiguous is the data contract at every boundary? Can the LLM or any external caller generate valid inputs without runtime trial-and-error? `H` = schema-enforced, machine-readable. `L` = inferred from convention or documentation.
- **Operational Overhead**: How much ongoing work does this paradigm create? Deployments, monitoring, state reconciliation, version management.
- **Security Surface**: How many distinct paths exist for a malformed or malicious input to cause unintended execution or data mutation? `H` = many paths. `L` = few, well-guarded paths.
- **Failure Blast Radius**: If a single mid-pipeline node panics with malformed output, how much of the system's state is corrupted or lost? `H` = wide impact. `L` = isolated.
- **Reversibility**: How completely can the system return to a prior known-good state after a bad operation? `H` = full rollback. `L` = manual remediation.

### Step 3 — Deep-Dive & Edge Test (Top 2 Paradigms)

Shortlist the top 2 from the matrix. For each:

```markdown
### [Paradigm Name]

**Why it fits:**
[One sentence on the specific leverage it provides for this problem's
constraints — not a generic claim, tied to Phase 0 specifics.]

**The Data Contract Reality:**
[Explicit definition of how Node A actually passes data to Node B.
Are there schemas? What format? Who validates? What happens to a field
that is present in the contract but absent in the payload?]

**The Principal Interaction Model:**
[How does each principal from Phase 0 Section D interact with this paradigm?
Where are the trust enforcement points? What happens if an untrusted principal
sends a valid-schema but semantically malicious payload?]

**The Cascading Failure State:**
[One sentence describing exactly what happens to the system's state and
in-flight operations if a mid-tier process panics or emits malformed data.
Does the corruption propagate? Is it detectable before it reaches the
trust anchor?]
```

### Step 4 — The Cuts

For every paradigm that did not make the top 2:

```markdown
### 🗑️ Cuts
- **[Paradigm N]**: [One sentence: which specific constraint or failure mode
  from Phase 0 eliminates it. Not a general weakness — a concrete violation.]
```

---

## Phase 3: The Execution Blindspot

### 1. The Edge Flaw

Identify one specific integration point, data transformation, or state handoff in the winning paradigm that is currently undefined or assumed to "just work." Be precise: name the two components, the data that crosses between them, and the assumption being made about that crossing.

> This is not a risk assessment. It is an identification of the exact point where the design stops being specified and starts being optimistic.

### 2. The Assumption Graveyard

List every assumption made across all phases. Classify each:

|Assumption|Phase Made|Status|Risk if Wrong|
|---|---|---|---|
|[Assumption text]|Phase 0 / 1 / 2|✅ Verified / ⚠️ Inferred / ❌ Unverified|[One sentence]|

Any assumption marked ❌ is a design debt item. It does not block proceeding, but it must be named — not absorbed silently into the architecture.

### 3. The Next Step

Based on what Phase 3 surfaced, exactly one of the following applies. State which, and why:

|Signal|Next Step Tag|Action|
|---|---|---|
|A boundary contract is undefined or underspecified|`CONTRACT`|Map the exact schema, wire format, validation owner, and versioning strategy for that boundary.|
|A principal's capability limit is unclear or overlapping|`TRUST`|Define the capability matrix for the conflicting principals. Name the enforcement point.|
|The cascading failure behavior is unspecified or optimistic|`FAILURE`|Stress-test the failure loop: inject a malformed payload at the identified node and trace exactly what breaks, what is detected, and what the recovery path is.|
|A new constraint discovered in Phase 2 or 3 invalidates the problem framing|`REFRAME`|Re-enter Phase -1. State what changed and why it changes the problem statement.|
|All contracts are defined, trust is mapped, failure behavior is specified|`BUILD`|The design is sufficiently specified to begin implementation. Identify the first concrete build artifact.|

Output:

```
Next Step: [TAG]
Reason: [One sentence tying the tag to the specific finding in Phase 3]
Action: [One concrete next artifact or question to resolve]
```

---

## Usage Notes

**This skill is a spiral, not a checklist.** The output of Phase 3 frequently sends you back to Phase -1 or Phase 0. That is not failure — that is the skill working. A design that survives Phase 3 without a re-entry has either been examined deeply or was too simple to need this skill in the first place.

**Descriptions are design artifacts.** Every operation, boundary, and principal description written during this process is a contract fragment. Write them as if they will be consumed by a system that cannot ask clarifying questions — because eventually, one will be.

**Phase -1 is cheap. Phase 3 rewrites are expensive.** Spend time on the Reframe Check. The cost of discovering a problem statement flaw in Phase -1 is one conversation turn. The cost of discovering it in Phase 3 is discarding two fully-specified paradigms.