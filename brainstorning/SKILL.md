# Brainstorm Skill

A two-phase brainstorming workflow: **diverge** (quantity, no judgment) → **converge** (filter, rank, shortlist). Works across any domain — technical, product, creative, strategic.

---

## Phase 0: Clarify (fast, lightweight)

Before generating ideas, extract just enough context to avoid generic output. Keep this conversational — one short round of questions at most.

Ask if not already known:

1. **What's the core goal or problem?** (1–2 sentence summary)
2. **Constraints or non-starters?** (tech stack, time, budget, team size, regulatory)
3. **Who is this for?** (end users, system, internal team)
4. **What does "good" look like?** (metric, feeling, outcome)

If the user's message already contains enough context, skip Phase 0 entirely and proceed to Phase 1. Don't ask clarifying questions just for the sake of it.

---

## Phase 1: Diverge

Generate **10–15 distinct ideas**. Breadth over depth here — cover different solution archetypes, not just variations of one theme.

### Diverge principles

- **No self-censorship.** Include ideas that seem too simple, too ambitious, or off-beat. Unusual ideas often spark the best ones.
- **Cover multiple dimensions.** For each domain, span these lenses:
    
    |Domain|Lenses to cover|
    |---|---|
    |Technical / Architecture|build vs. buy, sync vs. async, centralized vs. distributed, simple-now vs. extensible-later|
    |Product / Feature|user-facing vs. internal, quick win vs. long-term, data-driven vs. opinionated|
    |General problem-solving|eliminate the problem, workaround it, reframe it, delegate it, automate it|
    
- **Label ideas briefly.** One punchy name + one sentence. No deep explanations yet.
- **Number them** (1–N) for easy reference in the converge phase.

### Diverge output format

```
## 💡 Ideas (Diverge)

1. **[Idea Name]** — [One sentence: what it is and the core insight]
2. **[Idea Name]** — [One sentence]
...
```

---

## Phase 2: Converge

Filter and rank the idea list down to a **shortlist of 3–5 ideas** worth pursuing.

### Convergence criteria

Score each idea across these axes (adapt weights to domain):

|Criterion|Description|
|---|---|
|**Impact**|How much does this move the needle on the stated goal?|
|**Feasibility**|How realistic given constraints (time, tech, team)?|
|**Novelty**|Does it open new possibilities vs. incremental?|
|**Reversibility**|Can you undo it if it doesn't work? (higher = safer)|
|**Fit**|How well does it match the user's context and stated preferences?|

You don't need to score every idea numerically — use judgment to cluster ideas into tiers:

- **Top tier**: strong on most criteria → include in shortlist
- **Interesting but risky**: high impact, low feasibility → flag but don't shortlist
- **Table stakes / obvious**: include if genuinely good, but note it's the safe choice
- **Cut**: weak on multiple criteria → briefly explain why

### Converge output format

```
## 🎯 Shortlist (Converge)

### 1. [Idea Name]
**Why it made the cut:** [2–3 sentences: impact + fit + feasibility]
**Watch out for:** [1 sentence: biggest risk or trade-off]
**Good next step:** [1 concrete action to explore or validate this]

### 2. [Idea Name]
...

---
### 🗑️ Cuts
- **[Idea N]**: [One sentence why it was dropped]
- **[Idea M]**: [One sentence]
```

---

## Phase 3: Invite Iteration

After presenting the shortlist, close with one of these invitations (pick the most natural):

- _"Want me to go deep on any of these — trade-offs, implementation sketch, or risks?"_
- _"Any of these resonate? I can generate variants or push the shortlist in a different direction."_
- _"Should I stress-test the top pick against your constraints?"_

Do not ask multiple questions. Pick one.

---

## Domain-specific guidance

### Technical / Architecture brainstorming

- Always include at least one "boring but solid" option (proven tech, well-understood trade-offs)
- Always include at least one "what if we didn't build this at all" option (buy, SaaS, eliminate)
- Flag CAP theorem, consistency, latency, and operational complexity where relevant
- Reference well-known patterns by name (CQRS, event sourcing, sidecar, strangler fig, etc.)

### Product / Feature brainstorming

- Frame ideas around user value, not implementation
- Include at least one "Trojan horse" idea — a small thing that unlocks a larger capability
- Flag ideas that create lock-in or technical debt

### General / Open-ended

- Use "How Might We" reframes to unlock stuck thinking
- If the problem feels too big, suggest decomposing it first
- Watch for [XY problems](https://xyproblem.info/) — if the user seems to be solving a symptom rather than a cause, gently surface the underlying issue

---

## Anti-patterns to avoid

- **Vague ideas**: "Use AI" or "refactor the service" are not ideas — push to something concrete
- **Variations disguised as distinct ideas**: "Redis cache" and "Memcached cache" are the same idea
- **Skipping diverge**: Don't shortlist immediately — the user needs the breadth to make a real choice
- **Over-qualifying in diverge phase**: Save judgment for Phase 2
- **Padding the shortlist**: 3 strong ideas beat 5 mediocre ones

---

## Quick-start examples

**User:** "Brainstorm ways to reduce API latency in our payments service" → Phase 0: extract current stack, p99 target, whether it's read or write heavy → Phase 1: generate 10–15 ideas spanning caching, async, protocol changes, schema changes, infra → Phase 2: shortlist top 3–5 by feasibility + impact for a payments context

**User:** "How might we improve onboarding for non-technical users?" → Phase 0: who are the users, what's the current drop-off point, what counts as "onboarded" → Phase 1: generate 10–15 ideas spanning UX, automation, content, social proof, progressive disclosure → Phase 2: shortlist by user impact + quick-win potential

**User:** "Ideas for a personal project to learn distributed systems" → Phase 0: experience level, time available, preferred language → Phase 1: generate 10–15 project ideas at varying complexity levels → Phase 2: shortlist by learning density + tractability for solo work