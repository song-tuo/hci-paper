#!/usr/bin/env python3
"""Tests for hci_state.py v2 — form-aware lifecycle + evidence-backed gates.
Run: python3 test_hci_state.py. No pytest; calls cmd_* with Namespaces."""
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


def raises(fn):
    try:
        fn(); return False
    except SystemExit:
        return True


def st(root):
    return json.loads((root / H.STATE_FILE).read_text())


def init(root, **kw):
    d = dict(project="P", venue="TEI 2027", deadline="", word_min=None, word_max=None,
             area="", tradition="", force=False)
    d.update(kw)
    H.cmd_init(root, Namespace(**d))


def main():
    print("== hci_state v2 tests ==")

    # --- undecided + form-aware skipping (conceptual_theoretical) ---
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); init(root)
        check("init → form=undecided", H.form_of(st(root)) == H.UNDECIDED)
        check("undecided active lifecycle is [forge, lock]", H.active_phases(st(root)) == ["forge", "lock"])
        H.cmd_deprecate(root, Namespace(option="alt", reason="r"))
        H.cmd_lock(root, Namespace(motivation="m", relock=False))
        check("advance forge→lock OK", H.cmd_advance(root, Namespace(to=None, force=False)) == 0)
        # cannot advance past lock while undecided — must set a form first
        check("lock→advance BLOCKED while undecided (must set form)",
              raises(lambda: H.cmd_advance(root, Namespace(to=None, force=False))))
        check("aihci rejected as a form (it is an AREA)",
              raises(lambda: H.cmd_set_type(root, Namespace(primary="aihci", secondary=None, area=None, tradition=None))))
        H.cmd_set_type(root, Namespace(primary="conceptual_theoretical", secondary=None, area=None, tradition=None))
        check("conceptual lifecycle skips study phases",
              H.active_phases(st(root)) == ["forge", "lock", "claim_lock", "paper"])
        # lock → claim_lock directly (prototype/ethics/study all skipped, no --force)
        check("advance lock→claim_lock (form-aware skip)",
              H.cmd_advance(root, Namespace(to=None, force=False)) == 0 and st(root)["lifecycle_phase"] == "claim_lock")

    # --- evidence-backed gates (empirical full walk) ---
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); init(root)
        H.cmd_deprecate(root, Namespace(option="a", reason="r"))
        H.cmd_lock(root, Namespace(motivation="m", relock=False))
        H.cmd_advance(root, Namespace(to=None, force=False))  # → lock
        H.cmd_set_type(root, Namespace(primary="empirical", secondary=None, area=None, tradition=None))
        check("empirical lifecycle skips prototype_gate", "prototype_gate" not in H.active_phases(st(root)))
        check("advance lock→ethics (skips prototype_gate)",
              H.cmd_advance(root, Namespace(to=None, force=False)) == 0 and st(root)["lifecycle_phase"] == "ethics")
        H.cmd_attest(root, Namespace(key="ethics_note", by="u", note="", evidence=None))
        H.cmd_advance(root, Namespace(to=None, force=False))  # → study_design
        H.cmd_attest(root, Namespace(key="study_design", by="u", note="", evidence=None))
        H.cmd_advance(root, Namespace(to=None, force=False))  # → pilot
        H.cmd_attest(root, Namespace(key="pilot", by="u", note="", evidence=None))
        H.cmd_advance(root, Namespace(to=None, force=False))  # → instrumentation
        H.cmd_attest(root, Namespace(key="instrumentation", by="u", note="", evidence=None))
        H.cmd_advance(root, Namespace(to=None, force=False))  # → data_freeze

        # data_freeze attest requires existing evidence
        check("attest data_freeze without --evidence rejected",
              raises(lambda: H.cmd_attest(root, Namespace(key="data_freeze", by="u", note="", evidence=None))))
        check("attest data_freeze with missing evidence rejected",
              raises(lambda: H.cmd_attest(root, Namespace(key="data_freeze", by="u", note="", evidence="nope"))))
        (root / "data").mkdir()
        H.cmd_attest(root, Namespace(key="data_freeze", by="u", note="", evidence="data"))
        check("attest data_freeze with real dir → recorded",
              "data_freeze" in st(root)["attestations"])
        H.cmd_advance(root, Namespace(to=None, force=False))  # → analysis

        # analysis exit needs an evidence-backed claim from the LEDGER (not a manual count)
        check("analysis→advance BLOCKED with zero claims", H.cmd_advance(root, Namespace(to=None, force=False)) == 1)
        check("claim add with missing evidence rejected",
              raises(lambda: H.cmd_claim(root, Namespace(action="add", text="c", evidence="ghost.json"))))
        (root / "res.json").write_text("{}")
        H.cmd_claim(root, Namespace(action="add", text="determinism 893/893", evidence="res.json"))
        check("claim_count derived from ledger == 1", H.count_claims(root) == 1)
        check("analysis→advance OK after evidence-backed claim",
              H.cmd_advance(root, Namespace(to=None, force=False)) == 0 and st(root)["lifecycle_phase"] == "claim_lock")

    # --- anti-forgery: record + relock + post-lock invalidation ---
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); init(root)
        check("record output of missing file rejected",
              raises(lambda: H.cmd_record(root, Namespace(kind="output", path="nope.pdf", verified_by="u"))))
        (root / "real.pdf").write_text("x")
        check("record real output OK", H.cmd_record(root, Namespace(kind="output", path="real.pdf", verified_by="u")) == 0)

        H.cmd_deprecate(root, Namespace(option="a", reason="r"))
        H.cmd_lock(root, Namespace(motivation="m1", relock=False))
        check("re-lock without --relock rejected",
              raises(lambda: H.cmd_lock(root, Namespace(motivation="m2", relock=False))))
        H.cmd_advance(root, Namespace(to=None, force=False))  # → lock
        H.cmd_set_type(root, Namespace(primary="artifact", secondary=None, area=None, tradition=None))
        H.cmd_attest(root, Namespace(key="media_necessity", by="u", note="", evidence=None))
        H.cmd_advance(root, Namespace(to=None, force=False))  # → prototype_gate? no: lock→prototype_gate
        # now beyond lock with an attestation; changing the form must invalidate downstream
        H.cmd_set_type(root, Namespace(primary="empirical", secondary=None, area=None, tradition=None))
        s = st(root)
        check("post-lock form change invalidates downstream (phase reset to lock)",
              s["lifecycle_phase"] == "lock" and s["attestations"] == {})
        check("invalidation raises a HIGH blocker", any(b["severity"] == "HIGH" for b in s["blockers"]))

    print(f"\n== {PASS} passed, {FAIL} failed ==")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
