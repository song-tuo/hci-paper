#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-codex}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
SOURCE="$ROOT/skills/hci-spine"

case "$TARGET" in
  codex) BASE="${CODEX_HOME:-$HOME/.codex}/skills" ;;
  claude) BASE="$HOME/.claude/skills" ;;
  *) echo "Usage: bash install.sh {codex|claude}" >&2; exit 2 ;;
esac

DEST="$BASE/hci-spine"
if [ -e "$DEST" ]; then
  echo "Refusing to overwrite existing installation: $DEST" >&2
  echo "Move or back it up, then run the installer again." >&2
  exit 1
fi

mkdir -p "$BASE"
cp -R "$SOURCE" "$DEST"
echo "Installed hci-spine at: $DEST"
