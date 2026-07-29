# Setup and language server status

Load when installing servers, diagnosing a missing binary, or checking whether a
language is supported.

### Setup

```bash
chmod +x <SKILL-PATH>/scripts/lsp-query.sh
chmod +x <SKILL-PATH>/scripts/lsp-*.sh

# Install servers for the languages you need:
pip install python-lsp-server            # Python
go install golang.org/x/tools/gopls@latest  # Go
# Java: see lsp-java.sh stub for status
```

---


### Language Status & Server Requirements

#### Python — `pylsp` (implemented)
```bash
# Minimal
pip install python-lsp-server

# With type checking
pip install python-lsp-server pylsp-mypy

# Verify
pylsp --version
```

The wrapper auto-activates the project's `.venv`, `venv`, or `env` directory.
Falls back to the active virtual environment (`$VIRTUAL_ENV`), then system Python.

#### Go — `gopls` (implemented)
```bash
go install golang.org/x/tools/gopls@latest
export PATH=$PATH:$(go env GOPATH)/bin

# Verify
gopls version
```

The wrapper resolves the `go.mod` root automatically — you don't need to set
`--workspace` manually for Go projects.

#### Java — `jdtls` (stub — next iteration)
```bash
# When implemented, prerequisites will be:
brew install jdtls   # macOS
# or manual download: github.com/eclipse-jdtls/eclipse.jdt.ls/releases

export JDTLS_HOME=/path/to/jdtls
```

Until implemented, `lsp-java.sh` exits with a clear message listing interim
alternatives (Maven dependency tree, grep-based symbol search, IntelliJ CLI).
See the Phase A/B/C implementation plan inside `lsp-java.sh`.

---

