#!/usr/bin/env python3
"""Coverage guard for an hci-spine translation package.

For every scaffolded artifact in translation_<lang>/, require: (1) the [TODO-TRANSLATE]
sentinel is gone (it was actually translated), and (2) the table-row count matches the
source 1:1 (no dropped/added rows in large tabular files). Mirrors translate_guard.

Usage: translate_guard.py [--root DIR] [--lang zh] [--output-dir hci_spine_output]
Exit: 0 PASS; 1 incomplete; 2 no package.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import hci_translate as T  # reuse SOURCES / MANUSCRIPTS / find / SENTINEL


def table_rows(text: str) -> int:
    n = 0
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("|") and set(s) - set("|:- "):  # a | row that is not a separator
            n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--lang", default="zh")
    ap.add_argument("--output-dir", default="hci_spine_output")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    outdir = root / a.output_dir
    tdir = root / f"translation_{a.lang}"
    if not tdir.is_dir():
        print(f"ERROR: no translation_{a.lang}/ — run hci_translate.py first", file=sys.stderr)
        return 2

    # rebuild the expected source set the same way the scaffolder did
    expected = []
    for rel in T.SOURCES:
        p = T.find(root, outdir, rel)
        if p:
            expected.append((rel, p))
    for rel in T.MANUSCRIPTS:
        p = T.find(root, outdir, rel)
        if p:
            expected.append((Path(rel).name, p)); break

    issues = []
    for relname, src in expected:
        tf = tdir / relname
        if not tf.is_file():
            issues.append(f"{relname}: MISSING translation"); continue
        tt = tf.read_text(encoding="utf-8", errors="replace")
        if T.SENTINEL in tt:
            issues.append(f"{relname}: still has {T.SENTINEL} (untranslated)")
        sr, tr = table_rows(src.read_text(encoding="utf-8", errors="replace")), table_rows(tt)
        if sr != tr:
            issues.append(f"{relname}: table rows {tr} ≠ source {sr} (row parity broken)")

    print(f"== translate_guard ({a.lang}) :: {len(expected)} artifact(s) ==")
    for i in issues:
        print(f"  ✗ {i}")
    print(f"\n== {'PASS' if not issues else 'INCOMPLETE (' + str(len(issues)) + ')'} ==")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
