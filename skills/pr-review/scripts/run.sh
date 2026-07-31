#!/usr/bin/env bash
# run.sh — pr-review data-app runner.
# Modes: fetch | persist-chunk | set-verdict | summary
# stdout: data only (tab-separated or one-line-per-record). stderr: diagnostics.
# exit 0 ok · 1 refused (bad input / validation) · 2 cannot run (missing dep)
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
CONFIG_DIR="$HOME/.config/skill-config/pr-review"
CONFIG_FILE="$CONFIG_DIR/skill.properties"

# mosaic's fixed, install-independent staging paths — see
# skill-creator/references/data-app-skills.md. Never a path relative to
# wherever mosaic itself happens to be installed on this machine.
MOSAIC_APPS_ROOT="${MOSAIC_APPS_DIR:-$HOME/.local/share/mosaic/apps}"
MOSAIC_DATA_ROOT="${MOSAIC_DATA_HOME:-$HOME/.local/share/mosaic/data}"
DATA_HOME="$MOSAIC_DATA_ROOT/pr-review"
MANIFEST="$DATA_HOME/manifest.json"
SCRATCH_ROOT="${PR_REVIEW_SCRATCH:-/tmp/pr-review}"

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'
YELLOW='\033[1;33m'; BOLD='\033[1m'; RESET='\033[0m'
info()    { echo -e "${CYAN}${BOLD}[info]${RESET}  $*" >&2; }
success() { echo -e "${GREEN}${BOLD}[done]${RESET}  $*" >&2; }
warn()    { echo -e "${YELLOW}${BOLD}[warn]${RESET}  $*" >&2; }
die()     { echo -e "${RED}${BOLD}[error]${RESET} $1" >&2; exit "${2:-1}"; }
now()     { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

command -v jq >/dev/null 2>&1 || die "'jq' is not installed." 2

# ── onboard into mosaic (idempotent; gated on config so it's cheap after the
#    first run) ────────────────────────────────────────────────────────────
mkdir -p "$DATA_HOME"
[[ -f "$MANIFEST" ]] || echo '{"schema":1,"datasets":[]}' > "$MANIFEST"
if [[ ! -f "$CONFIG_FILE" ]]; then
  mkdir -p "$CONFIG_DIR"
  cat > "$CONFIG_FILE" <<'EOF'
# pr-review configuration
# mosaic_onboarded: set once webapp/ has been symlinked into mosaic's apps
# staging dir and webapp/data into mosaic's central data dir — skip re-doing
# it every run once true (re-running is harmless, just unnecessary)
mosaic_onboarded=false
EOF
fi
prop() { grep -E "^$1=" "$CONFIG_FILE" | tail -1 | cut -d= -f2- || true; }
if [[ "$(prop mosaic_onboarded)" != "true" ]]; then
  mkdir -p "$MOSAIC_APPS_ROOT"
  ln -sfn "$SKILL_DIR/webapp" "$MOSAIC_APPS_ROOT/pr-review"
  ln -sfn "$DATA_HOME" "$SKILL_DIR/webapp/data"
  if grep -q '^mosaic_onboarded=' "$CONFIG_FILE"; then
    sed -i 's/^mosaic_onboarded=.*/mosaic_onboarded=true/' "$CONFIG_FILE"
  else
    echo "mosaic_onboarded=true" >> "$CONFIG_FILE"
  fi
  info "Onboarded into mosaic: apps/pr-review -> $SKILL_DIR/webapp"
fi

MODE="${1:-}"; shift || true
CATEGORIES='["correctness","code-quality","security","performance","resource-leak","concurrency","test-coverage","maintainability","dependency"]'
SEVERITIES='["must-fix","should-fix","suggestion"]'
SIDES='["LEFT","RIGHT"]'

case "$MODE" in

# ── fetch ─────────────────────────────────────────────────────────────────
fetch)
  usage_fetch() {
    cat >&2 <<'EOF'
usage: run.sh fetch <PR_URL> [-s <story_file>] [--pr-json <file> --diff <file>]
  --pr-json/--diff bypass gh entirely (fixture/offline testing); both required together.
EOF
    exit 1
  }

  STORY_FILE=""; FIXTURE_JSON=""; FIXTURE_DIFF=""; PR_URL=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -s) STORY_FILE="${2:-}"; shift 2 ;;
      --pr-json) FIXTURE_JSON="${2:-}"; shift 2 ;;
      --diff) FIXTURE_DIFF="${2:-}"; shift 2 ;;
      -h|--help) usage_fetch ;;
      *) [[ -z "$PR_URL" ]] && PR_URL="$1" || die "unexpected argument: $1"; shift ;;
    esac
  done
  [[ -n "$PR_URL" ]] || usage_fetch

  if [[ -n "$FIXTURE_JSON" || -n "$FIXTURE_DIFF" ]]; then
    [[ -n "$FIXTURE_JSON" && -n "$FIXTURE_DIFF" ]] || die "--pr-json and --diff must be given together"
    [[ -f "$FIXTURE_JSON" ]] || die "fixture PR json not found: $FIXTURE_JSON"
    [[ -f "$FIXTURE_DIFF" ]] || die "fixture diff not found: $FIXTURE_DIFF"
  else
    command -v gh >/dev/null 2>&1 || die "'gh' (GitHub CLI) is not installed. https://cli.github.com" 2
  fi

  PR_URL_CLEAN="${PR_URL#https://}"; PR_URL_CLEAN="${PR_URL_CLEAN#http://}"
  IFS='/' read -ra URL_PARTS <<< "$PR_URL_CLEAN"
  [[ ${#URL_PARTS[@]} -ge 5 && "${URL_PARTS[3]}" == "pull" ]] \
    || die "Could not parse PR URL. Expected: https://github.com/owner/repo/pull/NUMBER"
  OWNER="${URL_PARTS[1]}"; REPO="${URL_PARTS[2]}"; PR_NUMBER="${URL_PARTS[4]}"
  REPO_SLUG="${OWNER}/${REPO}"
  REVIEW_ID="$(printf '%s' "${OWNER}_${REPO}_${PR_NUMBER}" | tr -c 'a-zA-Z0-9_' '-' | tr '[:upper:]' '[:lower:]')"

  if [[ -n "$FIXTURE_JSON" ]]; then
    info "Using fixture PR data (offline mode) for ${REPO_SLUG}#${PR_NUMBER}"
    PR_JSON="$(cat "$FIXTURE_JSON")"
    PR_DIFF="$(cat "$FIXTURE_DIFF")"
  else
    info "Fetching PR #${PR_NUMBER} from ${REPO_SLUG} …"
    PR_JSON=$(gh pr view "$PR_URL" \
      --json number,title,body,author,baseRefName,headRefName,additions,deletions,changedFiles,labels,commits,files \
      2>/dev/null) || die "Failed to fetch PR metadata. Check the URL and 'gh auth status'."
    info "Fetching PR diff …"
    PR_DIFF=$(gh pr diff "$PR_URL" 2>/dev/null) || die "Failed to fetch diff. Ensure you have read access to the repo."
  fi
  jq -e . <<< "$PR_JSON" >/dev/null 2>&1 || die "PR JSON is not valid JSON"

  PR_TITLE=$(jq -r '.title' <<< "$PR_JSON")
  PR_AUTHOR=$(jq -r '.author.login' <<< "$PR_JSON")
  BASE_BRANCH=$(jq -r '.baseRefName' <<< "$PR_JSON")
  HEAD_BRANCH=$(jq -r '.headRefName' <<< "$PR_JSON")
  ADDITIONS=$(jq -r '.additions' <<< "$PR_JSON")
  DELETIONS=$(jq -r '.deletions' <<< "$PR_JSON")
  CHANGED_FILES=$(jq -r '.changedFiles' <<< "$PR_JSON")

  STORY=""
  if [[ -n "$STORY_FILE" ]]; then
    [[ -f "$STORY_FILE" ]] || die "Story file not found: $STORY_FILE"
    STORY="$(cat "$STORY_FILE")"
    info "Story loaded from: $STORY_FILE"
  elif [[ -t 0 ]]; then
    echo -e "${CYAN}${BOLD}Paste the user story / ticket description below.${RESET}" >&2
    echo -e "${YELLOW}(Press Ctrl+D on a new line when done)${RESET}" >&2
    STORY=$(cat) || true
  else
    warn "No story file given and stdin is not interactive — skipping story context."
  fi

  info "Chunking diff …"
  SCRATCH_DIR="$SCRATCH_ROOT/$REVIEW_ID/chunks"
  rm -rf "$SCRATCH_DIR"
  mkdir -p "$SCRATCH_DIR"
  MAX_CHUNK_SIZE="${MAX_CHUNK_SIZE:-102400}"
  awk -v outdir="$SCRATCH_DIR" -v max_size="$MAX_CHUNK_SIZE" '
    BEGIN { chunk_id = 1; size = 0; buf = "" }
    /^diff --git / {
      if (size > 0 && (size + length($0) > max_size)) {
        f = outdir "/chunk_" chunk_id ".diff"; printf "%s", buf > f; close(f)
        chunk_id++; size = 0; buf = ""
      }
    }
    { buf = buf $0 "\n"; size += length($0) + 1 }
    END { if (size > 0) { f = outdir "/chunk_" chunk_id ".diff"; printf "%s", buf > f; close(f) } }
  ' <<< "$PR_DIFF"
  CHUNK_COUNT=$(find "$SCRATCH_DIR" -maxdepth 1 -name 'chunk_*.diff' | wc -l | xargs)
  [[ "$CHUNK_COUNT" -gt 0 ]] || warn "No diff hunks found — nothing to review."

  META_DIR="$DATA_HOME/$REVIEW_ID"
  mkdir -p "$META_DIR"
  TIMESTAMP="$(now)"
  CREATED_AT="$TIMESTAMP"
  [[ -f "$META_DIR/meta.json" ]] && CREATED_AT="$(jq -r '.created_at' "$META_DIR/meta.json")"
  rm -f "$META_DIR"/chunk_*.json  # re-fetching a PR invalidates any prior per-chunk reviews

  # Write a diff-only stub for every chunk immediately, not just the ones
  # that have been reviewed — so a large PR's pages are all browsable while
  # review is still in progress. persist-chunk fills in findings later on
  # top of the same file. files[] is derived mechanically here (total
  # operation), not left for the agent to report.
  info "Writing ${CHUNK_COUNT} chunk stub(s) …"
  N=1
  while [[ -f "$SCRATCH_DIR/chunk_${N}.diff" ]]; do
    CHUNK_FILES=$(grep -Eo '^diff --git a/.* b/.*' "$SCRATCH_DIR/chunk_${N}.diff" \
      | sed -e 's|^diff --git a/||' -e 's| b/.*||' | jq -R . | jq -sc .)
    jq -n --argjson chunk "$N" --arg diff "$(cat "$SCRATCH_DIR/chunk_${N}.diff")" --argjson files "$CHUNK_FILES" \
      '{schema: 1, chunk: $chunk, files: $files, diff: $diff, findings: [], reviewed: false, reviewed_at: null}' \
      > "$META_DIR/chunk_${N}.json"
    N=$((N+1))
  done

  jq -n \
    --arg review_id "$REVIEW_ID" --arg repo "$REPO_SLUG" --argjson pr_number "$PR_NUMBER" \
    --arg url "$PR_URL" --arg title "$PR_TITLE" --arg author "$PR_AUTHOR" \
    --arg base_branch "$BASE_BRANCH" --arg head_branch "$HEAD_BRANCH" \
    --argjson additions "$ADDITIONS" --argjson deletions "$DELETIONS" --argjson changed_files "$CHANGED_FILES" \
    --argjson labels "$(jq -c '[(.labels // [])[].name]' <<< "$PR_JSON")" \
    --argjson commits "$(jq -c '[(.commits // [])[].messageHeadline]' <<< "$PR_JSON")" \
    --argjson files "$(jq -c '[(.files // [])[] | {path, additions, deletions}]' <<< "$PR_JSON")" \
    --arg story "$STORY" --argjson chunk_count "$CHUNK_COUNT" \
    --arg created_at "$CREATED_AT" --arg updated_at "$TIMESTAMP" \
    '{schema: 1, review_id: $review_id, repo: $repo, pr_number: $pr_number, url: $url,
      title: $title, author: $author, base_branch: $base_branch, head_branch: $head_branch,
      additions: $additions, deletions: $deletions, changed_files: $changed_files,
      labels: $labels, commits: $commits, files: $files, story: $story,
      chunk_count: $chunk_count, chunks_reviewed: 0,
      status: "pending_review", verdict: null,
      created_at: $created_at, updated_at: $updated_at}' \
    > "$META_DIR/meta.json"

  jq --argjson entry "$(jq -n \
      --arg id "$REVIEW_ID" --arg generated_at "$TIMESTAMP" --arg repo "$REPO_SLUG" \
      --argjson pr_number "$PR_NUMBER" --arg title "$PR_TITLE" --arg author "$PR_AUTHOR" \
      --arg updated_at "$TIMESTAMP" \
      '{id: $id, generated_at: $generated_at, schema_version: 1, tier: "hot",
        repo: $repo, pr_number: $pr_number, title: $title, author: $author,
        status: "pending_review", verdict: null, must_fix: 0, should_fix: 0, suggestions: 0,
        updated_at: $updated_at}')" \
    '.datasets = ([.datasets[] | select(.id != $entry.id)] + [$entry])' \
    "$MANIFEST" > "$MANIFEST.tmp" && mv "$MANIFEST.tmp" "$MANIFEST"

  success "Review ${REVIEW_ID}: ${CHUNK_COUNT} chunk(s) ready in ${SCRATCH_DIR}"
  printf 'review_id\t%s\nscratch_dir\t%s\nchunks\t%s\nmeta\t%s\n' \
    "$REVIEW_ID" "$SCRATCH_DIR" "$CHUNK_COUNT" "$META_DIR/meta.json"
  ;;

# ── persist-chunk ────────────────────────────────────────────────────────
persist-chunk)
  REVIEW_ID="${1:-}"; CHUNK_N="${2:-}"; FINDINGS_FILE="${3:-}"
  [[ -n "$REVIEW_ID" && -n "$CHUNK_N" && -n "$FINDINGS_FILE" ]] \
    || die "usage: run.sh persist-chunk <review_id> <chunk_n> <findings_file>"
  META_DIR="$DATA_HOME/$REVIEW_ID"
  META_FILE="$META_DIR/meta.json"
  CHUNK_FILE="$META_DIR/chunk_${CHUNK_N}.json"
  [[ -f "$META_FILE" ]] || die "no such review: $REVIEW_ID (run fetch first)"
  [[ -f "$CHUNK_FILE" ]] || die "no such chunk: $CHUNK_N (run fetch first, or check the chunk number)"
  [[ -f "$FINDINGS_FILE" ]] || die "findings file not found: $FINDINGS_FILE"
  jq -e . "$FINDINGS_FILE" >/dev/null 2>&1 || die "findings file is not valid JSON: $FINDINGS_FILE"

  VALID=$(jq --argjson cats "$CATEGORIES" --argjson sevs "$SEVERITIES" --argjson sides "$SIDES" -r '
    (.findings | type == "array") and
    ([.findings[] |
      (.category as $c | ($cats | index($c)) != null) and
      (.severity as $s | ($sevs | index($s)) != null) and
      (.side as $sd | ($sides | index($sd)) != null) and
      (.line | type == "number") and
      (.file | type == "string") and (.comment | type == "string")
    ] | all)
  ' "$FINDINGS_FILE")
  [[ "$VALID" == "true" ]] || die "findings file failed schema validation (bad category/severity/side/line/file/comment): $FINDINGS_FILE"

  TIMESTAMP="$(now)"
  jq --slurpfile findings_doc "$FINDINGS_FILE" --arg reviewed_at "$TIMESTAMP" \
    '.findings = $findings_doc[0].findings | .reviewed = true | .reviewed_at = $reviewed_at' \
    "$CHUNK_FILE" > "$CHUNK_FILE.tmp" && mv "$CHUNK_FILE.tmp" "$CHUNK_FILE"
  info "Persisted chunk $CHUNK_N for $REVIEW_ID"

  CHUNK_COUNT=$(jq -r '.chunk_count' "$META_FILE")
  CHUNKS_REVIEWED=$(jq -s '[.[] | select(.reviewed == true)] | length' "$META_DIR"/chunk_*.json)
  STATUS="in_progress"
  [[ "$CHUNKS_REVIEWED" -ge "$CHUNK_COUNT" ]] && STATUS="awaiting_verdict"

  jq --argjson n "$CHUNKS_REVIEWED" --arg status "$STATUS" --arg updated_at "$TIMESTAMP" \
    '.chunks_reviewed = $n | .status = $status | .updated_at = $updated_at' \
    "$META_FILE" > "$META_FILE.tmp" && mv "$META_FILE.tmp" "$META_FILE"

  MUST_FIX=$(jq -s '[.[].findings[] | select(.severity=="must-fix")] | length' "$META_DIR"/chunk_*.json)
  SHOULD_FIX=$(jq -s '[.[].findings[] | select(.severity=="should-fix")] | length' "$META_DIR"/chunk_*.json)
  SUGGESTIONS=$(jq -s '[.[].findings[] | select(.severity=="suggestion")] | length' "$META_DIR"/chunk_*.json)
  jq --arg id "$REVIEW_ID" --arg status "$STATUS" --arg updated_at "$TIMESTAMP" \
     --argjson must "$MUST_FIX" --argjson should "$SHOULD_FIX" --argjson sugg "$SUGGESTIONS" \
    '.datasets |= map(if .id == $id then
        .status = $status | .must_fix = $must | .should_fix = $should | .suggestions = $sugg | .updated_at = $updated_at
      else . end)' \
    "$MANIFEST" > "$MANIFEST.tmp" && mv "$MANIFEST.tmp" "$MANIFEST"

  FINDINGS_N=$(jq '.findings | length' "$META_DIR/chunk_${CHUNK_N}.json")
  printf 'chunk\t%s\nstatus\t%s\nchunks_reviewed\t%s/%s\nfindings\t%s\n' \
    "$CHUNK_N" "$STATUS" "$CHUNKS_REVIEWED" "$CHUNK_COUNT" "$FINDINGS_N"
  ;;

# ── set-verdict ───────────────────────────────────────────────────────────
set-verdict)
  REVIEW_ID="${1:-}"; VERDICT="${2:-}"
  [[ -n "$REVIEW_ID" && -n "$VERDICT" ]] \
    || die "usage: run.sh set-verdict <review_id> <APPROVE|REQUEST_CHANGES|NEEDS_DISCUSSION>"
  case "$VERDICT" in APPROVE|REQUEST_CHANGES|NEEDS_DISCUSSION) ;; *) die "invalid verdict: $VERDICT" ;; esac
  META_FILE="$DATA_HOME/$REVIEW_ID/meta.json"
  [[ -f "$META_FILE" ]] || die "no such review: $REVIEW_ID"
  CHUNK_COUNT=$(jq -r '.chunk_count' "$META_FILE")
  CHUNKS_REVIEWED=$(jq -r '.chunks_reviewed' "$META_FILE")
  [[ "$CHUNKS_REVIEWED" -ge "$CHUNK_COUNT" ]] \
    || die "not all chunks reviewed yet ($CHUNKS_REVIEWED/$CHUNK_COUNT) — review every chunk before setting a verdict"

  TIMESTAMP="$(now)"
  jq --arg v "$VERDICT" --arg updated_at "$TIMESTAMP" '.verdict = $v | .status = "reviewed" | .updated_at = $updated_at' \
    "$META_FILE" > "$META_FILE.tmp" && mv "$META_FILE.tmp" "$META_FILE"
  jq --arg id "$REVIEW_ID" --arg v "$VERDICT" --arg updated_at "$TIMESTAMP" \
    '.datasets |= map(if .id == $id then .verdict = $v | .status = "reviewed" | .updated_at = $updated_at else . end)' \
    "$MANIFEST" > "$MANIFEST.tmp" && mv "$MANIFEST.tmp" "$MANIFEST"

  success "Review $REVIEW_ID: verdict $VERDICT"
  printf 'status\treviewed\nverdict\t%s\n<artifact>\t%s\n' "$VERDICT" "$META_FILE"
  ;;

# ── summary (mandatory script→agent projection) ──────────────────────────
summary)
  REVIEW_ID="${1:-}"
  if [[ -z "$REVIEW_ID" ]]; then
    jq -r '.datasets | sort_by(.updated_at) | reverse | .[] |
      "\(.id)\t\(.status)\t\(.verdict // "pending")\t\(.must_fix) must-fix, \(.should_fix) should-fix, \(.suggestions) suggestions\t\(.repo)#\(.pr_number) \(.title)"' \
      "$MANIFEST"
    echo "<artifact>: $MANIFEST"
  else
    META_DIR="$DATA_HOME/$REVIEW_ID"
    [[ -d "$META_DIR" ]] || die "no such review: $REVIEW_ID"
    if compgen -G "$META_DIR/chunk_*.json" > /dev/null; then
      jq -s -r '[.[] | .findings[] as $f | "\($f.category)\t\($f.severity)\t\($f.file):\($f.line) (\($f.side))\t\($f.comment)"] | .[]' \
        "$META_DIR"/chunk_*.json
    fi
    echo "<artifact>: $META_DIR/meta.json"
  fi
  ;;

*) die "usage: run.sh <fetch|persist-chunk|set-verdict|summary> ... (mode was: '${MODE}')" ;;
esac
