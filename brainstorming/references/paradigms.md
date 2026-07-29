# Divergence and Convergence

Phases 1 and 2: generating architectural paradigms, then filtering, stress-testing,
and cutting them. Load after Phase 0 boundaries are settled.

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

