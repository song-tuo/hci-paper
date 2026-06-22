#!/usr/bin/env python3
"""Tests for verify_citations.py — offline only (no network). Run: python3 test_verify_citations.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = str(HERE / "verify_citations.py")
sys.path.insert(0, str(HERE))
import verify_citations as V  # noqa: E402

PASS = 0; FAIL = 0


def check(name, cond):
    global PASS, FAIL
    PASS, FAIL = (PASS + 1, FAIL) if cond else (PASS, FAIL + 1)
    print(("  ✓ " if cond else "  ✗ ") + name)


def run(args):
    r = subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


BIB = """@article{smith2020,
  title = {A Study of Things},
  doi = {10.1145/1234567},
  year = {2020}
}
@inproceedings{doe2019,
  title={Another Paper Without DOI},
  year={2019}
}
"""


def main():
    print("== verify_citations tests (offline) ==")
    # parser
    entries = V.parse_bib(BIB)
    check("parses 2 entries", len(entries) == 2)
    check("extracts doi for smith2020", entries[0]["doi"] == "10.1145/1234567")
    check("extracts title for doe2019", entries[1]["title"] == "Another Paper Without DOI")
    # norm + jaccard
    check("norm strips punctuation/case", V.norm("A Study, of Things!") == "a study of things")
    check("jaccard identical == 1.0", V.jaccard("a b c", "a b c") == 1.0)
    check("jaccard disjoint == 0.0", V.jaccard("a b", "c d") == 0.0)
    check("User-Agent has no mailto without email", V.user_agent(None) == "hci-spine/1.0")
    check("User-Agent includes caller email when provided", V.user_agent("user@example.org").endswith("(mailto:user@example.org)"))

    with tempfile.TemporaryDirectory() as d:
        bib = Path(d) / "refs.bib"; bib.write_text(BIB)
        # offline → all unverified, exit 0, valid JSON
        rc, out, _ = run([str(bib), "--offline"])
        obj = json.loads(out)
        check("offline exit 0", rc == 0)
        check("offline marks all unverified", all(c["found"] == "unverified" for c in obj["citations"]))
        check("offline JSON has summary + 2 citations", "summary" in obj and len(obj["citations"]) == 2)
        # offline --strict → unverified counts as failure
        rc, _, _ = run([str(bib), "--offline", "--strict"])
        check("offline --strict exit 1 (unverified = fail)", rc == 1)
        # --out writes file
        rc, _, _ = run([str(bib), "--offline", "--out", str(Path(d) / "v.json")])
        check("--out writes a file", (Path(d) / "v.json").is_file())
        # empty bib → exit 2
        empty = Path(d) / "empty.bib"; empty.write_text("nothing here")
        rc, _, _ = run([str(empty), "--offline"])
        check("no entries → exit 2", rc == 2)
        # missing file → exit 2
        rc, _, _ = run([str(Path(d) / "nope.bib"), "--offline"])
        check("missing file → exit 2", rc == 2)

    print(f"\n== {PASS} passed, {FAIL} failed ==")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
