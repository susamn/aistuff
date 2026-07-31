---
name: python-generic
description: Universal guidelines, patterns, and best practices for Python development. Use when working on any Python project, script, or backend.
version: 2.0.0
kind: guidance
triggers:
  - "work on python project"
  - "create python script"
  - "python backend"
intent: execution
guardrails:
  - "Never install packages globally; I use pyenv — activate the virtual environment called Playground for generic work and install there. If an existing venv is present in the current directory, use it."
  - "Prefer `uv` for package and virtual environment management."
  - "Do not use `print()` for application logs; use `logging` or structured logging such as `structlog`."
  - "Avoid broad `except Exception:` blocks that do not log the stack trace."
  - "Never commit hardcoded secrets, API keys, or database credentials."
  - "Always check whether `LOCAL_CA_BUNDLE`, `PIP_CACHE_DIR`, and `PYTHON3**_HOME` (e.g. `PYTHON311_HOME`, `PYTHON312_HOME`, `PYTHON313_HOME`) are set. If they are, use them."
tools:
  - bash
created_at: 2026-05-30
updated_at: 2026-07-29
---

# Python development guidelines

## 1. Style & formatting
- Follow **PEP 8**.
- Use automated tooling: **Ruff**, **Black**, **isort**.
- Type-hint arguments, variables, and returns (PEP 484); check with `mypy`.

## 2. Dependency management
- Declare dependencies explicitly.
- Prefer `pyproject.toml`; fall back to `requirements.txt`, `Pipfile`, or poetry
  to match the existing project.
- Always isolate in a virtual environment.
- Pin dependencies in production for deterministic builds.

## 3. Architecture & layout
- Prefer the `src/` layout (`src/my_package/`) for packaging and isolation.
- Group logic by domain or feature; avoid god files.

## 4. Testing
- **pytest** for all unit testing.
- Test files prefixed `test_`, in a root-level `tests/` directory.
- Cover edge cases, not just the happy path.

## 5. Documentation
- Docstrings on all public modules, classes, and functions, Google-style.
- Maintain a descriptive `README.md` covering setup and execution.

## 6. Logging & error handling
- Use `logging` or `structlog`; never `print` in production code.
- Create custom exception classes for domain-specific errors.
- Log context and stack traces when catching exceptions.

## 7. Vulnerability management
- Scan dependencies with `safety` or `pip-audit`.
- Run SAST with `bandit`.
- Keep dependencies current; with `uv`, periodically update to patch vulnerable
  transitive dependencies.

## 8. API & web development
- **FastAPI** as the default web framework, served by **Uvicorn** or another ASGI server.
- **Pydantic** for validation, serialization, and settings.
- Check for an existing **OpenAPI schema** first — if one exists, build strictly
  to that contract.
