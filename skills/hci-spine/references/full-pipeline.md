# HCI-Spine Full Pipeline

Use this map to resume a project. Read `HCI_STATE.json` and `HANDOFF.md` first;
this file defines the stable workflow, while project files hold live state.

## Lifecycle

```text
forge → lock → prototype_gate → ethics → study_design → pilot
      → instrumentation → data_freeze → analysis → claim_lock → paper
```

- Initialize or inspect state with `scripts/hci_state.py`.
- Keep `PROJECT_ANCHOR.md`, `DECISION_LEDGER.md`, and
  `CLAIM_EVIDENCE_LEDGER.md` current.
- Regenerate `OUTPUT_MANIFEST.md` and `HANDOFF.md` before handing the project to
  another agent or session.
- If a lifecycle phase does not apply, record a justified exemption instead of
  silently skipping it.

## Stage 0 — Forge and lock

1. For a vague idea, stay in `forge`; use `idea-discovery`, `research-refine`,
   or an equivalent adversarial dialogue.
2. Run an idea-kill review before lock.
3. Lock the motivation and record deprecated alternatives.
4. Resolve four separate axes before leaving `lock`:
   `primary_form`, optional `secondary_form`, `research_area`, `tradition`, and
   `venue`.
5. Load `references/contribution-form-playbooks.md`.

## Stage 1 — Build evidence and the paper

1. Create `source_map.md`; index local references before web supplementation.
2. Produce `research_dossier.md`, `exemplar_learning_dossier.md`,
   `style_profile.md`, `sota_gap_map.md`, and
   `motivation_options_after_research.md`.
3. Build `citation_support_bank.md` by claim coverage. Layer canonical, recent,
   and opposing evidence. Do not use a citation-count or recency quota.
4. Pass the project gates:
   - **Gate A:** motivation, scope, ethics plan, and idea red-team.
   - **Gate B:** prototype/media fit, study-design red-team, ethics, pilot,
     instrumentation, data freeze, analysis, and claim-to-evidence audit.
   - **Gate C:** complete manuscript lint, citation audit, claim audit, and
     independent citation triage.
   - **Gate D:** multi-perspective review, adversarial review, and independent
     cross-model review.
   - **Gate E:** final integrity and venue-format audit.
5. Create `section_blueprints.md` and `hci_rationale_matrix.md` before drafting.
6. Draft from `templates/<primary_form>.tex`; merge secondary-form checks when
   applicable.
7. Compile source and PDF with the available LaTeX workflow.

## Codex roles

Use `scripts/codex_role.sh` for the independent second-model passes:

```bash
bash scripts/codex_role.sh --role review --cd PROJECT --paper PAPER --out OUTPUT
bash scripts/codex_role.sh --role dual_write --cd PROJECT --paper SOURCE_PACK --section SECTION --out OUTPUT
bash scripts/codex_role.sh --role cite_verify --cd PROJECT --paper PAPER --bib BIB --out OUTPUT
bash scripts/codex_role.sh --role data_audit --cd PROJECT --data DATA --claims CLAIMS --out OUTPUT
```

Treat `cite_verify` as a second-eye triage. Authoritative citation verification
still requires primary-source, DOI, or trusted-index checks. Keep cross-model
reviews independent and merge unique findings; never average verdicts.

## Stage 2 — Polish loop

1. Run a read-only style and argument diagnostic.
2. Apply formal academic polishing to structure, logic, and evidence-backed
   expression.
3. Apply a restrained human-style pass without changing facts, citations,
   formulas, labels, or numbers.
4. Resolve or consciously accept every diagnostic flag.
5. Re-run completeness and integrity checks.

Personal author-style overlays are optional and are not bundled with this public
skill.

## Stage 3 — Submission checks

- Confirm venue and submission track requirements from current official sources.
- Re-run `check_universal.py` with word limits, anonymity mode, TeX root, and
  compile log when applicable.
- Verify references, figures, permissions, accessibility text, supplementary
  files, anonymization, and PDF compilation.
- Regenerate `OUTPUT_MANIFEST.md` and `HANDOFF.md`.

## Bundled components

| Component | Relative path |
|---|---|
| Orchestrator | `SKILL.md` |
| Contribution playbooks | `references/contribution-form-playbooks.md` |
| State manager | `scripts/hci_state.py` |
| Universal lint | `scripts/check_universal.py` |
| Codex role dispatcher | `scripts/codex_role.sh` |
| Codex role contracts | `references/codex-roles/` |
| Form templates | `templates/` |
