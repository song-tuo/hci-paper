#!/usr/bin/env python3
"""hci-spine project state machine — the operating-system core.

Holds dynamic project state (not just the flow) in HCI_STATE.json and enforces the
HCI research lifecycle:

  forge → lock → prototype_gate → ethics → study_design → pilot
        → instrumentation → data_freeze → analysis → claim_lock → paper

`forge` is exploratory: NO contribution type is forced. The type is chosen between
`lock` and `prototype_gate`. Each phase transition has an entry gate; `advance`
refuses (and records a blocker) when a gate is unmet, unless `--force` (which logs an
override to the decision ledger).

Anti-drift: `manifest` scans the project dir and regenerates OUTPUT_MANIFEST.md from
the filesystem, flagging files claimed-in-state-but-missing and present-but-unrecorded.

Stdlib only. Usage: hci_state.py <cmd> [...] (run with -h).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

STATE_FILE = "HCI_STATE.json"
SCHEMA_VERSION = "1.0"

PHASES = [
    "forge", "lock", "prototype_gate", "ethics", "study_design", "pilot",
    "instrumentation", "data_freeze", "analysis", "claim_lock", "paper",
]

# Contribution FORM (not area, not venue, not tradition) — refactored model.
CONTRIBUTION_FORMS = [
    "empirical", "artifact", "method", "conceptual_theoretical",
    "dataset_corpus", "critical_artistic", "replication",
]

MANAGED_FILES = {
    STATE_FILE, "OUTPUT_MANIFEST.md", "PROJECT_ANCHOR.md",
    "DECISION_LEDGER.md", "CLAIM_EVIDENCE_LEDGER.md", "HANDOFF.md",
}

NEXT_STEP_HINTS = {
    "forge": "explore options; record deprecated alternatives (`deprecate`); RED-TEAM #1 (idea kill via kill-argument); then `lock`",
    "lock": "set the contribution form (`set-type`), then `advance` to prototype_gate",
    "prototype_gate": "RED-TEAM #2 (media/AI necessity): fill PROJECT_ANCHOR media judgment, `attest media_necessity`, then advance to ethics",
    "ethics": "obtain ethics review; `attest ethics_note` (or `ethics_exempt`)",
    "study_design": "RED-TEAM #3 (study-design attack) BEFORE data; finalize design; `attest study_design`",
    "pilot": "run the pilot; `attest pilot`",
    "instrumentation": "wire instrumentation/logging; `attest instrumentation`",
    "data_freeze": "freeze raw data; `attest data_freeze`",
    "analysis": "run analysis; log claims to CLAIM_EVIDENCE_LEDGER; `claims --count N`",
    "claim_lock": "lock claims to evidence; `attest claim_lock`",
    "paper": "draft (form template) → GATE C lint → GATE D review (RED-TEAM #4) → two-stage polish → GATE E audit → submit",
}


def set_next(s: dict) -> None:
    s["next_step"] = NEXT_STEP_HINTS.get(s.get("lifecycle_phase", ""), "")


# Gate: target_phase -> list of (label, predicate(state)->bool). All must hold.
def _has_attest(s, key):
    return key in s.get("attestations", {})

GATES = {
    "lock": [
        ("locked_motivation is set", lambda s: bool(s.get("locked_motivation"))),
        ("≥1 deprecated option recorded (alternatives considered)",
         lambda s: len(s.get("deprecated_options", [])) >= 1),
    ],
    "prototype_gate": [
        ("contribution.primary_form is set",
         lambda s: s.get("contribution", {}).get("primary_form") in CONTRIBUTION_FORMS),
    ],
    "ethics": [
        ("media_necessity attested (why-not-paper/screen, AI removable, etc.)",
         lambda s: _has_attest(s, "media_necessity")),
    ],
    "study_design": [
        ("ethics attested (ethics_note OR ethics_exempt)",
         lambda s: _has_attest(s, "ethics_note") or _has_attest(s, "ethics_exempt")),
    ],
    "pilot": [
        ("study_design attested", lambda s: _has_attest(s, "study_design")),
    ],
    "instrumentation": [
        ("pilot attested", lambda s: _has_attest(s, "pilot")),
    ],
    "data_freeze": [
        ("instrumentation attested", lambda s: _has_attest(s, "instrumentation")),
    ],
    "analysis": [
        ("data_freeze attested", lambda s: _has_attest(s, "data_freeze")),
    ],
    "claim_lock": [
        ("≥1 claim in CLAIM_EVIDENCE_LEDGER",
         lambda s: s.get("claim_count", 0) >= 1),
        ("no HIGH-severity blocker open",
         lambda s: not any(b.get("severity") == "HIGH" for b in s.get("blockers", []))),
    ],
    "paper": [
        ("claim_lock attested", lambda s: _has_attest(s, "claim_lock")),
    ],
}


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def sha8(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:8]
    except OSError:
        return "????????"


def state_path(root: Path) -> Path:
    return root / STATE_FILE


def load(root: Path) -> dict:
    p = state_path(root)
    if not p.is_file():
        sys.exit(f"no {STATE_FILE} in {root} — run `hci_state.py init` first")
    return json.loads(p.read_text(encoding="utf-8"))


def save(root: Path, s: dict) -> None:
    s["updated_at"] = now()
    state_path(root).write_text(json.dumps(s, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_ledger(root: Path, fname: str, line: str) -> None:
    f = root / fname
    head = "" if f.exists() else f"# {fname.replace('.md','').replace('_',' ').title()}\n\n"
    with f.open("a", encoding="utf-8") as fh:
        fh.write(head + f"- {now()} — {line}\n")


# --------------------------------------------------------------------------- #
def cmd_init(root: Path, a) -> int:
    p = state_path(root)
    if p.exists() and not a.force:
        sys.exit(f"{p} already exists (use --force to reset)")
    s = {
        "schema_version": SCHEMA_VERSION,
        "project": a.project,
        "venue": {"name": a.venue or "", "deadline": a.deadline or "",
                  "word_min": a.word_min, "word_max": a.word_max},
        "lifecycle_phase": "forge",
        "contribution": {"primary_form": None, "secondary_form": None,
                         "research_area": a.area or "", "tradition": a.tradition or ""},
        "locked_motivation": None,
        "deprecated_options": [],
        "latest_inputs": [],
        "verified_outputs": [],
        "blockers": [],
        "attestations": {},
        "claim_count": 0,
        "next_step": "forge: explore options; record deprecated alternatives; then `lock` the motivation",
        "gates_passed": [],
        "updated_at": now(),
    }
    save(root, s)
    for fn in ("PROJECT_ANCHOR.md", "DECISION_LEDGER.md", "CLAIM_EVIDENCE_LEDGER.md", "HANDOFF.md"):
        if not (root / fn).exists():
            (root / fn).write_text(f"# {fn[:-3].replace('_',' ').title()}\n\n_(managed by hci_state.py)_\n", encoding="utf-8")
    print(f"initialized {p} @ phase=forge")
    return 0


def _gate_report(s: dict, target: str) -> list:
    return [(label, pred(s)) for label, pred in GATES.get(target, [])]


def cmd_status(root: Path, a) -> int:
    s = load(root)
    cur = s["lifecycle_phase"]
    i = PHASES.index(cur)
    nxt = PHASES[i + 1] if i + 1 < len(PHASES) else None
    print(f"project: {s['project']}   phase: {cur}   venue: {s['venue'].get('name') or '—'}")
    print(f"motivation: {'LOCKED' if s.get('locked_motivation') else '(unlocked)'}")
    cf = s.get("contribution", {})
    print(f"contribution: primary={cf.get('primary_form')} secondary={cf.get('secondary_form')} "
          f"area={cf.get('research_area') or '—'}")
    if s.get("blockers"):
        print("blockers:")
        for b in s["blockers"]:
            print(f"  [{b.get('severity','?')}] {b.get('id','')}: {b.get('desc','')}")
    if nxt:
        print(f"\nnext gate → {nxt}:")
        for label, ok in _gate_report(s, nxt):
            print(f"  [{'✓' if ok else '✗'}] {label}")
    else:
        print("\nat final phase (paper).")
    print(f"\nnext_step: {s.get('next_step','')}")
    return 0


def cmd_lock(root: Path, a) -> int:
    s = load(root)
    s["locked_motivation"] = a.motivation
    append_ledger(root, "DECISION_LEDGER.md", f"LOCK motivation: {a.motivation}")
    anchor = root / "PROJECT_ANCHOR.md"
    anchor.write_text(
        f"# Project Anchor\n\n## Locked motivation\n{a.motivation}\n\n"
        "## Media judgment (fill before prototype_gate→ethics)\n"
        "- Why not paper / a plain screen?\n- Is the AI removable without losing the point?\n"
        "- Does the interaction act participate in meaning-making?\n"
        "- Is the artifact more than a technical assembly (form↔mechanism↔meaning cohere)?\n",
        encoding="utf-8")
    save(root, s)
    print("motivation locked; PROJECT_ANCHOR.md written.")
    return 0


def cmd_set_type(root: Path, a) -> int:
    s = load(root)
    if a.primary not in CONTRIBUTION_FORMS:
        sys.exit(f"primary must be one of {CONTRIBUTION_FORMS}")
    if a.secondary and a.secondary not in CONTRIBUTION_FORMS:
        sys.exit(f"secondary must be one of {CONTRIBUTION_FORMS}")
    s["contribution"].update({
        "primary_form": a.primary,
        "secondary_form": a.secondary,
        "research_area": a.area or s["contribution"].get("research_area", ""),
        "tradition": a.tradition or s["contribution"].get("tradition", ""),
    })
    append_ledger(root, "DECISION_LEDGER.md",
                  f"SET-TYPE primary={a.primary} secondary={a.secondary} area={a.area}")
    save(root, s)
    print(f"contribution form set: primary={a.primary} secondary={a.secondary}")
    return 0


def cmd_deprecate(root: Path, a) -> int:
    s = load(root)
    s["deprecated_options"].append({"option": a.option, "reason": a.reason, "at": now()})
    append_ledger(root, "DECISION_LEDGER.md", f"DEPRECATE: {a.option} — {a.reason}")
    save(root, s)
    print(f"deprecated: {a.option}")
    return 0


def cmd_attest(root: Path, a) -> int:
    s = load(root)
    s.setdefault("attestations", {})[a.key] = {"by": a.by, "note": a.note or "", "at": now()}
    append_ledger(root, "DECISION_LEDGER.md", f"ATTEST {a.key} (by {a.by}): {a.note or ''}")
    save(root, s)
    print(f"attested: {a.key}")
    return 0


def cmd_blocker(root: Path, a) -> int:
    s = load(root)
    if a.action == "add":
        s["blockers"].append({"id": a.id, "desc": a.desc or "", "severity": a.severity, "since": now()})
    elif a.action == "clear":
        s["blockers"] = [b for b in s["blockers"] if b.get("id") != a.id]
    save(root, s)
    print(f"blocker {a.action}: {a.id}")
    return 0


def cmd_record(root: Path, a) -> int:
    """record an input or a verified output with its sha."""
    s = load(root)
    fp = (root / a.path)
    if not fp.is_file():
        sys.exit(f"cannot record missing/non-file path: {fp}")
    entry = {"path": a.path, "sha": sha8(fp), "at": now()}
    if a.kind == "input":
        s["latest_inputs"] = [e for e in s["latest_inputs"] if e["path"] != a.path] + [entry]
    else:
        entry["verified_by"] = a.verified_by or "unspecified"
        s["verified_outputs"] = [e for e in s["verified_outputs"] if e["path"] != a.path] + [entry]
    save(root, s)
    print(f"recorded {a.kind}: {a.path} ({entry['sha']})")
    return 0


def cmd_claims(root: Path, a) -> int:
    s = load(root)
    s["claim_count"] = a.count
    save(root, s)
    print(f"claim_count set to {a.count}")
    return 0


def cmd_advance(root: Path, a) -> int:
    s = load(root)
    cur = s["lifecycle_phase"]
    i = PHASES.index(cur)
    target = a.to or (PHASES[i + 1] if i + 1 < len(PHASES) else None)
    if target is None:
        sys.exit("already at final phase (paper)")
    if target not in PHASES or PHASES.index(target) != i + 1:
        sys.exit(f"can only advance to the next phase ({PHASES[i+1] if i+1<len(PHASES) else 'none'}); got {target}")
    report = _gate_report(s, target)
    unmet = [label for label, ok in report if not ok]
    if unmet and not a.force:
        print(f"BLOCKED: cannot advance {cur} → {target}. Unmet gate(s):")
        for u in unmet:
            print(f"  ✗ {u}")
        s["blockers"].append({"id": f"gate:{target}", "desc": "; ".join(unmet),
                              "severity": "HIGH", "since": now()})
        save(root, s)
        return 1
    if unmet and a.force:
        append_ledger(root, "DECISION_LEDGER.md",
                      f"FORCE advance {cur}→{target} despite: {'; '.join(unmet)}")
    s["lifecycle_phase"] = target
    s["gates_passed"] = sorted(set(s.get("gates_passed", []) + [target]))
    s["blockers"] = [b for b in s["blockers"] if b.get("id") != f"gate:{target}"]
    set_next(s)
    save(root, s)
    print(f"advanced {cur} → {target}" + (" (forced)" if unmet else ""))
    return 0


def cmd_manifest(root: Path, a) -> int:
    """Scan the dir and regenerate OUTPUT_MANIFEST.md — kills state↔fs drift."""
    s = load(root)
    ignore = {".git", "__pycache__", ".aris", "node_modules"}
    files = []
    for f in sorted(root.rglob("*")):
        if f.is_file() and not any(part in ignore for part in f.parts):
            rel = f.relative_to(root).as_posix()
            files.append((rel, sha8(f), f.stat().st_size))
    recorded = {e["path"] for e in s.get("verified_outputs", [])}
    present = {rel for rel, _, _ in files}
    missing = sorted(recorded - present)        # claimed in state, not on disk
    unrecorded = sorted(present - recorded - MANAGED_FILES)

    lines = [f"# Output Manifest", "", f"_Generated {now()} by hci_state.py — do not hand-edit._",
             f"", f"Files on disk: {len(files)} | verified outputs in state: {len(recorded)}", ""]
    lines.append("| file | sha8 | bytes | verified |")
    lines.append("|---|---|---|---|")
    for rel, sh, size in files:
        lines.append(f"| {rel} | `{sh}` | {size} | {'✓' if rel in recorded else ''} |")
    if missing:
        lines += ["", "## ⚠ Drift: recorded as verified but MISSING on disk"] + [f"- {m}" for m in missing]
    if unrecorded:
        lines += ["", "## Present on disk but NOT recorded as verified output"] + [f"- {u}" for u in unrecorded]
    (root / "OUTPUT_MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OUTPUT_MANIFEST.md: {len(files)} files; {len(missing)} missing, {len(unrecorded)} unrecorded")
    return 1 if missing else 0


def cmd_handoff(root: Path, a) -> int:
    """Regenerate HANDOFF.md from state so a fresh session can resume cold."""
    s = load(root)
    cur = s["lifecycle_phase"]
    i = PHASES.index(cur)
    nxt = PHASES[i + 1] if i + 1 < len(PHASES) else None
    gates = _gate_report(s, nxt) if nxt else []
    out = [
        "# Handoff", "", f"_Generated {now()} from HCI_STATE.json._", "",
        f"- **Project:** {s['project']}", f"- **Phase:** {cur}",
        f"- **Venue:** {s['venue'].get('name') or '—'} (deadline {s['venue'].get('deadline') or '—'})",
        f"- **Motivation:** {'LOCKED — ' + s['locked_motivation'] if s.get('locked_motivation') else '(unlocked)'}",
        f"- **Contribution:** primary={s['contribution'].get('primary_form')} "
        f"secondary={s['contribution'].get('secondary_form')} area={s['contribution'].get('research_area') or '—'}",
        f"- **Next step:** {s.get('next_step','')}", "",
        "## Open blockers",
    ]
    out += [f"- [{b.get('severity')}] {b.get('id')}: {b.get('desc')}" for b in s.get("blockers", [])] or ["- none"]
    out += ["", f"## Gate to {nxt or '(final)'}"]
    out += [f"- [{'x' if ok else ' '}] {label}" for label, ok in gates] or ["- (at final phase)"]
    out += ["", "## Deprecated options (do not revisit)"]
    out += [f"- {d['option']} — {d['reason']}" for d in s.get("deprecated_options", [])] or ["- none"]
    (root / "HANDOFF.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("HANDOFF.md regenerated.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="hci-spine project state machine")
    ap.add_argument("--root", default=".", help="project root holding HCI_STATE.json")
    sub = ap.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("init"); pi.add_argument("--project", required=True)
    pi.add_argument("--venue"); pi.add_argument("--deadline")
    pi.add_argument("--word-min", type=int); pi.add_argument("--word-max", type=int)
    pi.add_argument("--area"); pi.add_argument("--tradition"); pi.add_argument("--force", action="store_true")

    sub.add_parser("status")
    pl = sub.add_parser("lock"); pl.add_argument("--motivation", required=True)
    pt = sub.add_parser("set-type"); pt.add_argument("--primary", required=True)
    pt.add_argument("--secondary"); pt.add_argument("--area"); pt.add_argument("--tradition")
    pd = sub.add_parser("deprecate"); pd.add_argument("--option", required=True); pd.add_argument("--reason", required=True)
    pa = sub.add_parser("attest"); pa.add_argument("key"); pa.add_argument("--by", default="user"); pa.add_argument("--note")
    pb = sub.add_parser("blocker"); pb.add_argument("action", choices=["add", "clear"])
    pb.add_argument("--id", required=True); pb.add_argument("--desc"); pb.add_argument("--severity", default="MED", choices=["LOW", "MED", "HIGH"])
    pr = sub.add_parser("record"); pr.add_argument("kind", choices=["input", "output"])
    pr.add_argument("--path", required=True); pr.add_argument("--verified-by")
    pc = sub.add_parser("claims"); pc.add_argument("--count", type=int, required=True)
    pv = sub.add_parser("advance"); pv.add_argument("--to"); pv.add_argument("--force", action="store_true")
    sub.add_parser("manifest")
    sub.add_parser("handoff")

    a = ap.parse_args()
    root = Path(a.root).resolve()
    dispatch = {
        "init": cmd_init, "status": cmd_status, "lock": cmd_lock, "set-type": cmd_set_type,
        "deprecate": cmd_deprecate, "attest": cmd_attest, "blocker": cmd_blocker,
        "record": cmd_record, "claims": cmd_claims, "advance": cmd_advance,
        "manifest": cmd_manifest, "handoff": cmd_handoff,
    }
    return dispatch[a.cmd](root, a)


if __name__ == "__main__":
    raise SystemExit(main())
