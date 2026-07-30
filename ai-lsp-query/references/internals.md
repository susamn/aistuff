# Architecture and adding a language

Load only when modifying the skill itself — the dispatcher, the JSON-RPC engine,
or adding a new language wrapper.

### Architecture

```
lsp-query.sh  (dispatcher)
     │
     ├── lsp-python.sh   ─── activates venv, selects pylsp/pyright
     ├── lsp-go.sh       ─── resolves go.mod root, configures gopls
     └── lsp-java.sh     ─── stub (jdtls — next iteration)
              │
              └──► lib/lsp-rpc.py   (JSON-RPC engine)
                        │
                        ├── LspSession     — process lifecycle, stdio framing
                        ├── Query methods  — hover, references, definition, ...
                        └── Formatters     — table (human) | json (machine)
```

`lsp-rpc.py` is language-agnostic. Adding a new language requires only a new
`lsp-<lang>.sh` wrapper that sets `--server-cmd` and `--language-id` correctly.
The protocol handling, query dispatch, and output formatting are inherited for free.

---

### Adding a New Language

Create `<SKILL-PATH>/scripts/lsp-<lang>.sh`:

```bash
#!/usr/bin/env bash
# Minimal new language wrapper

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RPC_SCRIPT="${SCRIPT_DIR}/lib/lsp-rpc.py"

# 1. Parse forwarded args (copy the arg-parsing block from lsp-go.sh)
# 2. Check the LSP server binary exists
# 3. Set SERVER_CMD and INIT_OPTIONS for this language
# 4. Call:

exec python3 "$RPC_SCRIPT" \
  --server-cmd  "$SERVER_CMD" \
  --workspace   "$WORKSPACE" \
  --file        "$FILE" \
  --query       "$QUERY" \
  --language-id "<lang-id>" \
  --output      "$OUTPUT" \
  --timeout     "$TIMEOUT" \
  --init-options "$INIT_OPTIONS"
```

Then register the extension in `lsp-query.sh`'s `detect_language()` function:
```bash
myext) echo "mylang" ;;
```

## Script roles

| script | role |
|---|---|
| `scripts/lsp-query.sh` | Main dispatcher. Detects language from extension or `--lang`, validates prerequisites, delegates to the language wrapper. **The only script other skills should call.** |
| `scripts/lsp-python.sh` | Python bootstrap. Activates the project venv (or Playground), selects pylsp or pyright, disables noisy plugins. |
| `scripts/lsp-go.sh` | Go bootstrap. Locates the go.mod root, configures gopls with staticcheck and inlay hints, respects GOPATH/GOROOT. |
| `scripts/lsp-java.sh` | Java stub (jdtls). Not wired — prints interim alternatives and the roadmap. |
| `scripts/lsp-rpc.py` | Core JSON-RPC engine. Owns the LSP protocol: initialize handshake, didOpen, all query types, response parsing, formatting. Not invoked directly. |
