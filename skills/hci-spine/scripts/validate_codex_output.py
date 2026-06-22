#!/usr/bin/env python3
"""Validate structured Codex-role output (cite_verify / data_audit).

The codex output file wraps JSON in a fenced block with header lines; this extracts
the JSON object and checks it against the role's contract (required fields + enums).
Lightweight, stdlib-only — no jsonschema dependency.

Usage: validate_codex_output.py --role {cite_verify,data_audit} FILE
Exit: 0 valid; 1 invalid; 2 bad input / no JSON found.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SPEC = {
    "cite_verify": {
        "array": "citations",
        "item_required": ["key", "exists", "claim_supported", "note"],
        "enums": {"exists": {"yes", "no", "unsure"},
                  "claim_supported": {"yes", "partial", "no", "unsure"}},
    },
    "data_audit": {
        "array": "claims",
        "item_required": ["claim", "evidence_file", "verdict", "note"],
        "enums": {"verdict": {"supported", "partial", "unsupported", "no_evidence"}},
    },
}


def extract_json(text: str):
    """Return the JSON object in text (whole-file, or first '{'..last '}')."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    i, j = text.find("{"), text.rfind("}")
    if i == -1 or j == -1 or j <= i:
        return None
    try:
        return json.loads(text[i:j + 1])
    except json.JSONDecodeError:
        return None


def validate(role: str, obj) -> list:
    spec = SPEC[role]
    errs = []
    if not isinstance(obj, dict):
        return ["top-level value is not an object"]
    if "summary" not in obj:
        errs.append("missing 'summary'")
    arr = obj.get(spec["array"])
    if not isinstance(arr, list):
        return errs + [f"missing/invalid array '{spec['array']}'"]
    if not arr:
        errs.append(f"'{spec['array']}' is empty")
    for idx, item in enumerate(arr):
        if not isinstance(item, dict):
            errs.append(f"[{idx}] not an object"); continue
        for k in spec["item_required"]:
            if k not in item:
                errs.append(f"[{idx}] missing '{k}'")
        for field, allowed in spec["enums"].items():
            if field in item and item[field] not in allowed:
                errs.append(f"[{idx}] {field}={item[field]!r} not in {sorted(allowed)}")
    # anti-vacuous: a verification that determined nothing is NOT a pass.
    if role == "cite_verify" and arr and all(it.get("exists") == "unsure" for it in arr if isinstance(it, dict)):
        errs.append("every citation is 'unsure' — no real existence verification was performed "
                    "(run verify_citations.py against Crossref for the existence half)")
    if role == "data_audit" and arr and all(it.get("verdict") == "no_evidence" for it in arr if isinstance(it, dict)):
        errs.append("every claim is 'no_evidence' — audit produced no determination")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", required=True, choices=sorted(SPEC))
    ap.add_argument("file")
    a = ap.parse_args()
    p = Path(a.file)
    if not p.is_file():
        print(f"ERROR: not a file: {p}", file=sys.stderr); return 2
    obj = extract_json(p.read_text(encoding="utf-8", errors="replace"))
    if obj is None:
        print("ERROR: no JSON object found in output", file=sys.stderr); return 2
    errs = validate(a.role, obj)
    if errs:
        print(f"INVALID ({a.role}): {len(errs)} issue(s)")
        for e in errs:
            print(f"  ✗ {e}")
        return 1
    n = len(obj[SPEC[a.role]["array"]])
    print(f"VALID ({a.role}): {n} item(s) conform.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
