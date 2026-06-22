#!/usr/bin/env python3
"""Residual-AI / signature-style checker for a finished manuscript (zh + en).

Makes "the prose does not read like AI / violates the signature style" a verifiable
gate INSIDE hci-spine, instead of relying only on the Codex-side polish prompt. Maps
to references/contribution-form-playbooks.md universal checks + the paper-polish-human
signature-style + anti-defensive layers. Fenced code and LaTeX comments are skipped.

HARD (fail): defensive disclaimers; adjective-stacking; >2 negation-first framings;
em-dash connectors over threshold; AI template openers over threshold; simile density
over threshold. ADVISORY (shown): colon-definition pattern.

Usage: humanize_check.py PAPER [--max-emdash 3] [--max-openers 4] [--max-simile-per-1k 4]
                         [--strict] [--advisory-only]
Exit: 0 clean (or --advisory-only); 1 HARD-FAIL; 2 bad input.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFENSIVE = re.compile(r"(我们并不声称|本文并不(主张|是要)|这并不意味着|我们的目的不是.{0,20}而是|"
                       r"\bwe do not claim\b|\bthis does not mean\b|\bwe are not claiming\b|"
                       r"\bour goal is not\b.{0,40}\bbut\b)", re.I)
NEGATION_FIRST = re.compile(r"(不是.{0,30}?而是|没有.{0,30}?只有|不像.{0,30}?更像|\brather than\b|"
                            r"\bnot\b[^.,;]{1,40}?\bbut\b)", re.I)
ADJ_STACK = re.compile(r"(更\S{1,4}更\S{1,4}更|(\S{1,6}的、){2,}\S{1,6}的|(\S{1,8}、){3,})")
# specific simile markers only — bare 像 is excluded (it false-matches 图像/想象/对象…)
SIMILE = re.compile(r"(好像|就像|像是|宛如|犹如|仿佛|彷彿|如同|恰似|有如|像[^,，。；]{1,12}一样|"
                    r"\blike a\b|\bas if\b|\bas though\b)", re.I)
TEMPLATE_OPENER = re.compile(r"^\s*(However|Furthermore|Moreover|In addition|Additionally|Specifically|"
                             r"In particular|Overall|In summary|Notably|综上所述|此外|另外|值得注意的是|"
                             r"总的来说|首先)[,，]", re.I)
COLON_DEF = re.compile(r"^\s*\S{1,12}[:：]\s*\S")
EMDASH = re.compile(r"——|(?<=\S) — (?=\S)")
WORD = re.compile(r"\w+|[一-鿿]")


def strip_noise(text: str) -> str:
    out, fence = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence; out.append(""); continue
        out.append("" if fence else re.sub(r"(?<!\\)%.*$", "", line))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paper")
    ap.add_argument("--max-emdash", type=int, default=3)
    ap.add_argument("--max-openers", type=int, default=4)
    ap.add_argument("--max-simile-per-1k", type=float, default=4.0)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--advisory-only", action="store_true")
    a = ap.parse_args()

    p = Path(a.paper)
    if not p.is_file():
        print(f"ERROR: not a file: {p}", file=sys.stderr)
        return 2
    text = strip_noise(p.read_text(encoding="utf-8", errors="replace"))
    lines = text.splitlines()
    nwords = max(1, len(WORD.findall(text)))

    def hits(rx):
        return [(i + 1, l.strip()) for i, l in enumerate(lines) if rx.search(l)]

    defensive = hits(DEFENSIVE)
    negation = hits(NEGATION_FIRST)
    adj = hits(ADJ_STACK)
    openers = hits(TEMPLATE_OPENER)
    colon = hits(COLON_DEF)
    emdash_n = len(EMDASH.findall(text))
    simile_n = len(SIMILE.findall(text))
    simile_per_1k = simile_n / nwords * 1000

    neg_count = len(NEGATION_FIRST.findall(text))  # occurrences, not lines
    max_emdash = 0 if a.strict else a.max_emdash
    max_openers = 2 if a.strict else a.max_openers
    max_neg = 0 if a.strict else 2

    hard = []
    if defensive:
        hard.append(f"defensive disclaimers ×{len(defensive)} (cut scattered ones; keep one necessary scope sentence)")
    if adj:
        hard.append(f"adjective-stacking / rule-of-three ×{len(adj)}")
    if neg_count > max_neg:
        hard.append(f"negation-first framing ×{neg_count} (> {max_neg})")
    if emdash_n > max_emdash:
        hard.append(f"em-dash connectors ×{emdash_n} (> {max_emdash})")
    if len(openers) > max_openers:
        hard.append(f"AI template openers ×{len(openers)} (> {max_openers})")
    if simile_per_1k > a.max_simile_per_1k:
        hard.append(f"simile density {simile_per_1k:.1f}/1k (> {a.max_simile_per_1k})")

    print(f"== humanize check :: {p.name} ({nwords} tokens) ==\n")
    for label, hs in (("defensive disclaimer", defensive), ("negation-first", negation),
                      ("adjective-stack/rule-of-three", adj), ("AI template opener", openers)):
        if hs:
            print(f"[{label}] ×{len(hs)}")
            for ln, s in hs[:4]:
                print(f"  L{ln}: {s[:84]}")
    print(f"[em-dash connectors] ×{emdash_n}   [similes] ×{simile_n} ({simile_per_1k:.1f}/1k)")
    print(f"[advisory: colon-definition] ×{len(colon)}")
    if colon:
        for ln, s in colon[:3]:
            print(f"  L{ln}: {s[:70]}")

    print(f"\n== {'HARD-FAIL — ' + str(len(hard)) + ' issue(s)' if hard else 'PASS'} ==")
    for h in hard:
        print(f"  • {h}")
    return 0 if (a.advisory_only or not hard) else 1


if __name__ == "__main__":
    raise SystemExit(main())
