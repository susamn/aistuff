#!/usr/bin/env bash
# fetch.sh — fetch candidate skill from git URL, local folder, or remote archive into a staging area.
# stdout: staging directory path (data only) · stderr: diagnostics
# exit 0 ok · 1 invalid source/download failure · 2 missing dependency

set -euo pipefail

die() { echo "error: $*" >&2; exit "${2:-1}"; }

need() {
  command -v "$1" >/dev/null 2>&1 || die "$1 command not found" 2
}

usage() {
  echo "usage: fetch.sh <source> [subpath]" >&2
  echo "  <source>   git URL (https://... or git@...), local directory path, or archive URL" >&2
  echo "  [subpath]  optional subdirectory inside repository/archive containing the skill" >&2
  exit 1
}

[[ $# -ge 1 ]] || usage
SOURCE="$1"
SUBPATH="${2:-}"

STAGING_BASE="/tmp/skill-importer-staging"
STAGING_DIR="${STAGING_BASE}/$(date +%s)_$$"
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"

if [[ -d "$SOURCE" ]]; then
  # Local directory
  cp -a "$SOURCE/." "$STAGING_DIR/"
elif [[ "$SOURCE" =~ ^(https://|git@|git://).*\.git$ ]] || [[ "$SOURCE" =~ ^https://github\.com/ ]]; then
  # Git repository
  need git
  git clone --depth 1 --quiet "$SOURCE" "$STAGING_DIR/repo" >&2
  if [[ -n "$SUBPATH" ]]; then
    [[ -d "$STAGING_DIR/repo/$SUBPATH" ]] || die "subpath '$SUBPATH' not found in repo"
    mv "$STAGING_DIR/repo/$SUBPATH"/* "$STAGING_DIR/"
    rm -rf "$STAGING_DIR/repo"
  else
    # If root contains SKILL.md or skills in subfolder
    if [[ ! -f "$STAGING_DIR/repo/SKILL.md" ]] && [[ -d "$STAGING_DIR/repo/skills" ]]; then
      # If repository has skills/ subfolder, copy contents
      mv "$STAGING_DIR/repo/skills"/* "$STAGING_DIR/" 2>/dev/null || mv "$STAGING_DIR/repo"/* "$STAGING_DIR/"
    else
      mv "$STAGING_DIR/repo"/* "$STAGING_DIR/" 2>/dev/null || true
      mv "$STAGING_DIR/repo"/.* "$STAGING_DIR/" 2>/dev/null || true
    fi
    rm -rf "$STAGING_DIR/repo"
  fi
elif [[ "$SOURCE" =~ ^https?://.*\.tar\.gz$ ]] || [[ "$SOURCE" =~ ^https?://.*\.tgz$ ]]; then
  # Tarball archive
  need curl; need tar
  curl -sSL "$SOURCE" | tar -xz -C "$STAGING_DIR" >&2
elif [[ "$SOURCE" =~ ^https?://.*\.zip$ ]]; then
  # Zip archive
  need curl; need unzip
  TMP_ZIP="${STAGING_DIR}/tmp.zip"
  curl -sSL "$SOURCE" -o "$TMP_ZIP" >&2
  unzip -q "$TMP_ZIP" -d "$STAGING_DIR" >&2
  rm -f "$TMP_ZIP"
else
  # Try simple curl download if it's a direct file URL (e.g. single SKILL.md)
  if [[ "$SOURCE" =~ ^https?:// ]]; then
    need curl
    curl -sSL "$SOURCE" -o "$STAGING_DIR/SKILL.md" >&2
  else
    die "unrecognized or non-existent source: $SOURCE"
  fi
fi

# Print the staging directory path
echo "$STAGING_DIR"
