#!/usr/bin/env python3
"""Tests for build_adapters.py — generates to a temp dest (does NOT touch ~/.codex).
Run: python3 test_build_adapters.py"""
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = str(HERE / "build_adapters.py")
sys.path.insert(0, str(HERE))
import build_adapters as B  # noqa: E402

PASS = 0; FAIL = 0


def check(name, cond):
    global PASS, FAIL
    PASS, FAIL = (PASS + 1, FAIL) if cond else (PASS, FAIL + 1)
    print(("  ✓ " if cond else "  ✗ ") + name)


def run(args):
    r = subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def main():
    print("== build_adapters tests ==")
    # unit: frontmatter stripping
    fm = "---\nname: x\ndescription: d\nargument-hint: [t]\nallowed-tools: Bash(*)\n---\nbody\n"
    out = B.strip_frontmatter_keys(fm)
    check("strips argument-hint", "argument-hint" not in out)
    check("strips allowed-tools", "allowed-tools" not in out)
    check("keeps name + description + body", "name: x" in out and "description: d" in out and "body" in out)

    with tempfile.TemporaryDirectory() as d:
        dest = Path(d) / "hci-spine"
        rc, out = run(["--dest", str(dest), "--dry-run"])
        check("dry-run exit 0", rc == 0)
        check("dry-run does not create dest", not dest.exists())
        check("dry-run mentions openai.yaml", "openai.yaml" in out)

        rc, out = run(["--dest", str(dest)])
        check("generate exit 0", rc == 0)
        check("SKILL.md emitted", (dest / "SKILL.md").is_file())
        sk = (dest / "SKILL.md").read_text()
        fmblock = sk.split("---", 2)[1]
        check("emitted SKILL.md frontmatter has no argument-hint", "argument-hint:" not in fmblock)
        check("emitted SKILL.md frontmatter has no allowed-tools", "allowed-tools:" not in fmblock)
        check("emitted SKILL.md keeps name", "name: hci-spine" in fmblock)
        check("openai.yaml written", (dest / "agents/openai.yaml").is_file())
        check("ADAPTER_GENERATED marker written", (dest / B.MARKER).is_file())
        check("playbook + script copied", (dest / "references/contribution-form-playbooks.md").is_file()
              and (dest / "scripts/hci_state.py").is_file())

        # idempotent re-run
        rc2, _ = run(["--dest", str(dest)])
        check("re-run idempotent (exit 0 over generated dir)", rc2 == 0)

        # refuses a non-generated, non-empty dir without --force
        foreign = Path(d) / "foreign"; foreign.mkdir(); (foreign / "keep.txt").write_text("mine")
        rc3, _ = run(["--dest", str(foreign)])
        check("refuses non-generated non-empty dir", rc3 == 2)
        rc4, _ = run(["--dest", str(foreign), "--force"])
        check("--force overwrites foreign dir", rc4 == 0)

    print(f"\n== {PASS} passed, {FAIL} failed ==")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
