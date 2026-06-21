#!/usr/bin/env python3
"""Lifecycle/gate tests for hci_state.py. Run: python3 test_hci_state.py
No pytest — plain asserts + a tiny runner. Calls cmd_* directly with Namespaces."""
import json
import sys
import tempfile
from argparse import Namespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hci_state as H  # noqa: E402

PASS = 0; FAIL = 0


def check(name, cond):
    global PASS, FAIL
    PASS, FAIL = (PASS + 1, FAIL) if cond else (PASS, FAIL + 1)
    print(("  ✓ " if cond else "  ✗ ") + name)


def st(root):
    return json.loads((root / H.STATE_FILE).read_text())


def main():
    print("== hci_state lifecycle/gate tests ==")
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        H.cmd_init(root, Namespace(project="P", venue="TEI 2027", deadline="2026-08-06",
                                   word_min=7000, word_max=8000, area="", tradition="", force=False))
        check("init → phase=forge", st(root)["lifecycle_phase"] == "forge")

        # gate: forge→lock blocked without motivation/deprecated
        rc = H.cmd_advance(root, Namespace(to=None, force=False))
        check("advance forge→lock BLOCKED (rc=1)", rc == 1 and st(root)["lifecycle_phase"] == "forge")
        check("blocker recorded on block", any(b["id"] == "gate:lock" for b in st(root)["blockers"]))

        # satisfy gate
        H.cmd_deprecate(root, Namespace(option="IUI framing", reason="retargeted TEI"))
        H.cmd_lock(root, Namespace(motivation="Form is indexical"))
        rc = H.cmd_advance(root, Namespace(to=None, force=False))
        check("advance forge→lock OK after gate met", rc == 0 and st(root)["lifecycle_phase"] == "lock")
        check("next_step updated to lock hint", "set-type" in st(root)["next_step"])
        check("blocker cleared after advance", not any(b["id"] == "gate:lock" for b in st(root)["blockers"]))

        # invalid contribution form rejected
        try:
            H.cmd_set_type(root, Namespace(primary="aihci", secondary=None, area=None, tradition=None))
            check("invalid primary rejected", False)
        except SystemExit:
            check("invalid primary rejected (aihci is an AREA, not a form)", True)

        # lock→prototype_gate blocked without type, then OK
        rc = H.cmd_advance(root, Namespace(to=None, force=False))
        check("lock→prototype_gate BLOCKED without type", rc == 1)
        H.cmd_set_type(root, Namespace(primary="artifact", secondary="empirical", area="human-AI interaction", tradition=None))
        rc = H.cmd_advance(root, Namespace(to=None, force=False))
        check("lock→prototype_gate OK after set-type", rc == 0 and st(root)["lifecycle_phase"] == "prototype_gate")

        # media necessity gate (item 11)
        rc = H.cmd_advance(root, Namespace(to=None, force=False))
        check("prototype_gate→ethics BLOCKED without media_necessity", rc == 1)
        H.cmd_attest(root, Namespace(key="media_necessity", by="user", note="thermal receipt; AI removable=no"))
        rc = H.cmd_advance(root, Namespace(to=None, force=False))
        check("→ethics OK after media_necessity attested", rc == 0 and st(root)["lifecycle_phase"] == "ethics")

        # force override
        rc = H.cmd_advance(root, Namespace(to=None, force=True))
        check("force advance overrides unmet gate", rc == 0 and st(root)["lifecycle_phase"] == "study_design")

        # advance can only go to the immediate next phase
        try:
            H.cmd_advance(root, Namespace(to="paper", force=True))
            check("skipping phases rejected", False)
        except SystemExit:
            check("skipping phases rejected", True)

        # manifest drift: record an output, then delete it → missing=1, rc=1
        (root / "draft.md").write_text("hello", encoding="utf-8")
        H.cmd_record(root, Namespace(kind="output", path="draft.md", verified_by="user"))
        try:
            H.cmd_record(root, Namespace(kind="output", path="missing.md", verified_by="user"))
            check("record rejects missing output", False)
        except SystemExit:
            check("record rejects missing output", True)
        rc = H.cmd_manifest(root, Namespace())
        check("manifest clean when recorded file present (rc=0)", rc == 0)
        (root / "draft.md").unlink()
        rc = H.cmd_manifest(root, Namespace())
        check("manifest detects drift when recorded file missing (rc=1)", rc == 1)
        check("OUTPUT_MANIFEST flags the missing file",
              "draft.md" in (root / "OUTPUT_MANIFEST.md").read_text())

        # handoff regenerates from state
        H.cmd_handoff(root, Namespace())
        ho = (root / "HANDOFF.md").read_text()
        check("handoff carries phase + motivation", "study_design" in ho and "Form is indexical" in ho)

    print(f"\n== {PASS} passed, {FAIL} failed ==")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
