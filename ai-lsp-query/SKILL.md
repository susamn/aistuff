---
name: ai-lsp-query
description: >
  Semantic code intelligence via LSP servers. Answers structured questions about
  a codebase — references, definitions, type info, call hierarchies, symbol
  listings, and diagnostics — using the same AST-backed data an IDE uses.
  Composable: any other skill can call lsp-query.sh to get semantic context
  before generating or validating code.
version: 2.0.0
kind: pipeline
triggers:
  - "find all references to"
  - "who calls this function"
  - "what type is this"
  - "go to definition"
  - "find implementations of"
  - "list symbols in file"
  - "lsp query"
  - "semantic code search"
intent: execution
guardrails:
  - "Use --output json when the result feeds another script or skill — not for human display."
  - "LSP servers index on startup — expect 1–5s latency for Python/Go, up to 90s for Java (jdtls first run)."
  - "lsp-query.sh uses the git root as the workspace by default. Override with --workspace if the project root differs."
  - "For positional queries prefer --symbol over --line/--col — symbol search survives file edits."
  - "Never query generated files (build/, target/, dist/, __pycache__/) — results are noisy and unreliable."
  - "Java support is a stub. Use the interim alternatives printed by lsp-java.sh until jdtls is wired."
resources:
  - <SKILL_PATH>/scripts/lsp-query.sh
  - <SKILL_PATH>/scripts/lsp-python.sh
  - <SKILL_PATH>/scripts/lsp-go.sh
  - <SKILL_PATH>/scripts/lsp-java.sh
  - <SKILL_PATH>/scripts/lsp-rpc.py
tools:
  - bash
  - python3
created_at: 2026-05-30
updated_at: 2026-07-29
---

# AI LSP Query — semantic code intelligence

Ask an LSP server the questions an IDE asks, and get AST-backed answers instead
of grep guesses. `lsp-query.sh` is the only entrypoint other skills should call.

```bash
<SKILL_PATH>/scripts/lsp-query.sh --file <path> --query <type> [--symbol <name>]
```

### Query Reference

| Query | What it answers | Requires position? |
|---|---|---|
| `hover` | Type signature and doc comment at a symbol | Yes |
| `definition` | Where a symbol is declared | Yes |
| `references` | Every call site / usage across the workspace | Yes |
| `implementations` | All concrete implementations of an interface or abstract | Yes |
| `symbols` | Every symbol declared in a single file | No |
| `workspace-symbols` | Symbol search across the entire project | No (uses --symbol as search term) |
| `call-hierarchy` | Who calls this function (callers) + what it calls (callees) | Yes |
| `diagnostics` | Errors and warnings the server reports for a file | No |

---


## Output

Default output is a human-readable table. Pass `--output json` when another
script or skill consumes the result — that is the machine-readable projection,
and it keeps raw server responses out of context.

Language support: Python and Go are implemented; Java is a stub. Details and
install commands are in `references/setup.md`.

## Read next

| file | when |
|---|---|
| `references/setup.md` | installing servers, a missing binary, checking language support |
| `references/examples.md` | concrete invocations, calling this skill from another skill |
| `references/internals.md` | modifying the dispatcher, RPC engine, or adding a language |
