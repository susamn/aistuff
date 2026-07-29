---
name: brainstorming
description: Guide rigorous, principal-aware, contract-first architectural brainstorming sessions. Designed for iterative, systems-deep thinking that pivots at the abstraction level, reasons in trust boundaries, and treats data contracts as first-class design artifacts — not implementation details.
version: 3.0.0
kind: guidance
triggers:
  - "lets brainstorm on an idea"
  - "lets plan an idea"
  - "lets plan a project"
  - "lets think about an idea"
  - "I have an idea"
intent: planning
guardrails:
  - Do not optimize for agreement — name the precise failure mode instead of praising.
  - Halt only when a missing variable blocks a verifiable contract or execution boundary, never for preferences.
  - Mark every re-entry explicitly; never silently absorb a new constraint.
created_at: 2026-05-30
updated_at: 2026-07-29
---

# Architectural Brainstorm Engine — The Defensive Deconstructionist

A spiral, not a waterfall. Work the phases in order, and re-enter earlier ones
the moment a later phase invalidates them.

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

## Phase sequence

| phase | purpose | reference |
|---|---|---|
| **-1** Reframe Check | audit the problem statement, abstraction level, invalidation test | `references/framing.md` |
| **0** Boundaries | trust anchor, hard constraints, failure tolerance, principal trust map, boundary data contracts | `references/framing.md` |
| **1** Divergence | generate architectural paradigms | `references/paradigms.md` |
| **2** Convergence | filter, trade-off matrix, deep-dive, cuts | `references/paradigms.md` |
| **3** Execution Blindspot | edge flaw, assumption graveyard, next step | `references/blindspot.md` |

Load each reference when the session reaches that phase. A session that stops
after framing never needs the rest.

## Usage Notes

**This skill is a spiral, not a checklist.** The output of Phase 3 frequently sends you back to Phase -1 or Phase 0. That is not failure — that is the skill working. A design that survives Phase 3 without a re-entry has either been examined deeply or was too simple to need this skill in the first place.

**Descriptions are design artifacts.** Every operation, boundary, and principal description written during this process is a contract fragment. Write them as if they will be consumed by a system that cannot ask clarifying questions — because eventually, one will be.

**Phase -1 is cheap. Phase 3 rewrites are expensive.** Spend time on the Reframe Check. The cost of discovering a problem statement flaw in Phase -1 is one conversation turn. The cost of discovering it in Phase 3 is discarding two fully-specified paradigms.