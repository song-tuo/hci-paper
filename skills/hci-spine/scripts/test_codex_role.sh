#!/usr/bin/env bash
# Self-test for codex_role.sh + validate_codex_output.py. No real Codex call (dry-run).
# Run: bash test_codex_role.sh
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
ROLE="$DIR/codex_role.sh"; VAL="$DIR/validate_codex_output.py"
FIX="$(mktemp -d)"; trap 'rm -rf "$FIX"' EXIT
printf '%s\n' 'draft' > "$FIX/draft.md"
printf '%s\n' '@article{x,title={X}}' > "$FIX/refs.bib"
printf '%s\n' '# claims' > "$FIX/claims.md"
mkdir -p "$FIX/results"
PASS=0; FAIL=0
ok(){ if [ "$2" = "$3" ]; then PASS=$((PASS+1)); echo "  ✓ $1"; else FAIL=$((FAIL+1)); echo "  ✗ $1 (want $2 got $3)"; fi; }
grok(){ if echo "$2" | grep -q -- "$3"; then PASS=$((PASS+1)); echo "  ✓ $1"; else FAIL=$((FAIL+1)); echo "  ✗ $1"; fi; }

echo "== codex_role.sh self-test =="
bash -n "$ROLE"; ok "dispatcher syntax" 0 $?
bash -n "$DIR/codex_lib.sh"; ok "codex_lib syntax" 0 $?

bash "$ROLE" --role bogus --out /tmp/x >/dev/null 2>&1; ok "bad role → 2" 2 $?
bash "$ROLE" --role review --cd /tmp >/dev/null 2>&1; ok "missing --out → 2" 2 $?
bash "$ROLE" --role review --cd "$FIX" --out x.md --dry-run >/dev/null 2>&1; ok "review missing paper → 2" 2 $?
bash "$ROLE" --role cite_verify --cd "$FIX" --paper "$FIX/draft.md" --out x.md --dry-run >/dev/null 2>&1; ok "cite_verify missing bib → 2" 2 $?
bash "$ROLE" --role data_audit --cd "$FIX" --data "$FIX/results" --out x.md --dry-run >/dev/null 2>&1; ok "data_audit missing claims → 2" 2 $?

OUTR=$(bash "$ROLE" --role review --cd "$FIX" --paper "$FIX/draft.md" --out r.md --dry-run 2>&1); rc=$?
ok "dry-run review → 0" 0 $rc; grok "review dry-run prints command" "$OUTR" "DRY-RUN"

OUTC=$(bash "$ROLE" --role cite_verify --cd "$FIX" --paper "$FIX/draft.md" --bib "$FIX/refs.bib" --out c.md --dry-run 2>&1)
grok "cite_verify wires --output-schema" "$OUTC" "output-schema"
OUTD=$(bash "$ROLE" --role data_audit --cd "$FIX" --data "$FIX/results" --claims "$FIX/claims.md" --out d.md --dry-run 2>&1)
grok "data_audit wires --output-schema" "$OUTD" "output-schema"
OUTW=$(bash "$ROLE" --role dual_write --cd "$FIX" --section "Introduction" --paper "$FIX/draft.md" --out w.md --dry-run 2>&1)
grok "dual_write is prose (no schema)" "$OUTW" "DRY-RUN"
if echo "$OUTW" | grep -q -- "output-schema"; then FAIL=$((FAIL+1)); echo "  ✗ dual_write must NOT use a schema"; else PASS=$((PASS+1)); echo "  ✓ dual_write has no schema"; fi

echo "== validate_codex_output.py =="
GOODC=$(mktemp); cat > "$GOODC" <<'J'
prefix noise
```
{"citations":[{"key":"smith2020","exists":"yes","claim_supported":"partial","note":"ok"}],"summary":"s"}
```
J
python3 "$VAL" --role cite_verify "$GOODC" >/dev/null 2>&1; ok "good cite_verify → 0" 0 $?
BADC=$(mktemp); echo '{"citations":[{"key":"x","exists":"maybe","claim_supported":"yes","note":""}],"summary":"s"}' > "$BADC"
python3 "$VAL" --role cite_verify "$BADC" >/dev/null 2>&1; ok "bad enum cite_verify → 1" 1 $?
GOODD=$(mktemp); echo '{"claims":[{"claim":"c","evidence_file":"f.json","verdict":"supported","note":"n"}],"summary":"s"}' > "$GOODD"
python3 "$VAL" --role data_audit "$GOODD" >/dev/null 2>&1; ok "good data_audit → 0" 0 $?
BADD=$(mktemp); echo '{"claims":[{"claim":"c","verdict":"supported"}],"summary":"s"}' > "$BADD"
python3 "$VAL" --role data_audit "$BADD" >/dev/null 2>&1; ok "missing-field data_audit → 1" 1 $?
NOJSON=$(mktemp); echo "no json here" > "$NOJSON"
python3 "$VAL" --role cite_verify "$NOJSON" >/dev/null 2>&1; ok "no-JSON → 2" 2 $?
rm -f "$GOODC" "$BADC" "$GOODD" "$BADD" "$NOJSON"

echo ""; echo "== $PASS passed, $FAIL failed =="
[ "$FAIL" = "0" ]
