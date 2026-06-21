#!/usr/bin/env bash
# Self-test for codex_review.sh — exercises arg handling, error paths, and binary
# resolution via --dry-run. Does NOT make a real Codex call. Run: bash test_codex_review.sh
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$DIR/codex_review.sh"
PASS=0; FAIL=0

check() { # name, expected_exit, actual_exit
  if [ "$2" = "$3" ]; then PASS=$((PASS+1)); echo "  ✓ $1"; else FAIL=$((FAIL+1)); echo "  ✗ $1 (expected exit $2, got $3)"; fi
}

echo "== codex_review.sh self-test =="

# syntax
bash -n "$SCRIPT"; check "syntax OK" 0 $?

# missing --prompt → exit 2
bash "$SCRIPT" --cd /tmp >/dev/null 2>&1; check "missing --prompt → 2" 2 $?

# nonexistent prompt file → exit 2
bash "$SCRIPT" --prompt /no/such/file.md >/dev/null 2>&1; check "nonexistent prompt → 2" 2 $?

# unknown arg → exit 2
bash "$SCRIPT" --bogus >/dev/null 2>&1; check "unknown arg → 2" 2 $?

# dry-run with a real prompt file → exit 0 (resolves binary, prints command, no Codex call)
TMP_PROMPT="$(mktemp)"; echo "test prompt" > "$TMP_PROMPT"
OUT="$(bash "$SCRIPT" --prompt "$TMP_PROMPT" --cd /tmp --dry-run 2>&1)"; rc=$?
check "dry-run → 0 (when a codex binary resolves)" 0 $rc
echo "$OUT" | grep -q "DRY-RUN" && echo "  ✓ dry-run printed the command" || echo "  ⚠ dry-run produced no DRY-RUN marker (codex binary may be absent on this host)"
rm -f "$TMP_PROMPT"

echo ""
echo "== $PASS passed, $FAIL failed =="
[ "$FAIL" = "0" ]
