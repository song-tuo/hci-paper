#!/usr/bin/env python3
"""hci-spine project state machine — the operating-system core.

Holds dynamic project state (HCI_STATE.json) and enforces a FORM-AWARE research
lifecycle with EVIDENCE-BACKED gates (not formal pass-throughs).

Canonical phase order:
  forge → lock → prototype_gate → ethics → study_design → pilot
        → instrumentation → data_freeze → analysis → claim_lock → paper

Each FORM traverses only the phases that apply (FORM_LIFECYCLE); inapplicable
phases are skipped automatically (no --force). `forge` forces no form; `primary_form`
is `undecided` until `lock`. Gates are EXIT requirements of the phase you LEAVE, so a
skipped phase never strands a later gate.

Anti-forgery: `record output` rejects missing files; `attest data_freeze` requires an
existing --evidence path (hashed); claims are counted from CLAIM_EVIDENCE_LEDGER (no
manual count); re-`lock` and post-lock form/motivation changes invalidate downstream
attestations. Stdlib only. Run with -h.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

STATE_FILE = "HCI_STATE.json"
SCHEMA_VERSION = "2.0"
LEDGER = "CLAIM_EVIDENCE_LEDGER.md"

PHASES = [
    "forge", "lock", "prototype_gate", "ethics", "study_design", "pilot",
    "instrumentation", "data_freeze", "analysis", "claim_lock", "paper",
]
CONTRIBUTION_FORMS = [
    "empirical", "artifact", "method", "conceptual_theoretical",
    "dataset_corpus", "critical_artistic", "replication",
]
UNDECIDED = "undecided"

_STUDY = ["ethics", "study_design", "pilot", "instrumentation", "data_freeze", "analysis"]
FORM_LIFECYCLE = {
    "empirical":               ["forge", "lock"] + _STUDY + ["claim_lock", "paper"],
    "replication":            ["forge", "lock"] + _STUDY + ["claim_lock", "paper"],
    "artifact":               ["forge", "lock", "prototype_gate"] + _STUDY + ["claim_lock", "paper"],
    "dataset_corpus":         ["forge", "lock", "ethics", "data_freeze", "analysis", "claim_lock", "paper"],
    "method":                 ["forge", "lock", "analysis", "claim_lock", "paper"],
    "conceptual_theoretical": ["forge", "lock", "claim_lock", "paper"],
    "critical_artistic":      ["forge", "lock", "prototype_gate", "claim_lock", "paper"],
}
UNDECIDED_LIFECYCLE = ["forge", "lock"]  # cannot proceed past lock until a form is set
EVIDENCE_REQUIRED_ATTEST = {"data_freeze"}

NEXT_STEP_HINTS = {
    "forge": "explore options; `deprecate` alternatives; RED-TEAM #1 (idea kill via kill-argument); then `lock`",
    "lock": "set the contribution form (`set-type`), then `advance`",
    "prototype_gate": "RED-TEAM #2 (media/AI necessity): fill PROJECT_ANCHOR media judgment, `attest media_necessity`",
    "ethics": "obtain ethics review; `attest ethics_note` (or `ethics_exempt`)",
    "study_design": "RED-TEAM #3 (study-design attack) BEFORE data; `attest study_design`",
    "pilot": "run the pilot; `attest pilot`",
    "instrumentation": "wire instrumentation; `attest instrumentation`",
    "data_freeze": "freeze raw data; `attest data_freeze --evidence <data path>`",
    "analysis": "log claims with evidence (`claim add --text … --evidence <file>`)",
    "claim_lock": "lock claims to evidence; `attest claim_lock`",
    "paper": "draft (form template) → GATE C lint → GATE D review (RED-TEAM #4) → polish → GATE E audit → submit",
}


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def sha8(path: Path):
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:8]
    except OSError:
        return None


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


CLAIM_LINE = re.compile(r"^- CLAIM:.*\|\s*EVIDENCE:", re.M)


def append_ledger(root: Path, fname: str, line: str) -> None:
    f = root / fname
    head = "" if f.exists() else f"# {fname[:-3].replace('_',' ').title()}\n\n"
    with f.open("a", encoding="utf-8") as fh:
        fh.write(head + f"{line}\n")


def count_claims(root: Path) -> int:
    f = root / LEDGER
    return len(CLAIM_LINE.findall(f.read_text(encoding="utf-8"))) if f.is_file() else 0


def form_of(s: dict):
    return s.get("contribution", {}).get("primary_form")


def active_phases(s: dict):
    base = FORM_LIFECYCLE.get(form_of(s), UNDECIDED_LIFECYCLE)
    na = set(s.get("na_phases", []))
    return [p for p in base if p not in na]


def next_active(s: dict):
    cur = s["lifecycle_phase"]
    act = active_phases(s)
    if cur not in act:
        prior = [p for p in act if PHASES.index(p) <= PHASES.index(cur)]
        cur = prior[-1] if prior else act[0]
    later = [p for p in act if PHASES.index(p) > PHASES.index(cur)]
    return later[0] if later else None


def _attest(s, k):
    return k in s.get("attestations", {})


# EXIT requirements: to LEAVE phase P (keyed by the phase being left).
PHASE_EXIT = {
    "forge": [
        ("locked_motivation is set", lambda s, r: bool(s.get("locked_motivation"))),
        ("≥1 deprecated option recorded", lambda s, r: len(s.get("deprecated_options", [])) >= 1),
    ],
    "lock": [("contribution.primary_form chosen (not undecided)",
              lambda s, r: form_of(s) in CONTRIBUTION_FORMS)],
    "prototype_gate": [("media_necessity attested", lambda s, r: _attest(s, "media_necessity"))],
    "ethics": [("ethics attested (ethics_note OR ethics_exempt)",
                lambda s, r: _attest(s, "ethics_note") or _attest(s, "ethics_exempt"))],
    "study_design": [("study_design attested", lambda s, r: _attest(s, "study_design"))],
    "pilot": [("pilot attested", lambda s, r: _attest(s, "pilot"))],
    "instrumentation": [("instrumentation attested", lambda s, r: _attest(s, "instrumentation"))],
    "data_freeze": [("data_freeze attested with evidence", lambda s, r: _attest(s, "data_freeze"))],
    "analysis": [
        ("≥1 evidence-backed claim in CLAIM_EVIDENCE_LEDGER", lambda s, r: count_claims(r) >= 1),
        ("no HIGH-severity blocker open",
         lambda s, r: not any(b.get("severity") == "HIGH" for b in s.get("blockers", []))),
    ],
    "claim_lock": [("claim_lock attested", lambda s, r: _attest(s, "claim_lock"))],
}


def set_next(s: dict) -> None:
    s["next_step"] = NEXT_STEP_HINTS.get(s.get("lifecycle_phase", ""), "")


def invalidate_downstream(root: Path, s: dict, why: str) -> None:
    if PHASES.index(s["lifecycle_phase"]) <= PHASES.index("lock"):
        return
    s["attestations"] = {}
    s["claim_count"] = 0
    s["lifecycle_phase"] = "lock"
    s["blockers"].append({"id": "stale:downstream", "severity": "HIGH",
                          "desc": f"downstream invalidated: {why}", "since": now()})
    append_ledger(root, "DECISION_LEDGER.md", f"- {now()} — INVALIDATE downstream: {why}")


# --------------------------------------------------------------------------- #
def cmd_init(root: Path, a) -> int:
    p = state_path(root)
    if p.exists() and not a.force:
        sys.exit(f"{p} already exists (use --force to reset)")
    s = {
        "schema_version": SCHEMA_VERSION, "project": a.project,
        "venue": {"name": a.venue or "", "deadline": a.deadline or "",
                  "word_min": a.word_min, "word_max": a.word_max},
        "lifecycle_phase": "forge",
        "contribution": {"primary_form": UNDECIDED, "secondary_form": None,
                         "research_area": a.area or "", "tradition": a.tradition or ""},
        "locked_motivation": None, "deprecated_options": [],
        "latest_inputs": [], "verified_outputs": [], "blockers": [],
        "attestations": {}, "na_phases": [], "claim_count": 0,
        "gates_passed": [], "updated_at": now(),
    }
    set_next(s)
    save(root, s)
    for fn in ("PROJECT_ANCHOR.md", "DECISION_LEDGER.md", LEDGER, "HANDOFF.md"):
        if not (root / fn).exists():
            (root / fn).write_text(f"# {fn[:-3].replace('_',' ').title()}\n\n_(managed by hci_state.py)_\n", encoding="utf-8")
    print(f"initialized {p} @ phase=forge, form=undecided")
    return 0


def cmd_status(root: Path, a) -> int:
    s = load(root); cur = s["lifecycle_phase"]; nxt = next_active(s)
    print(f"project: {s['project']}   phase: {cur}   venue: {s['venue'].get('name') or '—'}")
    print(f"form: {form_of(s)} (+{s['contribution'].get('secondary_form')})   "
          f"motivation: {'LOCKED' if s.get('locked_motivation') else '(unlocked)'}")
    print(f"active lifecycle: {' → '.join(active_phases(s))}")
    for b in s.get("blockers", []):
        print(f"  blocker [{b.get('severity')}] {b.get('id')}: {b.get('desc')}")
    print(f"\nto LEAVE {cur} (→ {nxt or '(final)'}):")
    for label, pred in PHASE_EXIT.get(cur, []):
        print(f"  [{'✓' if pred(s, root) else '✗'}] {label}")
    print(f"\nnext_step: {s.get('next_step','')}")
    return 0


def cmd_lock(root: Path, a) -> int:
    s = load(root)
    if s.get("locked_motivation") and not a.relock:
        sys.exit("motivation already locked; use --relock to overwrite (invalidates downstream)")
    if s.get("locked_motivation") and a.relock:
        invalidate_downstream(root, s, "motivation relocked")
    s["locked_motivation"] = a.motivation
    append_ledger(root, "DECISION_LEDGER.md", f"- {now()} — LOCK motivation: {a.motivation}")
    (root / "PROJECT_ANCHOR.md").write_text(
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
    if a.secondary and a.secondary == a.primary:
        sys.exit("secondary must differ from primary")
    changed = form_of(s) not in (None, UNDECIDED) and form_of(s) != a.primary
    s["contribution"].update({"primary_form": a.primary, "secondary_form": a.secondary,
                              "research_area": a.area or s["contribution"].get("research_area", ""),
                              "tradition": a.tradition or s["contribution"].get("tradition", "")})
    append_ledger(root, "DECISION_LEDGER.md", f"- {now()} — SET-TYPE primary={a.primary} secondary={a.secondary}")
    if changed:
        invalidate_downstream(root, s, f"primary_form changed to {a.primary}")
    save(root, s)
    print(f"form set: primary={a.primary} secondary={a.secondary}; active: {' → '.join(active_phases(s))}")
    return 0


def cmd_deprecate(root: Path, a) -> int:
    s = load(root)
    s["deprecated_options"].append({"option": a.option, "reason": a.reason, "at": now()})
    append_ledger(root, "DECISION_LEDGER.md", f"- {now()} — DEPRECATE: {a.option} — {a.reason}")
    save(root, s); print(f"deprecated: {a.option}"); return 0


def cmd_attest(root: Path, a) -> int:
    s = load(root)
    rec = {"by": a.by, "note": a.note or "", "at": now()}
    if a.key in EVIDENCE_REQUIRED_ATTEST:
        if not a.evidence:
            sys.exit(f"attest {a.key} requires --evidence <path> (evidence-backed gate)")
        ep = root / a.evidence
        if not ep.exists():
            sys.exit(f"evidence path does not exist: {a.evidence}")
        rec["evidence"] = a.evidence
        rec["evidence_sha"] = sha8(ep) if ep.is_file() else "dir"
    s.setdefault("attestations", {})[a.key] = rec
    append_ledger(root, "DECISION_LEDGER.md", f"- {now()} — ATTEST {a.key} (by {a.by})")
    save(root, s); print(f"attested: {a.key}"); return 0


def cmd_blocker(root: Path, a) -> int:
    s = load(root)
    if a.action == "add":
        s["blockers"].append({"id": a.id, "desc": a.desc or "", "severity": a.severity, "since": now()})
    else:
        s["blockers"] = [b for b in s["blockers"] if b.get("id") != a.id]
    save(root, s); print(f"blocker {a.action}: {a.id}"); return 0


def cmd_record(root: Path, a) -> int:
    s = load(root)
    fp = root / a.path
    if not fp.exists():
        sys.exit(f"refuse to record: file does not exist: {a.path}")
    entry = {"path": a.path, "sha": sha8(fp), "at": now()}
    if a.kind == "input":
        s["latest_inputs"] = [e for e in s["latest_inputs"] if e["path"] != a.path] + [entry]
    else:
        entry["verified_by"] = a.verified_by or "unspecified"
        s["verified_outputs"] = [e for e in s["verified_outputs"] if e["path"] != a.path] + [entry]
    save(root, s); print(f"recorded {a.kind}: {a.path} ({entry['sha']})"); return 0


def cmd_claim(root: Path, a) -> int:
    ep = root / a.evidence
    if not ep.is_file():
        sys.exit(f"claim evidence file does not exist: {a.evidence}")
    append_ledger(root, LEDGER, f"- CLAIM: {a.text} | EVIDENCE: {a.evidence} ({sha8(ep)})")
    s = load(root); s["claim_count"] = count_claims(root); save(root, s)
    print(f"claim recorded; ledger now has {s['claim_count']} evidence-backed claim(s)."); return 0


def cmd_skip(root: Path, a) -> int:
    s = load(root)
    if a.phase not in PHASES:
        sys.exit(f"unknown phase: {a.phase}")
    if a.phase not in s.get("na_phases", []):
        s.setdefault("na_phases", []).append(a.phase)
    append_ledger(root, "DECISION_LEDGER.md", f"- {now()} — SKIP phase {a.phase}: {a.reason}")
    save(root, s); print(f"marked not-applicable: {a.phase}"); return 0


def cmd_advance(root: Path, a) -> int:
    s = load(root); cur = s["lifecycle_phase"]; target = next_active(s)
    if target is None:
        if form_of(s) == UNDECIDED:
            sys.exit("set a contribution form (`set-type`) before advancing past lock")
        sys.exit("already at the final active phase")
    if a.to and a.to != target:
        sys.exit(f"next active phase is {target} (got {a.to}); use `skip` to mark phases not-applicable")
    # clear this phase's own prior gate-blocker before re-evaluating, so a retry is not
    # poisoned by the HIGH blocker its own earlier failure recorded (self-lock bug).
    s["blockers"] = [b for b in s["blockers"] if b.get("id") != f"gate:{cur}"]
    unmet = [label for label, pred in PHASE_EXIT.get(cur, []) if not pred(s, root)]
    if unmet and not a.force:
        print(f"BLOCKED: cannot leave {cur} (→ {target}). Unmet:")
        for u in unmet:
            print(f"  ✗ {u}")
        s["blockers"].append({"id": f"gate:{cur}", "desc": "; ".join(unmet), "severity": "HIGH", "since": now()})
        save(root, s); return 1
    if unmet and a.force:
        append_ledger(root, "DECISION_LEDGER.md", f"- {now()} — FORCE leave {cur}→{target} despite: {'; '.join(unmet)}")
    s["lifecycle_phase"] = target
    s["gates_passed"] = sorted(set(s.get("gates_passed", []) + [target]))
    s["blockers"] = [b for b in s["blockers"] if b.get("id") != f"gate:{cur}"]
    set_next(s); save(root, s)
    print(f"advanced {cur} → {target}" + (" (forced)" if unmet else "")); return 0


def cmd_manifest(root: Path, a) -> int:
    s = load(root)
    ignore = {".git", "__pycache__", ".aris", "node_modules"}
    files = [(f.relative_to(root).as_posix(), sha8(f), f.stat().st_size)
             for f in sorted(root.rglob("*"))
             if f.is_file() and not any(p in ignore for p in f.parts)]
    recorded = {e["path"] for e in s.get("verified_outputs", [])}
    present = {rel for rel, _, _ in files}
    managed = {STATE_FILE, "OUTPUT_MANIFEST.md", "PROJECT_ANCHOR.md", "DECISION_LEDGER.md", LEDGER, "HANDOFF.md"}
    missing = sorted(recorded - present)
    unrecorded = sorted(present - recorded - managed)
    out = ["# Output Manifest", "", f"_Generated {now()} by hci_state.py — do not hand-edit._", "",
           f"Files: {len(files)} | verified outputs in state: {len(recorded)}", "",
           "| file | sha8 | bytes | verified |", "|---|---|---|---|"]
    out += [f"| {r} | `{h}` | {n} | {'✓' if r in recorded else ''} |" for r, h, n in files]
    if missing:
        out += ["", "## ⚠ Drift: recorded as verified but MISSING"] + [f"- {m}" for m in missing]
    if unrecorded:
        out += ["", "## Present but NOT recorded as verified output"] + [f"- {u}" for u in unrecorded]
    (root / "OUTPUT_MANIFEST.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"OUTPUT_MANIFEST.md: {len(files)} files; {len(missing)} missing, {len(unrecorded)} unrecorded")
    return 1 if missing else 0


def cmd_handoff(root: Path, a) -> int:
    s = load(root); cur = s["lifecycle_phase"]; nxt = next_active(s)
    out = ["# Handoff", "", f"_Generated {now()} from HCI_STATE.json._", "",
           f"- **Project:** {s['project']}", f"- **Phase:** {cur}",
           f"- **Active lifecycle:** {' → '.join(active_phases(s))}",
           f"- **Venue:** {s['venue'].get('name') or '—'} (deadline {s['venue'].get('deadline') or '—'})",
           f"- **Motivation:** {'LOCKED — ' + s['locked_motivation'] if s.get('locked_motivation') else '(unlocked)'}",
           f"- **Form:** primary={form_of(s)} secondary={s['contribution'].get('secondary_form')}",
           f"- **Evidence-backed claims:** {count_claims(root)}",
           f"- **Next step:** {s.get('next_step','')}", "", "## Open blockers"]
    out += [f"- [{b.get('severity')}] {b.get('id')}: {b.get('desc')}" for b in s.get("blockers", [])] or ["- none"]
    out += ["", f"## To leave {cur}"]
    out += [f"- [{'x' if pred(s, root) else ' '}] {label}" for label, pred in PHASE_EXIT.get(cur, [])] or ["- (final)"]
    out += ["", "## Deprecated (do not revisit)"]
    out += [f"- {d['option']} — {d['reason']}" for d in s.get("deprecated_options", [])] or ["- none"]
    (root / "HANDOFF.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("HANDOFF.md regenerated."); return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="hci-spine project state machine")
    ap.add_argument("--root", default="."); sub = ap.add_subparsers(dest="cmd", required=True)
    pi = sub.add_parser("init"); pi.add_argument("--project", required=True)
    pi.add_argument("--venue"); pi.add_argument("--deadline"); pi.add_argument("--word-min", type=int)
    pi.add_argument("--word-max", type=int); pi.add_argument("--area"); pi.add_argument("--tradition")
    pi.add_argument("--force", action="store_true")
    sub.add_parser("status")
    pl = sub.add_parser("lock"); pl.add_argument("--motivation", required=True); pl.add_argument("--relock", action="store_true")
    pt = sub.add_parser("set-type"); pt.add_argument("--primary", required=True)
    pt.add_argument("--secondary"); pt.add_argument("--area"); pt.add_argument("--tradition")
    pd = sub.add_parser("deprecate"); pd.add_argument("--option", required=True); pd.add_argument("--reason", required=True)
    pa = sub.add_parser("attest"); pa.add_argument("key"); pa.add_argument("--by", default="user")
    pa.add_argument("--note"); pa.add_argument("--evidence")
    pb = sub.add_parser("blocker"); pb.add_argument("action", choices=["add", "clear"]); pb.add_argument("--id", required=True)
    pb.add_argument("--desc"); pb.add_argument("--severity", default="MED", choices=["LOW", "MED", "HIGH"])
    pr = sub.add_parser("record"); pr.add_argument("kind", choices=["input", "output"])
    pr.add_argument("--path", required=True); pr.add_argument("--verified-by")
    pc = sub.add_parser("claim"); pc.add_argument("action", choices=["add"])
    pc.add_argument("--text", required=True); pc.add_argument("--evidence", required=True)
    psk = sub.add_parser("skip"); psk.add_argument("phase"); psk.add_argument("--reason", required=True)
    pv = sub.add_parser("advance"); pv.add_argument("--to"); pv.add_argument("--force", action="store_true")
    sub.add_parser("manifest"); sub.add_parser("handoff")
    a = ap.parse_args(); root = Path(a.root).resolve()
    d = {"init": cmd_init, "status": cmd_status, "lock": cmd_lock, "set-type": cmd_set_type,
         "deprecate": cmd_deprecate, "attest": cmd_attest, "blocker": cmd_blocker, "record": cmd_record,
         "claim": cmd_claim, "skip": cmd_skip, "advance": cmd_advance, "manifest": cmd_manifest, "handoff": cmd_handoff}
    return d[a.cmd](root, a)


if __name__ == "__main__":
    raise SystemExit(main())
