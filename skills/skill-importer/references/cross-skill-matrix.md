# Cross-Skill Integration Analysis

When a new skill is imported, analyze how it fits into the broader skills ecosystem and suggest potential cross-skill integrations.

## 1. Integration Archetypes

| Archetype | Description | Example |
|---|---|---|
| **Lifecycle Enhancement** | An existing skill loads the imported skill to improve quality or add a phase. | `brainstorming` loading `critic` to critique design proposals. |
| **Pre-requisite / Pre-check** | An existing skill calls the imported skill before performing its core task. | `pr-review` calling `repo-reliability` or a newly imported security scanner. |
| **Post-processing / Audit** | An imported skill runs after a generation or editing skill finishes. | `skill-manager` auditing a skill right after `skill-creator` or `skill-importer` runs. |
| **Specialized Tooling Subagent** | An existing skill delegates specialized tasks to a subagent equipped with the imported skill. | `python-generic` delegating performance profiling to an imported `py-profiler` skill. |

## 2. Evaluation Method

1. **Scan `AGENTS-TEMPLATE.md`**: Inspect all active skills in the library, their intents, and triggers.
2. **Match Complementary Intents**:
   - `planning` / `brainstorming` <--> `review` / `critic` / `evaluator`
   - `code-review` / `execution` <--> `vulnerability-manager` / `linter` / `profiler`
   - `meta` / `system` <--> `auditor` / `manifestor` / `importer`
3. **Draft Integration Proposals**:
   - Identify the primary host skill (`<host-skill>`).
   - Specify the exact lifecycle phase where the imported skill (`<imported-skill>`) should be invoked.
   - Draft explicit prompt text or `SKILL.md` additions to suggest to the user.

## 3. Presenting Recommendations

Present cross-skill suggestions clearly after deployment and audit:

```markdown
### 🔗 Potential Cross-Skill Integrations

The imported skill `<imported-skill>` can enhance the following existing skill(s):

1. **`<host-skill>`**
   - **Integration Point**: Phase X (e.g. initial plan review / post-build verification).
   - **Benefit**: Explains why loading `<imported-skill>` improves outcomes.
   - **Suggested SKILL.md Update**:
     > "When <trigger>, consider loading `<imported-skill>` to perform <task>."
```
