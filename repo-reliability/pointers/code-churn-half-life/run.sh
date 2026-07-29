#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export POINTER_DIR="$DIR"
export REPO_DIR="${REPO_DIR:-$PWD}"
export PYTHONPATH="${RR_LIB:-$DIR/../../scripts}${PYTHONPATH:+:$PYTHONPATH}"
exec python3 "$DIR/pointer.py"
