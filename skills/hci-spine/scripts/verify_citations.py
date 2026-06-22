#!/usr/bin/env python3
"""Deterministic citation EXISTENCE verifier (Crossref) for hci-spine.

This is the real-verification half that Codex's `cite_verify` role cannot do from
the manuscript alone: it checks each bibliography entry against Crossref (by DOI, or
by bibliographic title match). The Codex role judges claim SUPPORT; this judges
EXISTENCE. Together they close the hallucinated-citation gap.

Input: a BibTeX .bib file. Output: JSON {citations:[{key,doi,found,matched_title,score,note}],summary}.
  found ∈ {yes, no, unverified}. `unverified` = offline/error/no DOI+title (never silently "yes").

Usage:
  verify_citations.py REFS.bib [--out FILE] [--offline] [--email you@x] [--timeout 10]
Exit: 0 if every entry is yes/unverified; 1 if any entry is `no` (likely fabricated);
      2 on bad input. (`--strict` makes `unverified` also nonzero.)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ENTRY = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)\n\}", re.S)
FIELD = re.compile(r"(\w+)\s*=\s*[{\"](.+?)[}\"]\s*,?\s*$", re.M)


def norm(t: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", t.lower()).split())


def jaccard(a: str, b: str) -> float:
    sa, sb = set(a.split()), set(b.split())
    return len(sa & sb) / len(sa | sb) if sa and sb else 0.0


def parse_bib(text: str):
    out = []
    for m in ENTRY.finditer(text):
        key, body = m.group(2), m.group(3)
        fields = {k.lower(): v.strip() for k, v in FIELD.findall(body)}
        out.append({"key": key, "title": fields.get("title", ""), "doi": fields.get("doi", ""),
                    "year": fields.get("year", "")})
    return out


def user_agent(email: str | None) -> str:
    return f"hci-spine/1.0 (mailto:{email})" if email else "hci-spine/1.0"


def http_json(url: str, email: str | None, timeout: int):
    req = urllib.request.Request(url, headers={"User-Agent": user_agent(email)})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def verify_one(e: dict, email: str, timeout: int) -> dict:
    key, title, doi = e["key"], e["title"], e["doi"]
    if doi:
        try:
            d = http_json(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}", email, timeout)
            ct = (d.get("message", {}).get("title") or [""])[0]
            return {"key": key, "doi": doi, "found": "yes", "matched_title": ct, "score": 1.0,
                    "note": "DOI resolves on Crossref"}
        except Exception as ex:  # noqa: BLE001
            return {"key": key, "doi": doi, "found": "no", "matched_title": "", "score": 0.0,
                    "note": f"DOI did not resolve ({type(ex).__name__})"}
    if title:
        try:
            q = urllib.parse.urlencode({"query.bibliographic": title, "rows": 5})
            d = http_json(f"https://api.crossref.org/works?{q}", email, timeout)
            best, bt = 0.0, ""
            for it in d.get("message", {}).get("items", []):
                cand = (it.get("title") or [""])[0]
                s = jaccard(norm(title), norm(cand))
                if s > best:
                    best, bt = s, cand
            found = "yes" if best >= 0.6 else "no"
            return {"key": key, "doi": "", "found": found, "matched_title": bt, "score": round(best, 2),
                    "note": "title match on Crossref" if found == "yes" else "no close title match"}
        except Exception as ex:  # noqa: BLE001
            return {"key": key, "doi": "", "found": "unverified", "matched_title": "", "score": 0.0,
                    "note": f"lookup error ({type(ex).__name__})"}
    return {"key": key, "doi": "", "found": "unverified", "matched_title": "", "score": 0.0,
            "note": "no DOI and no title to verify"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bib")
    ap.add_argument("--out")
    ap.add_argument("--offline", action="store_true", help="parse only; mark all unverified (no network)")
    ap.add_argument("--strict", action="store_true", help="treat `unverified` as failure too")
    ap.add_argument(
        "--email",
        default=os.environ.get("CROSSREF_MAILTO"),
        help="optional contact email for Crossref User-Agent; can also use CROSSREF_MAILTO",
    )
    ap.add_argument("--timeout", type=int, default=10)
    a = ap.parse_args()

    p = Path(a.bib)
    if not p.is_file():
        print(f"ERROR: not a file: {p}", file=sys.stderr)
        return 2
    entries = parse_bib(p.read_text(encoding="utf-8", errors="replace"))
    if not entries:
        print("ERROR: no BibTeX entries parsed", file=sys.stderr)
        return 2

    if a.offline:
        cites = [{"key": e["key"], "doi": e["doi"], "found": "unverified", "matched_title": "",
                  "score": 0.0, "note": "offline mode — not checked"} for e in entries]
    else:
        cites = [verify_one(e, a.email, a.timeout) for e in entries]

    n_no = sum(1 for c in cites if c["found"] == "no")
    n_unv = sum(1 for c in cites if c["found"] == "unverified")
    result = {"citations": cites,
              "summary": f"{len(cites)} entries: {len(cites)-n_no-n_unv} verified, {n_no} not found, {n_unv} unverified"}
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if a.out:
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    for c in cites:
        if c["found"] == "no":
            print(f"  ✗ NOT FOUND: {c['key']} — {c['note']}", file=sys.stderr)
    fail = n_no > 0 or (a.strict and n_unv > 0)
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
