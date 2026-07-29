# Guidance skills and progressive disclosure

For `kind: guidance` — skills that encode judgment with nothing to compute. Also
the playbook for splitting an oversized skill of any kind.

## The rule

A guidance skill has **zero scripts**. There is no runtime input to read, so
there is nothing total to compute. Adding scripts here converts judgment into a
frozen heuristic and makes the skill worse.

Its only real failure mode is size: a single SKILL.md that grows until it is a
manual nobody routes through, loaded whole into context whenever it triggers.

## Structure

```
skill-name/
├── SKILL.md          # ≤150 lines — router only
└── references/
    ├── <topic-a>.md  # loaded only when the task touches topic A
    └── <topic-b>.md
```

SKILL.md answers three questions and stops:

1. When does this skill apply?
2. What are the non-negotiable rules — the few that apply to every task?
3. Which reference covers the topic at hand?

Everything else is a reference. The test for whether content belongs in SKILL.md:
*would this be true and relevant for every single invocation?* If not, it is a
reference.

## The routing table

End SKILL.md with an explicit table. This is what makes disclosure actually
progressive — without it the agent has no way to know a reference exists.

```markdown
## Read next

| file | when |
|---|---|
| `references/data-access.md` | repositories, entities, transactions, JPA |
| `references/security.md`    | authentication, authorization, filters |
| `references/testing.md`     | writing or reviewing tests |
```

Name the *situation*, not the file's contents. The agent matches its current task
against the situation column.

## Splitting an oversized skill

1. Outline the current headings — each top-level section is a candidate reference.
2. Group into 3–7 topics along the lines of *when they are needed*, not by
   subject-matter tidiness. Two sections always needed together belong in one file.
3. Extract each topic verbatim to `references/<topic>.md`. Do not rewrite while
   moving — split first, edit later, so the diff stays reviewable.
4. Reduce SKILL.md to the router: applicability, universal rules, routing table.
5. Anything that survives in SKILL.md must pass the every-invocation test.

## Universal rules stay in SKILL.md

A handful of rules apply to every task in the domain and belong in the router —
version baselines, a hard prohibition, a convention that would corrupt work if
missed. Keep these few and absolute. If the list grows past roughly ten, it is
not universal rules any more; it is a reference.

## What not to do

- Do not split into files so small the routing table costs more than the content.
- Do not duplicate a rule into several references so it is "not missed." It drifts.
  Put it in SKILL.md once.
- Do not create `references/overview.md`. If it is needed every time, it is
  SKILL.md; if it is not, it is not needed.
