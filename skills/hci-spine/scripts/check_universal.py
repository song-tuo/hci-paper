#!/usr/bin/env python3
"""hci-spine universal honesty lint (genre-agnostic).

HARD gates (affect exit code) — submission-completeness:
  - word count vs venue range (min AND max enforced independently)
  - unresolved citation placeholders (⏳ / "at LaTeX time" / empty \\cite{} / CITEME / TODO)
  - placeholder figure/table markers ([Figure: …] / [Table N])
  - LaTeX: \\input/\\include targets, \\includegraphics files, \\bibliography .bib all exist
  - LaTeX: every \\cite key resolves in the bib(s)
  - anonymity leaks (with --anonymous)
  - unresolved references in a compile log (with --log)

ADVISORY (surfaced, never fail): absolute-quantifier lines, breakdown↔total candidates,
multiple sample denominators — cannot be auto-judged, shown for human/Codex review.

Fenced code blocks and LaTeX comments are skipped so prose that *discusses*
placeholders is not falsely flagged.

Usage:
  check_universal.py PAPER [--min-words N] [--max-words N] [--tex-root DIR]
                     [--bib B ...] [--log FILE] [--anonymous] [--advisory-only]
Exit: 0 clean (or --advisory-only); 1 HARD-FAIL; 2 bad input.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PLACEHOLDER_CITE = re.compile(r"(⏳|at LaTeX time|\[citation needed\]|\\cite\{\s*\}|\bCITEME\b|\bTODO\b)", re.I)
PLACEHOLDER_FIG = re.compile(r"(\[Figure[:\s\]]|\[Table\b|\[TODO\b)", re.I)
ABSOLUTE = re.compile(r"\b(never|always|all|none|every|100\s*%|no\s+\w+\s+(?:ever|at all))\b", re.I)
TOTAL_LINE = re.compile(r"\b(total|controls|overall|in total|sum)\b", re.I)
DENOM = re.compile(r"\b(\d{1,6})\s+(images?|runs?|participants?|trials?|samples?|pairs?|controls?|corpora|corpus|items?)\b", re.I)
INT = re.compile(r"\d[\d,]*")
ANON = re.compile(r"(\\author\{[^}]*[A-Za-z]{2,}[^}]*\}|\\thanks\{|acknowledg|our (?:prior|previous) work|@[\w.]+\.\w+)", re.I)
TEX_INPUT = re.compile(r"\\(?:input|include)\{([^}]+)\}")
TEX_GRAPHIC = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
TEX_BIBLIO = re.compile(r"\\bibliography\{([^}]+)\}")
TEX_CITE = re.compile(r"\\cite[a-zA-Z]*(?:\[[^\]]*\])?\{([^}]+)\}")
BIB_ENTRY = re.compile(r"@\w+\s*\{\s*([^,\s]+)", re.I)


def strip_noise(text: str) -> str:
    """Remove fenced code blocks and LaTeX % comments for prose-level scans."""
    out, in_fence = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append("")
            continue
        if in_fence:
            out.append("")
            continue
        out.append(re.sub(r"(?<!\\)%.*$", "", line))  # drop tex comments (keep \%)
    return "\n".join(out)


def wordcount(text: str) -> int:
    t = re.sub(r"[#*_`>|]+", " ", text)
    t = re.sub(r"\\[a-zA-Z]+\*?", " ", t)
    return len(t.split())


def resolve(root: Path, ref: str, exts) -> bool:
    cand = (root / ref)
    if cand.is_file():
        return True
    return any((root / (ref + e)).is_file() for e in exts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paper")
    ap.add_argument("--min-words", type=int)
    ap.add_argument("--max-words", type=int)
    ap.add_argument("--tex-root")
    ap.add_argument("--bib", action="append", default=[])
    ap.add_argument("--log")
    ap.add_argument("--anonymous", action="store_true")
    ap.add_argument("--advisory-only", action="store_true")
    a = ap.parse_args()

    p = Path(a.paper)
    if not p.is_file():
        print(f"ERROR: not a file: {p}", file=sys.stderr)
        return 2
    raw = p.read_text(encoding="utf-8", errors="replace")
    text = strip_noise(raw)
    lines = text.splitlines()
    root = Path(a.tex_root) if a.tex_root else p.parent
    hard = []

    print(f"== hci-spine universal lint :: {p.name} ==\n")

    # --- word count (min AND max independent) ---
    wc = wordcount(text)
    print(f"[words] {wc}")
    if a.min_words and wc < a.min_words:
        sev = " (SEVERE: <70% of floor)" if wc < int(a.min_words * 0.7) else ""
        hard.append(f"word count {wc} < venue floor {a.min_words}{sev}")
    if a.max_words and wc > a.max_words:
        hard.append(f"word count {wc} > venue max {a.max_words} (by {wc - a.max_words})")
    if a.min_words and a.max_words and a.min_words <= wc <= a.max_words:
        print(f"  ✓ within {a.min_words}–{a.max_words}")

    # --- placeholders ---
    cite_hits = [(i + 1, l.strip()) for i, l in enumerate(lines) if PLACEHOLDER_CITE.search(l)]
    fig_hits = [(i + 1, l.strip()) for i, l in enumerate(lines) if PLACEHOLDER_FIG.search(l)]
    for label, hits in (("citation placeholder", cite_hits), ("figure/table placeholder", fig_hits)):
        if hits:
            hard.append(f"{len(hits)} {label}(s) (e.g. L{hits[0][0]})")
            for ln, s in hits[:8]:
                print(f"  ✗ {label} L{ln}: {s[:84]}")

    # --- LaTeX existence checks (only when commands are present) ---
    inputs = [(i + 1, m) for i, l in enumerate(lines) for m in TEX_INPUT.findall(l)]
    for ln, ref in inputs:
        if not resolve(root, ref, (".tex",)):
            hard.append(f"\\input/\\include target missing: {ref} (L{ln})")
            print(f"  ✗ \\input missing: {ref} (L{ln})")
    graphics = [(i + 1, m) for i, l in enumerate(lines) for m in TEX_GRAPHIC.findall(l)]
    for ln, ref in graphics:
        if not resolve(root, ref, (".pdf", ".png", ".jpg", ".jpeg", ".eps")):
            hard.append(f"\\includegraphics file missing: {ref} (L{ln})")
            print(f"  ✗ figure missing: {ref} (L{ln})")

    # bibliography + cite-key resolution
    bib_keys = set()
    bibs = list(a.bib)
    for l in lines:
        for grp in TEX_BIBLIO.findall(l):
            bibs += [b.strip() for b in grp.split(",")]
    bib_found = False
    for b in bibs:
        bp = root / (b if b.endswith(".bib") else b + ".bib")
        if bp.is_file():
            bib_found = True
            bib_keys |= set(BIB_ENTRY.findall(bp.read_text(encoding="utf-8", errors="replace")))
        else:
            hard.append(f"\\bibliography .bib missing: {b}")
            print(f"  ✗ bib missing: {b}")
    cited = set()
    for l in lines:
        for grp in TEX_CITE.findall(l):
            cited |= {k.strip() for k in grp.split(",") if k.strip()}
    if cited and bib_found:
        unresolved = sorted(cited - bib_keys)
        if unresolved:
            hard.append(f"{len(unresolved)} \\cite key(s) not in bib: {unresolved[:5]}")
            print(f"  ✗ unresolved \\cite keys: {unresolved[:8]}")

    # anonymity
    if a.anonymous:
        anon_hits = [(i + 1, l.strip()) for i, l in enumerate(lines) if ANON.search(l)]
        if anon_hits:
            hard.append(f"{len(anon_hits)} possible anonymity leak(s)")
            for ln, s in anon_hits[:6]:
                print(f"  ✗ anonymity L{ln}: {s[:84]}")

    # compile log
    if a.log:
        lp = Path(a.log)
        if lp.is_file():
            logt = lp.read_text(encoding="utf-8", errors="replace")
            if re.search(r"undefined references|Citation .* undefined|Reference .* undefined", logt, re.I):
                hard.append("compile log reports undefined references/citations")
                print("  ✗ compile log: undefined references/citations present")
        else:
            print(f"  ⚠ --log file not found: {a.log}")

    # --- ADVISORY ---
    abs_hits = [(i + 1, l.strip()) for i, l in enumerate(lines) if ABSOLUTE.search(l)]
    print(f"\n[advisory: absolute quantifiers] {len(abs_hits)} line(s) — check against the paper's own exceptions")
    tot_hits = [(i + 1, l.strip()) for i, l in enumerate(lines) if TOTAL_LINE.search(l) and len(INT.findall(l)) >= 2]
    print(f"[advisory: breakdown↔total] {len(tot_hits)} line(s) with ≥2 numbers — verify parts sum")
    for ln, s in tot_hits[:10]:
        print(f"    L{ln}: {s[:96]}")
    denoms: dict[str, set] = {}
    for l in lines:
        for n, unit in DENOM.findall(l):
            denoms.setdefault(unit.lower().rstrip("s"), set()).add(int(n.replace(",", "")))
    multi = {u: sorted(v) for u, v in denoms.items() if len(v) > 1}
    print(f"[advisory: sample denominators] {multi or '(none)'}")

    print(f"\n== verdict: {'HARD-FAIL — ' + str(len(hard)) + ' issue(s)' if hard else 'PASS'} ==")
    for h in hard:
        print(f"  • {h}")
    return 0 if (a.advisory_only or not hard) else 1


if __name__ == "__main__":
    raise SystemExit(main())
