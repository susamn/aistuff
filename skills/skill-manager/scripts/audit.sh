#!/usr/bin/env bash
# audit.sh — entrypoint contract for the skill audit.
# usage: audit.sh [skill-name ...] [--all]
# stdout: findings, one per line · stderr: counts and diagnostics
# exit 0 clean · 1 errors found · 2 cannot run
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
command -v python3 >/dev/null 2>&1 || { echo "error: python3 not found" >&2; exit 2; }
exec python3 "$SCRIPT_DIR/audit.py" "$@"
