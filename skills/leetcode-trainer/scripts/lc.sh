#!/usr/bin/env bash
# leetcode-trainer entrypoint. stdout: data only · stderr: diagnostics.
# exit 0 ok · 1 violations/missing · 2 could not run
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"

usage() {
  cat >&2 <<'EOF'
usage:
  lc.sh add <file>              validate + store a problem JSON, rebuild manifest
  lc.sh remove <slug>            delete a stored problem, rebuild manifest
  lc.sh validate <file>          schema check only, no write
  lc.sh list                     one line per stored problem + manifest handle
  lc.sh progress [top100.json]   diff stored problems against the checklist
                                  (defaults to references/top-100.json)
  lc.sh rebuild-manifest         recompute manifest.json from problems/ on disk
EOF
  exit 1
}

command -v python3 >/dev/null 2>&1 || {
  echo '{"status":"error","reason":"python3 not found","remedy":"install python3"}' >&2
  exit 2
}

[[ $# -ge 1 ]] || usage
MODE="$1"; shift

if [[ "$MODE" == "progress" && $# -eq 0 ]]; then
  set -- "$SKILL_DIR/references/top-100.json"
fi

exec python3 "$SKILL_DIR/scripts/lc_core.py" "$MODE" "$@"
