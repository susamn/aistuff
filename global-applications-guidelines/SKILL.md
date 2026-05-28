
---
name: global-applications-guidelines
description: Core architectural and implementation guidelines for all application development.
version: 1.0.0
triggers:
  - "start a new project"
  - "architecting an application"
  - "implementing a new feature"
  - "want to build a new app"
  - "lets work on a project"
  - "lets create a new app"
intent: system
guardrails:
  - Do not bypass the type system
  - Do not suppress warnings
  - Do not introduce redundant logic
---

# Global Application Development Guidelines

When creating a new application or modifying an existing project, adhere to the following universal rules regardless of platform, language, or framework:

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.


# Execution workflow

## 1. Planning & Architecture
- **Architecture First:** Always create an `ARCHITECTURE.md` to brainstorm ideas and outline the high-level design. Clarify any questions with the user *before* beginning implementation.

## 2. Modularity & Documentation
- **Strict Modularity:** The project must be modular. Logic must be encapsulated within designated module directories.
- **Standard Documentation (Per Module):** Every module must contain:
  - `CONTEXT.md`: Explicitly defines the module's primary responsibility and scope.
  - `TODO.md`: A live task list. Items must be ticked off only upon completion and verification.
- **Scaffolding New Modules:** When creating a new module, you must initialize it with a `CONTEXT.md`, a `TODO.md`, and a dedicated `tests/` directory. Before making code changes, always read the module's `CONTEXT.md`, `TODO.md`, and the global `DEPENDENCY.md`.

## 3. Global Coordination Files
These files must exist at the root of the project:
- `ARCHITECTURE.md`: Contains the project architecture, requirements, and high-level design.
- `DEPENDENCY.md`: Clearly defines inter-module dependencies. **Rule:** This file must be symlinked into every child module.
- `PROJECT_STATE.md`: Mandatory root file to track architectural decisions and progress. **Rule:** This file must be symlinked into every child module.
  ```markdown
  - **Phase**: [Current Phase]
  - **Type**: [Fullstack/Frontend]
  - **Stack**: [List of selected techs]
  - **Modules**: [List of modules]
  - **API Status**: [Draft/Finalized]
  
  ## Module Updates
  [Each module adds its high-level status and major changes here, only relevant and single line containing the above information so that it can be easily read by other modules for their Reference]
  ```

## 4. Verification & Safety
- **Test-Always Rule:** Run tests after every change. For every change, you MUST create or update test cases.
- **Test-Preservation:** NEVER delete test cases without explicit notification and justification.
- **CVE Audit:** Before completing a task, check dependencies for active vulnerabilities (e.g., `npm audit`, `pip-audit`, `safety check`) and report any active CVEs to the user immediately.

## 5. Execution Strategy
- **Atomic Changes:** Work on one small item from the `TODO.md` at a time.
- **Minimal PRs:** Never pack too many unrelated changes into a single PR/Commit.

## 6. The "Contract First" Rule
- Interface and API definitions must precede any implementation.

## 7. Web Domain Mandate (OpenAPI)
For any web-based project, an **OpenAPI Schema** MUST be used as the source of truth to bind backend and frontend.
- **Contract-First Workflow:**
  1. Use the `openapi-schema-creator` skill to design the schema.
  2. **Iterate** with the user through design reviews until the schema is explicitly **finalized**.
  3. **LOCK:** Do NOT proceed to implementation or code generation until the schema is locked and saved.
- The schema acts as the immutable "Contract" allowing transport and client layers to be developed and tested independently.

## 8. Logging
- Logging must be done properly. Every method call must have some sort of log to trace execution (use debug and info levels appropriately) for easier troubleshooting.

## 9. Skill Loading
- When working on specific languages or frameworks, first check if there is a skill available for it in the available skills directory and utilize any relevant skills on demand to assist with specialized tasks.
