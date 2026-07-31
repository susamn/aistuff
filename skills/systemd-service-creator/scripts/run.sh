#!/usr/bin/env bash
# systemd-service-creator run.sh
# stdout: data only · stderr: diagnostics · exit 0 ok · 1 findings · 2 cannot run
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
PYTHON_EXEC="python3"

usage() {
  echo "usage: run.sh analyze | summary <artifact> | verbose <artifact> | manage <args...>" >&2
  exit 1
}

need() {
  command -v "$1" >/dev/null 2>&1 && return 0
  printf '{"status":"error","reason":"%s not found","remedy":"install %s"}\n' "$1" "$1"
  exit 2
}

[[ $# -ge 1 ]] || usage
MODE="$1"; shift

case "$MODE" in
  analyze)
    need python3
    ART="/tmp/systemd_service_creator_artifact.json"
    "$PYTHON_EXEC" "$SKILL_DIR/scripts/manage.py" list --json > "$ART"
    echo "$ART"
    ;;

  summary)
    need jq
    ART="${1:-}"
    [[ -f "$ART" ]] || { echo "error: no artifact: $ART" >&2; exit 2; }
    jq -r '.units[] | "\(.unit)\t\(.state)"' "$ART" 2>/dev/null || echo "No personal units found."
    echo "<artifact>: $ART"
    ;;

  verbose)
    need jq
    ART="${1:-}"
    [[ -f "$ART" ]] || { echo "error: no artifact: $ART" >&2; exit 2; }
    jq . "$ART"
    ;;

  manage)
    exec "$PYTHON_EXEC" "$SKILL_DIR/scripts/manage.py" "$@"
    ;;

  *) usage ;;
esac
