#!/usr/bin/env python3
"""Tests for artifact_check.py. Run: python3 test_artifact_check.py"""
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent / "artifact_check.py")
PASS = 0; FAIL = 0


def check(name, cond):
    global PASS, FAIL
    PASS, FAIL = (PASS + 1, FAIL) if cond else (PASS, FAIL + 1)
    print(("  ✓ " if cond else "  ✗ ") + name)


def run(args):
    r = subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


REAL = "x" * 120  # passes the >=80 usable threshold


def main():
    print("== artifact_check tests ==")
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); out = root / "hci_spine_output"; out.mkdir()

        # empty project: gate A fails
        rc, o = run(["--root", str(root), "--gate", "A"])
        check("gate A fails on empty project", rc == 1 and "MISSING" in o)

        # add gate-A artifacts (one real, one stub) → stub still fails
        (out / "contribution_form.md").write_text(REAL)
        (root / "PROJECT_ANCHOR.md").write_text("# Project Anchor\n\n_(managed by hci_state.py)_\n")
        rc, o = run(["--root", str(root), "--gate", "A"])
        check("stub PROJECT_ANCHOR flagged STUB/EMPTY", rc == 1 and "STUB/EMPTY" in o)

        # fill anchor for real → gate A passes
        (root / "PROJECT_ANCHOR.md").write_text("# Project Anchor\n\n## Locked motivation\n" + REAL)
        rc, o = run(["--root", str(root), "--gate", "A"])
        check("gate A passes when both real", rc == 0)

        # gate C needs a manuscript → fails without one
        (out / "section_blueprints.md").write_text(REAL)
        (out / "hci_rationale_matrix.md").write_text(REAL)
        rc, o = run(["--root", str(root), "--gate", "C"])
        check("gate C fails with no manuscript", rc == 1 and "manuscript" in o)

        # add a manuscript → gate C passes
        (root / "draft.md").write_text(REAL)
        rc, o = run(["--root", str(root), "--gate", "C"])
        check("gate C passes once draft.md exists", rc == 0)

        # --manuscript override resolves a custom path
        (root / "06_paper").mkdir(); (root / "06_paper/draft.md").write_text(REAL)
        rc, o = run(["--root", str(root), "--gate", "C", "--manuscript", "06_paper/draft.md"])
        check("--manuscript override works", rc == 0)

        # require-through B fails (research artifacts absent) even though A ok
        rc, o = run(["--root", str(root), "--require-through", "B"])
        check("require-through B fails (no research artifacts)", rc == 1)

        # all-mode is informational (exit 0) without require-through
        rc, o = run(["--root", str(root), "--gate", "all"])
        check("all-mode is informational (exit 0)", rc == 0)

        # CLAIM ledger usability: stub ledger not usable, real claim is
        led = out / "CLAIM_EVIDENCE_LEDGER.md"
        led.write_text("# Claim Evidence Ledger\n\n_(managed by hci_state.py)_\n")
        # ledger isn't a gate artifact here, but exercise usable() via gate B requirement set:
        # (research artifacts) — add real ones so gate B passes
        for f in ("research_dossier.md", "sota_gap_map.md", "citation_support_bank.md"):
            (out / f).write_text(REAL)
        rc, o = run(["--root", str(root), "--gate", "B"])
        check("gate B passes once research artifacts real", rc == 0)

    print(f"\n== {PASS} passed, {FAIL} failed ==")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
