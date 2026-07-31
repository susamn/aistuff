#!/usr/bin/env bash
# scaffold.sh — create a new skill directory from the template for its kind.
# stdout: created paths (data only). stderr: diagnostics.
# exit 0 ok · 1 refused (exists / bad input) · 2 cannot run
set -euo pipefail

SKILLS_DIR="${SKILLS_DIR:-$HOME/dotfiles/aistuff/skills}"
NAME=""; KIND=""; WEBAPP=0

die()  { echo "error: $*" >&2; exit "${2:-1}"; }
usage() {
  cat >&2 <<'EOF'
usage: scaffold.sh <name> --kind <guidance|pipeline|hybrid> [--webapp] [--skills-dir DIR]

  <name>     kebab-case, becomes the directory and the frontmatter `name`
  --kind     see skill-creator SKILL.md Step 0 — decides the generated shape
  --webapp   add a webapp/ skeleton for a mosaic dashboard tile — see
             references/data-app-skills.md. guidance skills can't take it.
EOF
  exit 1
}

[[ $# -ge 1 ]] || usage
NAME="$1"; shift
while [[ $# -gt 0 ]]; do
  case "$1" in
    --kind)       KIND="${2:-}"; shift 2 ;;
    --skills-dir) SKILLS_DIR="${2:-}"; shift 2 ;;
    --webapp)     WEBAPP=1; shift ;;
    -h|--help)    usage ;;
    *)            die "unknown argument: $1" ;;
  esac
done
[[ "$WEBAPP" -eq 1 && "$KIND" == "guidance" ]] && die "--webapp needs real output data — not valid with --kind guidance"

[[ "$NAME" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || die "name must be kebab-case: '$NAME'"
case "$KIND" in
  guidance|pipeline|hybrid) ;;
  "") die "--kind is required (guidance|pipeline|hybrid)" ;;
  *)  die "invalid --kind: '$KIND'" ;;
esac

[[ -d "$SKILLS_DIR" ]] || die "skills dir not found: $SKILLS_DIR" 2
DEST="$SKILLS_DIR/$NAME"
[[ -e "$DEST" ]] && die "already exists: $DEST"
[[ -e "$DEST.disabled" ]] && die "exists but is disabled: $DEST.disabled"

DATE="$(date +%F)"
mkdir -p "$DEST"

# ── frontmatter (shared) ─────────────────────────────────────────────────────
emit_frontmatter() {
  local extra_resources="$1" extra_tools="$2"
  cat <<EOF
---
name: $NAME
description: TODO one line — what it does, and "Use when <trigger>."
version: 0.1.0
kind: $KIND
triggers:
  - "TODO phrase a user would actually say"
intent: TODO
created_at: $DATE
updated_at: $DATE
guardrails:
  - TODO or delete this block
${extra_resources}tools:
  - bash
${extra_tools}---
EOF
}

case "$KIND" in
  guidance)
    mkdir -p "$DEST/references"
    { emit_frontmatter "" ""
      cat <<EOF

# ${NAME//-/ }

TODO: when this skill applies, in one or two sentences.

## Rules

Rules true for *every* invocation. Keep few and absolute; anything conditional
belongs in a reference.

- TODO

## Read next

| file | when |
|---|---|
| \`references/topic.md\` | TODO name the situation, not the contents |
EOF
    } > "$DEST/SKILL.md"
    cat > "$DEST/references/topic.md" <<EOF
# TODO topic

Loaded only when the task touches this topic. Rename this file.
EOF
    ;;

  pipeline|hybrid)
    mkdir -p "$DEST/scripts" "$DEST/references"
    { emit_frontmatter "resources:
  - <SKILL_PATH>/scripts/run.sh
  - <SKILL_PATH>/references/output.md
" ""
      cat <<EOF

# ${NAME//-/ }

TODO: when this skill applies, and what decision its output supports.

## Workflow

1. Run: \`<SKILL_PATH>/scripts/run.sh analyze <target>\` — prints the artifact path.
2. Read the digest: \`<SKILL_PATH>/scripts/run.sh summary <artifact>\`
3. Drill in only when a value looks wrong: \`run.sh verbose <artifact>\`. The
   artifact path is the last line of the summary.
4. Report findings with their evidence. Never present a value without it.
5. On failure, the script reports; **you** decide whether to retry, skip, fall
   back, or ask the user.

Output contract: \`references/output.md\`.

## Read next

| file | when |
|---|---|
| \`references/output.md\` | interpreting or extending the output |
EOF
    } > "$DEST/SKILL.md"

    cat > "$DEST/references/output.md" <<'EOF'
# Output contract (schema 1)

Artifact written to disk; the agent normally sees only the summary projection.

```json
{ "schema": 1, "id": "kebab-id", "status": "ok | error",
  "value": 0, "unit": "TODO", "band": "ok | warning | critical | unknown",
  "evidence": "commit hash / PR # / file path backing the value" }
```

Summary projection — one line per finding, last line is the artifact handle:

```
<id>   <band>   <value> <unit>   <evidence>
<artifact>: /abs/path/to/artifact.json
```

Failure shape. `remedy` only for failures the script recognizes (missing binary,
unauthenticated CLI, absent config key) — never a guess on an unexpected error:

```json
{ "status": "error", "id": "kebab-id", "reason": "one line, no stack",
  "log": "/abs/path/to/error.log", "remedy": "gh auth login" }
```

Recovery is the agent's decision, not the script's. Partial failure returns
partial results so the agent can see what succeeded before choosing.

Thresholds live in `scripts/thresholds.json`, never inline in code.
EOF

    cat > "$DEST/scripts/thresholds.json" <<'EOF'
{
  "example_metric": {
    "direction": "higher_is_worse",
    "warning": 5,
    "critical": 15
  }
}
EOF

    cat > "$DEST/scripts/run.sh" <<'EOF'
#!/usr/bin/env bash
# stdout: data only · stderr: diagnostics · exit 0 ok · 1 findings · 2 cannot run
# One entrypoint, several modes. Add a mode before you add a second script.
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"

usage() {
  echo "usage: run.sh analyze <target> | summary <artifact> | verbose <artifact>" >&2
  exit 1
}
need() {  # structured failure with a remedy — only for recognized cases
  command -v "$1" >/dev/null 2>&1 && return 0
  printf '{"status":"error","reason":"%s not found","remedy":"install %s"}\n' "$1" "$1"
  exit 2
}
[[ $# -ge 1 ]] || usage
MODE="$1"; shift

case "$MODE" in
  analyze)
    # TODO run the analysis, write the artifact to disk, print ONLY its path.
    echo "error: not implemented" >&2; exit 2 ;;

  summary)   # agent-facing projection: one line per finding, then the handle
    need jq
    ART="${1:-}"; [[ -f "$ART" ]] || { echo "error: no artifact: $ART" >&2; exit 2; }
    # TODO one line per finding — id, band, value, evidence. Nothing else.
    jq -r '"\(.id)\t\(.band)\t\(.value) \(.unit)\t\(.evidence)"' "$ART"
    echo "<artifact>: $ART" ;;

  verbose)   # full detail — only when a summary line looks wrong
    need jq
    ART="${1:-}"; [[ -f "$ART" ]] || { echo "error: no artifact: $ART" >&2; exit 2; }
    jq . "$ART" ;;

  *) usage ;;
esac
EOF
    chmod +x "$DEST/scripts/run.sh"
    ;;
esac

if [[ "$WEBAPP" -eq 1 ]]; then
  cat >> "$DEST/SKILL.md" <<EOF

## Steady state, once onboarded to mosaic

Once \`webapp/\` is onboarded (symlinked into mosaic's staging directory,
tracked by \`mosaic_onboarded\` in this skill's config), routine invocations
of this skill are data-producing runs only — they execute the generation
script, which writes new/updated data to \`~/.local/share/mosaic/data/$NAME/\`;
mosaic serves it automatically, no separate publish step. Modifying
\`webapp/app.json\`, \`webapp/static/\`, the onboarding symlink, or this
script's own logic is a distinct action, done only when the user explicitly
asks for it — never as a side effect of a routine run.
EOF

  mkdir -p "$DEST/webapp/static/js" "$DEST/webapp/static/css"
  cat > "$DEST/webapp/app.json" <<EOF
{
  "id": "$NAME",
  "name": "TODO Human name",
  "description": "TODO one line, shown on the mosaic dashboard tile",
  "version": "0.1.0",
  "entry": "index.html"
}
EOF
  cat > "$DEST/webapp/static/index.html" <<'EOF'
<!DOCTYPE html>
<html>
<head>
<title>TODO</title>
<link rel="stylesheet" href="css/style.css">
</head>
<body>
<h1>TODO</h1>
<script src="js/app.js"></script>
</body>
</html>
EOF
  cat > "$DEST/webapp/static/js/app.js" <<'EOF'
// Sub-paths under data/ are entirely up to this app. The generation script
// must write to ~/.local/share/mosaic/data/<id>/, creating it if missing —
// never assume mosaic or onboard.sh has run. See
// skill-creator/references/data-app-skills.md.
fetch("data/manifest.json").then((r) => r.json()).then((d) => {
  // TODO render into index.html's structure — fill the template, don't
  // build up an HTML string here.
  console.log(d);
});
EOF
  cat > "$DEST/webapp/static/css/style.css" <<'EOF'
/* TODO */
EOF
fi

echo "$DEST"
find "$DEST" -type f | sort | sed "s|^$DEST/|  |"

cat >&2 <<EOF

next:
  1. fill the TODOs in $DEST/SKILL.md (budget: 150 lines)
  2. register in $SKILLS_DIR/AGENTS-TEMPLATE.md
  3. bash ~/dotfiles/do-stow.sh
  4. $SKILLS_DIR/skill-manager/scripts/audit.sh $NAME
EOF
if [[ "$WEBAPP" -eq 1 ]]; then
  cat >&2 <<EOF
  5. fill webapp/app.json + webapp/static/{index.html,js/app.js,css/style.css}
  6. write your generation script directly to ~/.local/share/mosaic/data/$NAME/
  7. \$TOOLS_PATH/mosaic/scripts/onboard.sh $DEST/webapp   (never do-stow/do-unstow)
EOF
fi
