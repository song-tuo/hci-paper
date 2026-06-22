#!/usr/bin/env bash
# hci-spine unified Codex-role dispatcher — MCP-independent.
# Runs one of the four Codex roles as an independent, READ-ONLY pass:
#   review       prose peer review (anti-anchoring: paper-only)
#   dual_write   independent draft of ONE section (generator side of generator-evaluator)
#   cite_verify  structured citation existence + claim-support check (JSON via --output-schema)
#   data_audit   structured study-data / stats / coding honesty check (JSON via --output-schema)
#
# Usage:
#   codex_role.sh --role R --cd DIR --out OUT [--paper P] [--bib B] [--data D]
#                 [--claims C] [--section S] [--question Q] [--model M] [--reasoning E] [--dry-run]
#
# Standing rules (do not break): anti-anchoring — the prompt carries the paper +
# task only, NEVER the Claude panel's verdict or Claude's own draft. The caller
# merges Codex findings; it never averages.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
. "$DIR/codex_lib.sh"
ROLES_DIR="$DIR/../references/codex-roles"

ROLE="" CD_DIR="$PWD" OUT="" PAPER="" BIB="" DATA="" CLAIMS="" SECTION="" QUESTION=""
MODEL="gpt-5.5" REASONING="high" DRY=0
while [ $# -gt 0 ]; do case "$1" in
  --role) ROLE="$2"; shift 2;; --cd) CD_DIR="$2"; shift 2;; --out) OUT="$2"; shift 2;;
  --paper) PAPER="$2"; shift 2;; --bib) BIB="$2"; shift 2;; --data) DATA="$2"; shift 2;;
  --claims) CLAIMS="$2"; shift 2;; --section) SECTION="$2"; shift 2;; --question) QUESTION="$2"; shift 2;;
  --model) MODEL="$2"; shift 2;; --reasoning) REASONING="$2"; shift 2;; --dry-run) DRY=1; shift;;
  *) echo "unknown arg: $1" >&2; exit 2;; esac; done

case "$ROLE" in review|dual_write|cite_verify|data_audit) ;; *)
  echo "ERROR: --role must be review|dual_write|cite_verify|data_audit" >&2; exit 2;; esac
[ -n "$OUT" ] || { echo "ERROR: --out required" >&2; exit 2; }

TEMPLATE="$ROLES_DIR/$ROLE.prompt.md"
[ -f "$TEMPLATE" ] || { echo "ERROR: missing prompt template $TEMPLATE" >&2; exit 2; }

# structured roles get a JSON output schema
SCHEMA="-"
case "$ROLE" in
  cite_verify) SCHEMA="$ROLES_DIR/cite_verify.schema.json";;
  data_audit)  SCHEMA="$ROLES_DIR/data_audit.schema.json";;
esac
[ "$SCHEMA" = "-" ] || [ -f "$SCHEMA" ] || { echo "ERROR: missing schema $SCHEMA" >&2; exit 2; }

# assemble the final prompt (token substitution; empty tokens become "(not provided)")
PROMPT="$(mktemp)"; trap 'rm -f "$PROMPT"' EXIT
sed -e "s|{{PAPER}}|${PAPER:-(not provided)}|g" \
    -e "s|{{BIB}}|${BIB:-(not provided)}|g" \
    -e "s|{{DATA}}|${DATA:-(not provided)}|g" \
    -e "s|{{CLAIMS}}|${CLAIMS:-(not provided)}|g" \
    -e "s|{{SECTION}}|${SECTION:-(not provided)}|g" \
    "$TEMPLATE" > "$PROMPT"
if [ -n "$QUESTION" ] && [ -f "$QUESTION" ]; then
  { echo; echo "## Additional caller question"; cat "$QUESTION"; } >> "$PROMPT"
fi

hci_run_codex "$PROMPT" "$CD_DIR" "$OUT" "$MODEL" "$REASONING" "$SCHEMA" "$DRY"
