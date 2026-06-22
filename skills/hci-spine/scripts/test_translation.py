#!/usr/bin/env python3
"""Tests for hci_translate.py + translate_guard.py. Run: python3 test_translation.py"""
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRANS = str(HERE / "hci_translate.py")
GUARD = str(HERE / "translate_guard.py")
PASS = 0; FAIL = 0


def check(name, cond):
    global PASS, FAIL
    PASS, FAIL = (PASS + 1, FAIL) if cond else (PASS, FAIL + 1)
    print(("  ✓ " if cond else "  ✗ ") + name)


def run(script, args):
    r = subprocess.run([sys.executable, script] + args, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


SRC_TABLE = "# Matrix\n\n| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n"


def main():
    print("== translation tests ==")
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); out = root / "hci_spine_output"; out.mkdir()

        # no deliverables → scaffold exit 2
        rc, _ = run(TRANS, ["--root", str(root)])
        check("scaffold with nothing → exit 2", rc == 2)

        # add two deliverables (one with a table) + a manuscript
        (out / "hci_rationale_matrix.md").write_text(SRC_TABLE)
        (out / "research_dossier.md").write_text("# Research\n\nsome prose here.\n")
        (root / "draft.md").write_text("# Draft\n\nbody.\n")
        rc, o = run(TRANS, ["--root", str(root), "--lang", "zh"])
        check("scaffold succeeds", rc == 0)
        tdir = root / "translation_zh"
        check("translation dir + index created", (tdir / "TRANSLATION_INDEX.md").is_file())
        check("table artifact scaffolded with sentinel",
              "[TODO-TRANSLATE]" in (tdir / "hci_rationale_matrix.md").read_text())
        check("manuscript scaffolded", (tdir / "draft.md").is_file())

        # guard on fresh scaffold → INCOMPLETE (sentinels present)
        rc, o = run(GUARD, ["--root", str(root), "--lang", "zh"])
        check("guard fails on untranslated scaffold", rc == 1 and "untranslated" in o)

        # simulate a correct translation: remove sentinel lines, KEEP 2 table rows
        (tdir / "hci_rationale_matrix.md").write_text("# 矩阵\n\n| 甲 | 乙 |\n|---|---|\n| 一 | 二 |\n| 三 | 四 |\n")
        (tdir / "research_dossier.md").write_text("# 研究\n\n一些正文。\n")
        (tdir / "draft.md").write_text("# 稿\n\n正文。\n")
        rc, o = run(GUARD, ["--root", str(root), "--lang", "zh"])
        check("guard passes on complete translation w/ row parity", rc == 0)

        # break row parity (drop a table row) → guard fails
        (tdir / "hci_rationale_matrix.md").write_text("# 矩阵\n\n| 甲 | 乙 |\n|---|---|\n| 一 | 二 |\n")
        rc, o = run(GUARD, ["--root", str(root), "--lang", "zh"])
        check("guard fails when a table row is dropped (parity)", rc == 1 and "parity" in o)

        # guard with no package → exit 2
        rc, _ = run(GUARD, ["--root", str(root), "--lang", "en"])
        check("guard with no package → exit 2", rc == 2)

    print(f"\n== {PASS} passed, {FAIL} failed ==")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
