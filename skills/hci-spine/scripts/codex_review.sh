#!/usr/bin/env bash
# hci-spine Codex cross-model REVIEW leg (generic prompt) — MCP-independent.
# Thin wrapper over codex_lib.sh; takes a caller-written prompt file directly.
# (codex_role.sh is the higher-level dispatcher for the 4 named roles; this stays
# for the review gate's free-form prompts and for back-compat.)
#
# Usage: codex_review.sh --cd DIR --prompt FILE --out FILE [--model M] [--reasoning E] [--dry-run]
#
# Anti-anchoring (caller-enforced): the prompt holds the paper + questions ONLY,
# never the Claude panel verdict. Merge Codex-only findings; never average.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
. "$DIR/codex_lib.sh"

MODEL="gpt-5.5"; REASONING="high"; CD_DIR="$PWD"; PROMPT_FILE=""; OUT_FILE="hci_spine_output/codex_review_raw.md"; DRY=0
while [ $# -gt 0 ]; do case "$1" in
  --cd) CD_DIR="$2"; shift 2;; --prompt) PROMPT_FILE="$2"; shift 2;; --out) OUT_FILE="$2"; shift 2;;
  --model) MODEL="$2"; shift 2;; --reasoning) REASONING="$2"; shift 2;; --dry-run) DRY=1; shift;;
  *) echo "unknown arg: $1" >&2; exit 2;; esac; done

if [ -z "$PROMPT_FILE" ] || [ ! -f "$PROMPT_FILE" ]; then
  echo "ERROR: --prompt <file> required and must exist." >&2; exit 2
fi

hci_run_codex "$PROMPT_FILE" "$CD_DIR" "$OUT_FILE" "$MODEL" "$REASONING" "-" "$DRY"
