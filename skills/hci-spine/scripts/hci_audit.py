#!/usr/bin/env python3
"""Teaching-quality aggregate audit for hci-spine.

Runs the three deterministic lints (artifact_check, check_universal, humanize_check)
and turns their findings into a TEACHING report: each finding gets what / where /
root-cause / fix / downstream-impact (the form paper-spine's integrity_audit uses),
not just pass/fail. Aggregates exit codes into one verdict.

Usage:
  hci_audit.py PAPER [--root DIR] [--min-words N] [--max-words N] [--tex-root DIR]
               [--require-through A|B|C|D|E] [--out FILE] [--advisory-only]
Exit: 0 if no tool HARD-failed (or --advisory-only); 1 otherwise; 2 bad input.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# token found in a tool's output → teaching note (root cause, fix, downstream impact)
TEACH = [
    ("word count", ("manuscript length is outside the venue range",
                    "expand or cut to the venue's word band before submission",
                    "desk-reject / reviewer assumes the work is thin or padded")),
    ("citation placeholder", ("deferred citations (⏳/TODO) were never finalized",
                              "resolve every reference; run verify_citations.py",
                              "reviewers read it as incomplete; hallucinated-cite risk")),
    ("figure/table placeholder", ("a [Figure:]/[Table] marker was left unrendered",
                                  "render the real artifact or remove the marker",
                                  "the contribution looks unfinished")),
    ("unresolved \\cite", ("a \\cite key has no matching bib entry",
                           "add the entry or fix the key",
                           "broken citation in the compiled PDF")),
    ("\\input", ("an \\input/\\include target is missing",
                 "create the file or fix the path",
                 "the document will not compile")),
    ("figure missing", ("an \\includegraphics file does not exist",
                        "add the figure file or fix the path",
                        "compile failure / missing figure")),
    ("MISSING", ("a required stage deliverable is absent",
                 "produce it via the owning gate before advancing",
                 "the next gate cannot pass; the recovery map breaks")),
    ("STUB/EMPTY", ("a deliverable exists only as an unfilled template",
                    "fill it with real content",
                    "false sense of progress; downstream work builds on nothing")),
    ("defensive disclaimer", ("the AI local-patching reflex added a hedge instead of fixing prose",
                              "state what the work does, positively; keep one necessary scope sentence",
                              "plants the very doubt it disclaims; a strong AI tell")),
    ("em-dash connector", ("em-dash used as a clause connector (signature-style violation)",
                           "recast with commas / periods / natural phrasing",
                           "reads templated; lowers the human-authored signal")),
    ("negation-first", ("'not X but Y' framing instead of direct assertion",
                        "state Y directly",
                        "lower information density; an AI tell")),
    ("adjective-stack", ("stacked adjectives / rule-of-three",
                         "let each quality breathe in a full sentence; one modifier per noun",
                         "ornamental prose; reviewer fatigue")),
    ("AI template opener", ("paragraph opens with However,/Furthermore,/此外,… repeatedly",
                            "vary openings; fuse or drop the transition",
                            "uniform rhythm flags machine authorship")),
]


def run(tool, args):
    try:
        r = subprocess.run([sys.executable, str(HERE / tool)] + args, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr
    except Exception as e:  # noqa: BLE001
        return 2, f"(could not run {tool}: {e})"


def teach_blocks(combined: str):
    out = []
    low = combined.lower()
    for token, (root, fix, impact) in TEACH:
        if token.lower() in low:
            out.append((token, root, fix, impact))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paper")
    ap.add_argument("--root", default=".")
    ap.add_argument("--min-words", type=int)
    ap.add_argument("--max-words", type=int)
    ap.add_argument("--tex-root")
    ap.add_argument("--require-through", choices=list("ABCDE"))
    ap.add_argument("--out")
    ap.add_argument("--advisory-only", action="store_true")
    a = ap.parse_args()
    if not Path(a.paper).is_file():
        print(f"ERROR: not a file: {a.paper}", file=sys.stderr)
        return 2

    cu = ["--advisory-only", a.paper]  # capture findings without letting cu's code dominate
    if a.min_words:
        cu = ["--min-words", str(a.min_words)] + cu
    if a.max_words:
        cu = ["--max-words", str(a.max_words)] + cu
    if a.tex_root:
        cu = ["--tex-root", a.tex_root] + cu

    ac_args = ["--root", a.root]
    if a.require_through:
        ac_args += ["--require-through", a.require_through]

    results = {
        "artifact_check": run("artifact_check.py", ac_args),
        "check_universal": run("check_universal.py", cu),
        "humanize_check": run("humanize_check.py", [a.paper, "--advisory-only"]),
    }
    # real (non-advisory) verdicts for the exit code:
    rc_universal, _ = run("check_universal.py", [x for x in cu if x != "--advisory-only"])
    rc_humanize, _ = run("humanize_check.py", [a.paper])
    rc_artifact = results["artifact_check"][0] if a.require_through else 0

    combined = "\n".join(o for _, o in results.values())
    blocks = teach_blocks(combined)
    hard_fail = (rc_universal == 1) or (rc_humanize == 1) or (rc_artifact == 1)

    lines = [f"# hci-spine teaching audit :: {Path(a.paper).name}", "",
             f"- artifact_check: {'FAIL' if rc_artifact == 1 else 'ok'}"
             f"  | check_universal: {'FAIL' if rc_universal == 1 else 'ok'}"
             f"  | humanize_check: {'FAIL' if rc_humanize == 1 else 'ok'}", ""]
    if blocks:
        lines.append("## Findings (teaching form)")
        for token, root, fix, impact in blocks:
            lines += [f"### {token}",
                      f"- **What/Where:** see the lint output for `{token}`.",
                      f"- **Root cause:** {root}",
                      f"- **Fix:** {fix}",
                      f"- **Downstream impact:** {impact}", ""]
    else:
        lines.append("No teachable findings detected by the lints.")
    lines += ["", "## Raw lint output", ""]
    for name, (rc, o) in results.items():
        lines += [f"<details><summary>{name} (advisory rc={rc})</summary>", "", "```", o.strip(), "```", "</details>", ""]
    lines.append(f"## Verdict: {'HARD-FAIL' if hard_fail else 'PASS'}")
    report = "\n".join(lines) + "\n"

    if a.out:
        Path(a.out).write_text(report, encoding="utf-8")
        print(f"teaching audit → {a.out} ({'HARD-FAIL' if hard_fail else 'PASS'})")
    else:
        print(report)
    return 0 if (a.advisory_only or not hard_fail) else 1


if __name__ == "__main__":
    raise SystemExit(main())
