# Full Pipeline — HCI idea → submission (master map)

The complete flow built across this work. Two halves:
**Produce & review** (Claude side, `hci-spine` orchestrator) → **Polish & humanize**
(Codex side, two-stage polish). Every gate is named; every step points at the exact
skill/script that runs it. Skills not authored here are existing dependencies.

```
STAGE 0  Idea            STAGE 1  hci-spine (produce + review)        STAGE 2  Polish (Codex)      STAGE 3
idea-discovery   ─►   Phase0 router → research → gates → review   ─►   formal → human+signature  ─►  submit
research-refine                                                        paper-polish-workflow         final
                                                                       paper-polish-human            checks
```

---

## STAGE 0 — Idea (optional, when the idea is vague)
- `idea-discovery` / `research-refine` — turn a fuzzy direction into a problem-anchored idea.
- Exit when you have a candidate contribution and a rough motivation.

## STAGE 1 — hci-spine orchestrator (produce + review)
Entry: say "做 HCI 论文 / hci-spine", or run the intake wizard.

1. **Phase 0 — contribution-FORM router (FIRST).** Resolve the four axes — `primary_form`
   (+ optional `secondary_form`) / `research_area` / `tradition` / `venue` — keeping
   form separate from area (`aihci` is an area) and tradition. Forms: `empirical`,
   `artifact`, `method`, `conceptual_theoretical`, `dataset_corpus`,
   `critical_artistic`, `replication`. Load the form playbook
   (`references/contribution-form-playbooks.md`). Writes `contribution_form.md`.
   Project state is tracked by `scripts/hci_state.py` (lifecycle forge→…→paper).
2. **Config — intake wizard.**
   `bash scripts/launch_hci_spine_ui.sh <out>` (TUI) or
   `python3 scripts/intake_wizard.py --in-place --output-dir <out>`. Writes `hci_spine_config.json`.
3. **Research.** `deep-research` (local-first) → `research_dossier.md`,
   `sota_gap_map.md`, `motivation_options_after_research.md`.
4. **Citation coverage (NOT a quota).** `deep-research` / `citation-audit` →
   `citation_support_bank.md` keyed by CLAIM — every claim needing support has the
   citation(s) that support it, layered canonical / recent / opposing; each verified
   for existence AND support. Completeness = claim coverage, never a candidate count
   or an N-year freshness quota.

Integrity is FOUR ordered checkpoints (the lint needs a manuscript, so it runs AFTER
the draft). Authoritative list is SKILL.md "Non-Negotiable Route"; summary:

5. **GATE A — pre-study + motivation (HARD; no manuscript).** `confirmed_motivation.md`
   + contribution statement in the FORM's vocabulary; scope + ethics resolved.
   **Red-team #1 (idea kill)** via `kill-argument`. (state: `lock`.)
6. **GATE B — pre-draft evidence readiness (HARD; before Findings).** Data frozen;
   every claim has traceable evidence; form data audit (`experiment-audit` / Codex
   `data_audit`). **Red-team #2 (media/AI necessity)**, **#3 (study-design attack)**.
7. **Plan.** `section_blueprints.md` + **HCI Rationale Matrix** (`hci_rationale_matrix.md`).
8. **Draft.** Use the form skeleton `templates/<form>.tex` (one per form:
   artifact/empirical/method/conceptual_theoretical/dataset_corpus/critical_artistic/replication).
   Optional `dual_write` via `codex_role.sh --role dual_write`.
9. **GATE C — pre-review completeness (HARD; manuscript exists).** `check_universal.py
   PAPER --min-words … --max-words … [--tex-root DIR] [--anonymous] [--log build.log]`
   + `citation-audit` / `paper-claim-audit` + Codex `cite_verify`.
10. **GATE D — peer review.** `academic-paper-reviewer` (5 personas, form-configured) +
    `kill-argument` + Codex `review` (`codex_role.sh --role review`, or free-form
    `codex_review.sh --prompt`; MCP-independent; anti-anchoring; merge-don't-average).
    **Red-team #4 (final paper review)** lives here. → `review_synthesis.md` + `rebuttal_kit.md`.
11. **Revise → build.** `paper-spine-latex` / `paper-compile` → PDF.
12. **GATE E — pre-submission audit (HARD).** re-run `check_universal.py` (no HARD-FAIL)
    + `paper-spine-audit`; all [FLAG]s resolved; venue format.

**Hand-off to Stage 2:** the compiled draft prose (LaTeX or Word).

## STAGE 2 — Polish (Codex): diagnostic → formal → human/signature → FLAG loop → audit
The [FLAG]s must be produced BEFORE the formal pass that acts on them (the old
"2a handles flags, 2b generates them" order was a loop error). Corrected order:

1. **Diagnostic.** Run the `anti-defensive-and-ai-tells.md` checklist read-only over
   the draft to emit the `[EDIT]`/`[FLAG]` findings block up front (no edits yet).
2. **Formal academic polish.** `paper-polish-workflow` (or `paper-refine-special-en`/`-zh`).
   Structure, sentence logic, expression — AND act on the diagnostic `[FLAG]`s that
   need added content (missing background citations, genuine critical-thinking, swap a
   citation that no longer supports its claim).
3. **Human + signature pass.** `paper-polish-human` (formal:natural ≈ 7:3) applies the
   author layers — `author-signature-style.md` (prose DNA: long/short mixing; restrained
   em-dash, negation-first, parallelism, simile, adjective stacking; no colon-definition)
   and the `[EDIT]` removals from `anti-defensive-and-ai-tells.md`. Grammar-error mode
   is removed from this flow.
4. **FLAG-resolution loop.** Re-run the diagnostic; any remaining `[FLAG]` is resolved
   or consciously accepted by the author. Repeat until clear.
5. **Final audit.** `check_universal.py` + the diagnostic both clean.

Principle across both author layers: **傾向,不絕對** — every rule is "盡量避免",
kept when genuinely needed; dialogue negation exempt; keep necessary ethics/scope
boundaries (delete only the scattered defensive disclaimers).

## STAGE 3 — Final checks before submit
- Re-run `check_universal.py` (expect no HARD-FAIL: word-count in range, zero
  placeholders, zero `⏳`).
- Confirm all [FLAG] items resolved or consciously accepted.
- `paper-compile` final PDF; venue formatting (e.g. ACM TAPS for TEI).

---

## Where everything lives
| Piece | Path |
|---|---|
| hci-spine orchestrator | installed `hci-spine/` skill directory (SKILL.md, references/, scripts/, templates/) |
| Universal honesty lint | `hci-spine/scripts/check_universal.py` |
| Codex cross-model leg | `hci-spine/scripts/codex_review.sh` |
| Genre LaTeX skeletons | `hci-spine/templates/*.tex` |
| Formal polish (stage 2a) | installed `paper-polish-workflow/` skill |
| Human + signature (stage 2b) | installed `paper-polish-human/` skill (+ author-signature-style.md, anti-defensive-and-ai-tells.md) |
