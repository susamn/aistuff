#!/usr/bin/env bash
# run-report.sh — repo-reliability runner
# Discovers pointers/*/, runs every eligible pointer against a repo, stores the
# project bundle in mosaic's centralized data home, and refreshes the
# dashboard's manifest.json so the mosaic webapp can pick it up.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export RR_LIB="$SKILL_DIR/scripts"
BUILD="python3 $SKILL_DIR/scripts/rr_build.py"
CONFIG_DIR="$HOME/.config/skill-config/repo-reliability"
CONFIG_FILE="$CONFIG_DIR/skill.properties"

# mosaic's fixed, install-independent staging paths — never a path relative
# to wherever mosaic itself happens to be installed on this machine. See
# skill-creator/references/data-app-skills.md.
MOSAIC_APPS_ROOT="${MOSAIC_APPS_DIR:-$HOME/.local/share/mosaic/apps}"
MOSAIC_DATA_ROOT="${MOSAIC_DATA_HOME:-$HOME/.local/share/mosaic/data}"
RR_MOSAIC_DATA="$MOSAIC_DATA_ROOT/repo-reliability"
MOSAIC_PORT="${MOSAIC_PORT:-47500}"

usage() {
  cat <<EOF
Usage: run-report.sh [options]
  --repo <path|url>   Repo to analyze (local path, or https/ssh URL to clone). Default: cwd
  --months <n>        Analysis window in months (default from config)
  --render-only       Skip analysis; rebuild data/manifest.json from the existing data store
  --validate <dir>    Run one pointer folder standalone and validate its envelope, then exit
  --no-forge          Skip forge (GitHub) pointers even if gh is available
  --open              Open the mosaic dashboard tile for this app when done (mosaic must be running)
EOF
  exit 1
}

# ── config ────────────────────────────────────────────────────────────────────
if [[ ! -f "$CONFIG_FILE" ]]; then
  mkdir -p "$CONFIG_DIR"
  cat > "$CONFIG_FILE" <<'EOF'
# repo-reliability configuration
# data_home: where clones of URL-analyzed repos are cached (project bundles and
# the manifest live in mosaic's own data home, not here — see the data-app
# contract in skill-creator/references/data-app-skills.md)
data_home=~/.local/share/repo-reliability
# window_months: analysis window for time-boxed pointers
window_months=12
# forge_pr_limit: max PRs fetched from GitHub per run
forge_pr_limit=300
# forge_issue_limit: max issues fetched per state per run
forge_issue_limit=300
# mosaic_onboarded: set once webapp/ has been symlinked into mosaic's apps
# staging dir and webapp/data into mosaic's central data dir — skip re-doing
# it every run once true (re-running is harmless, just unnecessary)
mosaic_onboarded=false
EOF
  echo "[config] Created $CONFIG_FILE with defaults (data_home, window_months, forge limits, mosaic_onboarded)."
fi
prop() { grep -E "^$1=" "$CONFIG_FILE" | tail -1 | cut -d= -f2- || true; }
DATA_HOME="$(eval echo "$(prop data_home)")"
WINDOW_MONTHS="$(prop window_months)"
PR_LIMIT="$(prop forge_pr_limit)"
ISSUE_LIMIT="$(prop forge_issue_limit)"
MOSAIC_ONBOARDED="$(prop mosaic_onboarded)"
if [[ -z "$MOSAIC_ONBOARDED" ]]; then
  # upgrading from a pre-mosaic config that predates this property
  echo "mosaic_onboarded=false" >> "$CONFIG_FILE"
  MOSAIC_ONBOARDED="false"
  echo "[config] Added missing 'mosaic_onboarded' property (default: false)"
fi
echo "[config] Loaded: data_home=$DATA_HOME window_months=$WINDOW_MONTHS forge_pr_limit=$PR_LIMIT forge_issue_limit=$ISSUE_LIMIT"

# ── onboard into mosaic (idempotent; gated on config so it's cheap after the
#    first run) ───────────────────────────────────────────────────────────────
mkdir -p "$RR_MOSAIC_DATA"  # hard requirement: create defensively, never assume mosaic or its onboarding has run
if [[ "$MOSAIC_ONBOARDED" != "true" ]]; then
  mkdir -p "$MOSAIC_APPS_ROOT"
  ln -sfn "$SKILL_DIR/webapp" "$MOSAIC_APPS_ROOT/repo-reliability"
  ln -sfn "$RR_MOSAIC_DATA" "$SKILL_DIR/webapp/data"
  if grep -q '^mosaic_onboarded=' "$CONFIG_FILE"; then
    sed -i 's/^mosaic_onboarded=.*/mosaic_onboarded=true/' "$CONFIG_FILE"
  else
    echo "mosaic_onboarded=true" >> "$CONFIG_FILE"
  fi
  echo "[mosaic] Onboarded: apps/repo-reliability -> $SKILL_DIR/webapp, webapp/data -> $RR_MOSAIC_DATA"
fi

# ── args ──────────────────────────────────────────────────────────────────────
REPO="$PWD"; RENDER_ONLY=0; NO_FORGE=0; OPEN=0; VALIDATE_DIR=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --months) WINDOW_MONTHS="$2"; shift 2 ;;
    --render-only) RENDER_ONLY=1; shift ;;
    --validate) VALIDATE_DIR="$2"; shift 2 ;;
    --no-forge) NO_FORGE=1; shift ;;
    --open) OPEN=1; shift ;;
    *) usage ;;
  esac
done
export RR_WINDOW_MONTHS="$WINDOW_MONTHS"

open_dashboard() {
  [[ $OPEN -eq 1 ]] && xdg-open "http://localhost:$MOSAIC_PORT/mosaic/apps/repo-reliability/" >/dev/null 2>&1 || true
}

# ── validate mode ─────────────────────────────────────────────────────────────
if [[ -n "$VALIDATE_DIR" ]]; then
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  REPO_DIR="$REPO" bash "$VALIDATE_DIR/run.sh" > "$TMP"
  if $BUILD validate "$TMP"; then
    echo "[validate] OK: $(basename "$VALIDATE_DIR") emits a valid envelope"
  else
    echo "[validate] FAILED: $(basename "$VALIDATE_DIR")"; exit 1
  fi
  exit 0
fi

# ── render-only mode ──────────────────────────────────────────────────────────
if [[ $RENDER_ONLY -eq 1 ]]; then
  $BUILD manifest "$RR_MOSAIC_DATA"
  open_dashboard
  exit 0
fi

# ── resolve repo (clone if URL) ───────────────────────────────────────────────
if [[ "$REPO" =~ ^(https?://|git@) ]]; then
  CLONE_SLUG="$(basename "${REPO%.git}" | tr -cd 'A-Za-z0-9._-')"
  CLONE_DIR="$DATA_HOME/clones/$CLONE_SLUG"
  if [[ -d "$CLONE_DIR/.git" ]]; then
    echo "[repo] Updating existing clone $CLONE_DIR"
    git -C "$CLONE_DIR" fetch -q && git -C "$CLONE_DIR" pull -q --ff-only || true
  else
    echo "[repo] Cloning $REPO"
    git clone -q "$REPO" "$CLONE_DIR"
  fi
  REPO="$CLONE_DIR"
fi
REPO="$(cd "$REPO" && pwd)"
git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1 || { echo "[error] $REPO is not a git repository"; exit 1; }
export REPO_DIR="$REPO"
echo "[repo] Analyzing $REPO"

# ── forge cache (one API pull shared by all forge pointers) ───────────────────
RUN_TMP="$(mktemp -d)"
trap 'rm -rf "$RUN_TMP"' EXIT
FORGE_OK=0
REMOTE="$(git -C "$REPO" config --get remote.origin.url 2>/dev/null || true)"
if [[ $NO_FORGE -eq 0 && "$REMOTE" =~ github\.com[:/]([^/]+)/([^/]+?)(\.git)?$ ]]; then
  GH_REPO="${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
  if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
    echo "[forge] Fetching PR/issue data for $GH_REPO (limits: $PR_LIMIT PRs, $ISSUE_LIMIT issues/state)"
    mkdir -p "$RUN_TMP/forge"
    PR_FIELDS="number,title,url,additions,deletions,changedFiles,createdAt,mergedAt,state,author,comments,reviews"
    if gh pr list --repo "$GH_REPO" --state all --limit "$PR_LIMIT" --json "$PR_FIELDS" > "$RUN_TMP/forge/prs.json" 2>"$RUN_TMP/forge/err" \
       || gh pr list --repo "$GH_REPO" --state all --limit "$PR_LIMIT" --json "number,title,url,additions,deletions,changedFiles,createdAt,mergedAt,state,author" > "$RUN_TMP/forge/prs.json" 2>>"$RUN_TMP/forge/err"; then
      gh issue list --repo "$GH_REPO" --state open --limit "$ISSUE_LIMIT" --json "number,title,createdAt,updatedAt" > "$RUN_TMP/forge/issues_open.json" 2>>"$RUN_TMP/forge/err" || echo "[]" > "$RUN_TMP/forge/issues_open.json"
      gh issue list --repo "$GH_REPO" --state closed --limit "$ISSUE_LIMIT" --json "number,title,createdAt,updatedAt,closedAt" > "$RUN_TMP/forge/issues_closed.json" 2>>"$RUN_TMP/forge/err" || echo "[]" > "$RUN_TMP/forge/issues_closed.json"
      export RR_FORGE_CACHE="$RUN_TMP/forge"
      FORGE_OK=1
    else
      echo "[forge] PR fetch failed — forge pointers will report unavailable"
      sed 's/^/[forge]   /' "$RUN_TMP/forge/err" | head -3 || true
    fi
  else
    echo "[forge] gh CLI missing or not authenticated — forge pointers skipped"
  fi
else
  [[ $NO_FORGE -eq 1 ]] && echo "[forge] Skipped (--no-forge)" || echo "[forge] No GitHub remote detected — forge pointers skipped"
fi

# ── run pointers ──────────────────────────────────────────────────────────────
ENVELOPES=()
FAILED=()
while IFS= read -r PDIR; do
  ID="$(basename "$PDIR")"
  REQ="$(python3 -c "import json;print(' '.join(json.load(open('$PDIR/pointer.json')).get('requires',[])))")"
  if [[ " $REQ " == *" forge-cache "* && $FORGE_OK -eq 0 ]]; then
    echo "[skip] $ID (needs forge data)"
    continue
  fi
  OUT="$RUN_TMP/$ID.json"
  echo "[run ] $ID"
  if bash "$PDIR/run.sh" > "$OUT" 2>"$RUN_TMP/$ID.err" && $BUILD validate "$OUT"; then
    ENVELOPES+=("$OUT")
  else
    FAILED+=("$ID")
    echo "[fail] $ID — skipped (stderr below)"
    sed 's/^/       /' "$RUN_TMP/$ID.err" | head -5 || true
  fi
done < <(for d in "$SKILL_DIR"/pointers/*/; do
    b="$(basename "$d")"; [[ "$b" == _* ]] && continue
    o="$(python3 -c "import json;print(json.load(open('$d/pointer.json')).get('order',999))")"
    echo "$o $d"
  done | sort -n | cut -d' ' -f2-)

[[ ${#ENVELOPES[@]} -eq 0 ]] && { echo "[error] No pointer produced a valid envelope"; exit 1; }

# ── bundle + store + refresh manifest ──────────────────────────────────────────
$BUILD meta "$REPO" > "$RUN_TMP/meta.json"
SLUG="$(python3 -c "import json;print(json.load(open('$RUN_TMP/meta.json'))['slug'])")"
$BUILD bundle "$RUN_TMP/meta.json" "$RR_MOSAIC_DATA/$SLUG.json" "${ENVELOPES[@]}"
$BUILD manifest "$RR_MOSAIC_DATA"

echo
echo "[done] Project data : $RR_MOSAIC_DATA/$SLUG.json"
echo "[done] Dashboard    : http://localhost:$MOSAIC_PORT/mosaic/apps/repo-reliability/ (start mosaic first if not running)"
[[ ${#FAILED[@]} -gt 0 ]] && echo "[warn] Failed pointers: ${FAILED[*]}"
open_dashboard
exit 0
