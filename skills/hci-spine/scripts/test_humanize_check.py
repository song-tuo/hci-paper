#!/usr/bin/env python3
"""Tests for humanize_check.py. Run: python3 test_humanize_check.py"""
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent / "humanize_check.py")
PASS = 0; FAIL = 0


def check(name, cond):
    global PASS, FAIL
    PASS, FAIL = (PASS + 1, FAIL) if cond else (PASS, FAIL + 1)
    print(("  ✓ " if cond else "  ✗ ") + name)


def run(text, extra=None):
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(text); path = f.name
    r = subprocess.run([sys.executable, SCRIPT, path] + (extra or []), capture_output=True, text=True)
    Path(path).unlink()
    return r.returncode, r.stdout + r.stderr


CLEAN = ("我们关注交互技术在特定条件下如何影响用户的可验证性。"
         "系统把图像结构转译成收据形态的文本，每次渲染都附带可检视的执行清单。"
         "这种设计让读者能够追踪每一行的来源。\n") * 3


def main():
    print("== humanize_check tests ==")
    rc, _ = run(CLEAN)
    check("clean prose passes", rc == 0)

    rc, o = run("我们并不声称我们的方法适用于所有场景。" + CLEAN)
    check("defensive disclaimer → HARD-FAIL", rc == 1 and "defensive" in o)

    rc, o = run("这不是一个模型，而是一种机制。" + CLEAN + "没有华丽，只有精确。" + "不像图片，更像证据。")
    check("negation-first (>2) → HARD-FAIL", rc == 1 and "negation-first" in o)

    rc, o = run("皮肤更白更滑更软。" + CLEAN)
    check("adjective-stacking (更X更Y更Z) → HARD-FAIL", rc == 1 and "adjective" in o)

    rc, o = run("它快速的、精确的、稳健的、优雅的。" + CLEAN)
    check("rule-of-three 、-list → HARD-FAIL", rc == 1)

    emdash = "这是一个系统——它很强——而且可靠——还能复现——并且开源。\n" + CLEAN
    rc, o = run(emdash)
    check("em-dash connectors over threshold → HARD-FAIL", rc == 1 and "em-dash" in o)

    openers = "\n".join(["However, x." , "Furthermore, y.", "Moreover, z.", "In addition, w.", "Overall, v."]) + "\n" + CLEAN
    rc, o = run(openers)
    check("AI template openers (>4) → HARD-FAIL", rc == 1 and "opener" in o.lower())

    # fenced code with offending patterns is skipped
    fenced = "```\n我们并不声称任何东西。\n皮肤更白更滑更软。\n```\n" + CLEAN
    rc, _ = run(fenced)
    check("offending patterns inside fenced code ignored", rc == 0)

    # advisory-only never fails
    rc, _ = run("我们并不声称任何东西。" + CLEAN, ["--advisory-only"])
    check("--advisory-only → exit 0 despite issues", rc == 0)

    # strict lowers thresholds (1 em-dash trips it)
    rc, _ = run("一个系统——很强。\n" + CLEAN, ["--strict"])
    check("--strict trips on a single em-dash connector", rc == 1)

    print(f"\n== {PASS} passed, {FAIL} failed ==")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
