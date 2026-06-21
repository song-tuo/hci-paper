#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SKILL="$ROOT/skills/hci-spine"

VALIDATOR="${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py"
if [ -f "$VALIDATOR" ]; then
  python3 "$VALIDATOR" "$SKILL"
else
  grep -q '^name: hci-spine$' "$SKILL/SKILL.md"
  grep -q '^description:' "$SKILL/SKILL.md"
fi

python3 -m py_compile "$SKILL"/scripts/*.py
bash -n "$SKILL"/scripts/*.sh "$ROOT/install.sh" "$ROOT/verify.sh"

for test_file in "$SKILL"/scripts/test_*.py; do
  python3 "$test_file"
done
for test_file in "$SKILL"/scripts/test_*.sh; do
  bash "$test_file"
done

echo "All bundled checks passed."
