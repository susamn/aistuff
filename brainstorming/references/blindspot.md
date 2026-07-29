# The Execution Blindspot

Phase 3: edge flaws, the assumption graveyard, and the next step. Load once a
paradigm has survived convergence.

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

