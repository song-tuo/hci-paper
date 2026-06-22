#!/usr/bin/env python3
"""Tests for hci_audit.py (teaching aggregator). Run: python3 test_hci_audit.py"""
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent / "hci_audit.py")
PASS = 0; FAIL = 0


def check(name, cond):
    global PASS, FAIL
    PASS, FAIL = (PASS + 1, FAIL) if cond else (PASS, FAIL + 1)
    print(("  ✓ " if cond else "  ✗ ") + name)


def run(args):
    r = subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


CLEAN = ("我们关注交互技术在特定条件下如何影响用户的可验证性。"
         "系统把照片结构转译成收据形态的文本，每次渲染都附带可检视的执行清单。\n") * 8


def main():
    print("== hci_audit tests ==")
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        clean = root / "clean.md"; clean.write_text(CLEAN)
        rc, o = run([str(clean), "--root", str(root)])
        check("clean manuscript → PASS", rc == 0 and "Verdict: PASS" in o)

        dirty = root / "dirty.md"
        dirty.write_text("我们并不声称任何普适性。\n一个系统——很强——可靠。\n" + CLEAN + "\n[Figure: TODO]\n⏳ at LaTeX time\n")
        rc, o = run([str(dirty), "--root", str(root)])
        check("dirty manuscript → HARD-FAIL", rc == 1)
        check("teaching block for defensive disclaimer present", "defensive disclaimer" in o)
        check("teaching block has Root cause / Fix / Downstream", all(k in o for k in ("Root cause", "Fix", "Downstream impact")))
        check("citation placeholder taught", "citation placeholder" in o)

        # --out writes a report file
        rc, _ = run([str(dirty), "--root", str(root), "--out", str(root / "audit.md")])
        check("--out writes report", (root / "audit.md").is_file())

        # --advisory-only never fails
        rc, _ = run([str(dirty), "--root", str(root), "--advisory-only"])
        check("--advisory-only → exit 0", rc == 0)

        # word-count passthrough trips check_universal
        rc, o = run([str(clean), "--root", str(root), "--max-words", "1"])
        check("--max-words passthrough → FAIL + word-count teaching", rc == 1 and "word count" in o)

    print(f"\n== {PASS} passed, {FAIL} failed ==")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
