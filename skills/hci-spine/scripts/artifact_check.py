#!/usr/bin/env python3
"""Required-artifact existence/usability check, keyed to the route GATES (A–E).

Complements `hci_state.py manifest` (which compares recorded-vs-disk): this checks
that the artifacts a given GATE REQUIRES actually exist and are USABLE (present,
non-empty, not just an unfilled template stub). All forms share these writing
deliverables; study/data artifacts are gated separately by the hci_state lifecycle.

Usage:
  artifact_check.py [--root DIR] [--output-dir hci_spine_output] [--gate A|B|C|D|E|all]
                    [--manuscript PATH] [--require-through GATE]
Exit: 0 if the checked gate(s) are satisfied; 1 if any required artifact missing/stub; 2 bad input.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Gate → required artifacts (basename; searched in root and output-dir).
# "manuscript" is a virtual artifact resolved from candidates / --manuscript.
GATE_ARTIFACTS = {
    "A": ["contribution_form.md", "PROJECT_ANCHOR.md"],
    "B": ["research_dossier.md", "sota_gap_map.md", "citation_support_bank.md"],
    "C": ["section_blueprints.md", "hci_rationale_matrix.md", "manuscript"],
    "D": ["review_synthesis.md", "rebuttal_kit.md"],
    "E": ["final_paper/main.tex"],
}
GATE_ORDER = ["A", "B", "C", "D", "E"]
MANUSCRIPT_CANDIDATES = ["final_paper/main.tex", "draft.md", "06_paper/draft.md", "paper.md", "main.tex"]
STUB_MARKER = "_(managed by hci_state.py)_"


def find(root: Path, outdir: Path, rel: str):
    for base in (root, outdir):
        p = base / rel
        if p.is_file():
            return p
    return None


def usable(p: Path) -> bool:
    """Present, non-empty, and not an unfilled stub/template."""
    try:
        t = p.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return False
    if STUB_MARKER in t:
        return False
    # ledger is usable only with a real claim line
    if p.name == "CLAIM_EVIDENCE_LEDGER.md":
        return any(ln.startswith("- CLAIM:") and "EVIDENCE:" in ln for ln in t.splitlines())
    return len(t) >= 80  # below this it is effectively empty for a workflow artifact


def resolve_manuscript(root: Path, outdir: Path, override):
    if override:
        p = root / override
        return p if p.is_file() else None
    for c in MANUSCRIPT_CANDIDATES:
        p = find(root, outdir, c)
        if p:
            return p
    return None


def check_gate(root: Path, outdir: Path, gate: str, manuscript) -> list:
    rows = []
    for rel in GATE_ARTIFACTS[gate]:
        if rel == "manuscript":
            p = manuscript
            label = "manuscript (" + "/".join(MANUSCRIPT_CANDIDATES[:2]) + "/…)"
        else:
            p = find(root, outdir, rel)
            label = rel
        if p is None:
            rows.append((label, "MISSING", ""))
        elif not usable(p):
            rows.append((label, "STUB/EMPTY", str(p)))
        else:
            rows.append((label, "OK", str(p)))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--output-dir", default="hci_spine_output")
    ap.add_argument("--gate", default="all", choices=GATE_ORDER + ["all"])
    ap.add_argument("--manuscript")
    ap.add_argument("--require-through", choices=GATE_ORDER, help="hard-fail if any gate up to and including this is unsatisfied")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    outdir = root / a.output_dir
    if not root.is_dir():
        print(f"ERROR: not a dir: {root}", file=sys.stderr)
        return 2
    manuscript = resolve_manuscript(root, outdir, a.manuscript)

    gates = GATE_ORDER if a.gate == "all" else [a.gate]
    print(f"== artifact check :: {root.name} (output-dir={a.output_dir}) ==\n")
    bad_gates = []
    for g in gates:
        rows = check_gate(root, outdir, g, manuscript)
        ok = all(s == "OK" for _, s, _ in rows)
        print(f"GATE {g}: {'✓ satisfied' if ok else '✗ incomplete'}")
        for label, status, loc in rows:
            mark = "✓" if status == "OK" else "✗"
            print(f"  {mark} {label:34} {status}{('  ' + loc) if loc and status!='OK' else ''}")
        if not ok:
            bad_gates.append(g)

    # decide exit code
    fail = False
    if a.require_through:
        upto = GATE_ORDER[:GATE_ORDER.index(a.require_through) + 1]
        fail = any(g in bad_gates for g in upto)
        print(f"\nrequire-through {a.require_through}: {'FAIL' if fail else 'PASS'}")
    elif a.gate != "all":
        fail = bool(bad_gates)
    print(f"\n== {'INCOMPLETE: ' + ','.join(bad_gates) if bad_gates else 'all checked gates satisfied'} ==")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
