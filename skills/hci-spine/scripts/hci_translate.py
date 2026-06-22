#!/usr/bin/env python3
"""Scaffold a translation package (translation_<lang>/) for hci-spine deliverables.

Translation itself is an LLM task; this enumerates the artifacts that MUST be
translated and writes a structure-preserving scaffold for each (verbatim source +
a [TODO-TRANSLATE] sentinel + table rows reproduced 1:1 so the translator keeps row
parity). `translate_guard.py` then enforces coverage. Mirrors paper-spine-translate.

Usage: hci_translate.py [--root DIR] [--lang zh] [--output-dir hci_spine_output]
Exit: 0 on scaffold; 2 if nothing to translate.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SENTINEL = "[TODO-TRANSLATE]"
# default deliverables to translate (only those that exist are scaffolded)
SOURCES = [
    "PROJECT_ANCHOR.md", "confirmed_motivation.md", "contribution_form.md",
    "research_dossier.md", "sota_gap_map.md", "citation_support_bank.md",
    "section_blueprints.md", "hci_rationale_matrix.md",
    "review_synthesis.md", "rebuttal_kit.md",
]
MANUSCRIPTS = ["final_paper/main.tex", "draft.md", "06_paper/draft.md", "paper.md"]


def find(root: Path, outdir: Path, rel: str):
    for base in (root, outdir):
        p = base / rel
        if p.is_file():
            return p
    return None


def scaffold(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"<!-- TRANSLATE FROM: {src.name} | replace each line; KEEP table rows 1:1 -->",
             f"<!-- {SENTINEL}: delete this sentinel only when fully translated -->", ""]
    lines += src.read_text(encoding="utf-8", errors="replace").splitlines()
    dst.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--lang", default="zh")
    ap.add_argument("--output-dir", default="hci_spine_output")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    outdir = root / a.output_dir
    tdir = root / f"translation_{a.lang}"

    found = []
    for rel in SOURCES:
        p = find(root, outdir, rel)
        if p:
            found.append((rel, p))
    for rel in MANUSCRIPTS:
        p = find(root, outdir, rel)
        if p:
            found.append((Path(rel).name, p)); break  # one manuscript

    if not found:
        print("ERROR: no translatable deliverables found", file=sys.stderr)
        return 2

    for relname, p in found:
        scaffold(p, tdir / relname)
    (tdir / "TRANSLATION_INDEX.md").write_text(
        f"# Translation package ({a.lang})\n\nScaffolded {len(found)} artifact(s). "
        f"Translate each in place, remove the {SENTINEL} sentinel, keep table rows 1:1. "
        "Then run `translate_guard.py`.\n\n" +
        "\n".join(f"- {n}" for n, _ in found) + "\n", encoding="utf-8")
    print(f"scaffolded translation_{a.lang}/ with {len(found)} artifact(s) (+ TRANSLATION_INDEX.md)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
