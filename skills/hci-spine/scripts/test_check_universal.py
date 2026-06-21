#!/usr/bin/env python3
"""Tests for check_universal.py. Run: python3 test_check_universal.py
Builds fixtures, invokes the lint as a subprocess, checks exit codes + output."""
import subprocess
import sys
import tempfile
from pathlib import Path

LINT = str(Path(__file__).resolve().parent / "check_universal.py")
PASS = 0; FAIL = 0


def run(args):
    r = subprocess.run([sys.executable, LINT] + args, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def check(name, cond):
    global PASS, FAIL
    PASS, FAIL = (PASS + 1, FAIL) if cond else (PASS, FAIL + 1)
    print(("  ✓ " if cond else "  ✗ ") + name)


def main():
    print("== check_universal tests ==")
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        words = " ".join(["word"] * 300) + "\n"

        # the EXACT user-reported bug: --max-words 1 on a 300-word file must FAIL
        f = root / "over.md"; f.write_text(words)
        rc, out = run([str(f), "--max-words", "1"])
        check("--max-words 1 on 300-word file → HARD-FAIL (was PASS bug)", rc == 1 and "max" in out.lower())

        # min enforced independently
        rc, _ = run([str(f), "--min-words", "7000"])
        check("below --min-words → HARD-FAIL", rc == 1)

        # in-range passes
        rc, out = run([str(f), "--min-words", "100", "--max-words", "500"])
        check("in venue range → PASS", rc == 0 and "within" in out)

        # prose mentioning the word 'placeholder' must NOT fail (false-positive fix)
        f2 = root / "doc.md"; f2.write_text("We discuss how placeholder text is avoided in good papers.\n" + words)
        rc, _ = run([str(f2)])
        check("prose mentioning 'placeholder' → PASS (no false positive)", rc == 0)

        # real placeholder markers DO fail
        f3 = root / "ph.md"; f3.write_text(words + "\n[Figure: TODO screenshot]\nsee ⏳ at LaTeX time\n")
        rc, out = run([str(f3)])
        check("real ⏳ + [Figure: …] markers → HARD-FAIL", rc == 1)

        # fenced code block with markers is skipped
        f4 = root / "fenced.md"; f4.write_text(words + "\n```\n[Figure: example]\n⏳\n```\n")
        rc, _ = run([str(f4)])
        check("markers inside fenced code → PASS (skipped)", rc == 0)

        # LaTeX: missing \input and missing figure
        tex = root / "main.tex"
        tex.write_text(words + "\n\\input{missing_section}\n\\includegraphics{figs/nope}\n")
        rc, out = run([str(tex)])
        check("missing \\input + figure → HARD-FAIL", rc == 1 and "missing" in out)

        # LaTeX: bib present, cite resolves vs not
        (root / "refs.bib").write_text("@article{smith2020, title={X}}\n")
        tex2 = root / "p2.tex"
        tex2.write_text(words + "\n\\bibliography{refs}\n\\cite{smith2020} and \\cite{ghost2099}\n")
        rc, out = run([str(tex2)])
        check("unresolved \\cite key → HARD-FAIL", rc == 1 and ("ghost2099" in out or "unresolved" in out.lower()))

        # clean tex passes
        tex3 = root / "clean.tex"
        tex3.write_text(words + "\n\\bibliography{refs}\n\\cite{smith2020}\n")
        rc, out = run([str(tex3)])
        check("clean tex (resolved cite, no placeholders) → PASS", rc == 0)

        # anonymity flag
        tex4 = root / "anon.tex"; tex4.write_text(words + "\n\\author{Jane Doe}\n")
        rc, _ = run([str(tex4), "--anonymous"])
        check("--anonymous catches \\author{Name}", rc == 1)
        rc, _ = run([str(tex4)])
        check("without --anonymous, author line ignored", rc == 0)

        # advisory-only never fails
        rc, _ = run([str(f3), "--advisory-only"])
        check("--advisory-only → exit 0 despite issues", rc == 0)

    print(f"\n== {PASS} passed, {FAIL} failed ==")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
