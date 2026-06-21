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
[ -d "$CD_DIR" ] || { echo "ERROR: --cd directory not found: $CD_DIR" >&2; exit 2; }

case "$ROLE" in
  review)
    [ -n "$PAPER" ] && [ -f "$PAPER" ] || { echo "ERROR: review requires --paper FILE" >&2; exit 2; };;
  dual_write)
    [ -n "$PAPER" ] && [ -e "$PAPER" ] || { echo "ERROR: dual_write requires --paper SOURCE" >&2; exit 2; }
    [ -n "$SECTION" ] || { echo "ERROR: dual_write requires --section NAME" >&2; exit 2; };;
  cite_verify)
    [ -n "$PAPER" ] && [ -f "$PAPER" ] || { echo "ERROR: cite_verify requires --paper FILE" >&2; exit 2; }
    [ -n "$BIB" ] && [ -f "$BIB" ] || { echo "ERROR: cite_verify requires --bib FILE" >&2; exit 2; };;
  data_audit)
    [ -n "$DATA" ] && [ -e "$DATA" ] || { echo "ERROR: data_audit requires --data PATH" >&2; exit 2; }
    [ -n "$CLAIMS" ] && [ -f "$CLAIMS" ] || { echo "ERROR: data_audit requires --claims FILE" >&2; exit 2; };;
esac

TEMPLATE="$ROLES_DIR/$ROLE.prompt.md"
[ -f "$TEMPLATE" ] || { echo "ERROR: missing prompt template $TEMPLATE" >&2; exit 2; }

# structured roles get a JSON output schema
SCHEMA="-"
case "$ROLE" in
  cite_verify) SCHEMA="$ROLES_DIR/cite_verify.schema.json";;
  data_audit)  SCHEMA="$ROLES_DIR/data_audit.schema.json";;
esac
[ "$SCHEMA" = "-" ] || [ -f "$SCHEMA" ] || { echo "ERROR: missing schema $SCHEMA" >&2; exit 2; }

# Assemble the prompt. Escape sed replacement metacharacters so paths containing
# `&` or `|` remain literal.
PROMPT="$(mktemp)"; trap 'rm -f "$PROMPT"' EXIT
sed_escape() { printf '%s' "$1" | sed 's/[&|]/\\&/g'; }
PAPER_E="$(sed_escape "$PAPER")"; BIB_E="$(sed_escape "$BIB")"
DATA_E="$(sed_escape "$DATA")"; CLAIMS_E="$(sed_escape "$CLAIMS")"
SECTION_E="$(sed_escape "$SECTION")"
sed -e "s|{{PAPER}}|$PAPER_E|g" \
    -e "s|{{BIB}}|$BIB_E|g" \
    -e "s|{{DATA}}|$DATA_E|g" \
    -e "s|{{CLAIMS}}|$CLAIMS_E|g" \
    -e "s|{{SECTION}}|$SECTION_E|g" \
    "$TEMPLATE" > "$PROMPT"
if [ -n "$QUESTION" ] && [ -f "$QUESTION" ]; then
  { echo; echo "## Additional caller question"; cat "$QUESTION"; } >> "$PROMPT"
fi

hci_run_codex "$PROMPT" "$CD_DIR" "$OUT" "$MODEL" "$REASONING" "$SCHEMA" "$DRY"
