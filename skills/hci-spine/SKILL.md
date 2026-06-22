---
name: hci-spine
description: HCI paper full-pipeline orchestrator + project state machine. Routes by contribution FORM (empirical/artifact/method/conceptual_theoretical/dataset_corpus/critical_artistic/replication) kept separate from area/tradition/venue, runs a gated lifecycle (forge→lock→prototype_gate→ethics→study_design→pilot→instrumentation→data_freeze→analysis→claim_lock→paper), then idea → research → write → review → rebuttal-ready → LaTeX/PDF. Inherits paper-spine's row-by-row rationale matrix, deep-research rigor, and multi-reviewer simulation, with Codex cross-model integration at four named gates. Triggers on "hci-spine", "write an HCI paper", "CHI/UIST/CSCW/DIS/IUI paper", "做 HCI 论文", "HCI 全流程", "我要写交互论文".
allowed-tools: Bash(*), Read, Grep, Glob, Write, Edit, Skill, mcp__codex__codex, mcp__codex__codex-reply
---

# HCI-Spine Orchestrator

The HCI-native sibling of `paper-spine`. Same DNA — research-first, motivation-
gated, row-by-row rationale matrix, integrity gates — but the spine is shaped
around **HCI contribution types** (Wobbrock & Kientz 2016), not the ML/IMRaD
default. It is the suite entrypoint and routes to branch skills; it never
fabricates study data, participant quotes, metrics, citations, or figures.
User materials are authoritative for this paper's results; external exemplars
teach structure and rhetoric only.

## Operating Principle

HCI papers are judged on **contribution clarity**, not template compliance. A
UIST systems paper and a CSCW interview study are different *genres* with
different reviewer expectations, different figure conventions, and different
failure modes. So the FIRST decision is always: *which contribution type are we
writing?* Everything downstream — the rationale matrix columns, the reviewer
persona, which Codex gate matters most — branches off that.

## Phase 0 — Contribution-Form Router (DO THIS FIRST)

Resolve **four orthogonal axes — do not conflate them** (the old single-"type"
router did, mixing form/area/tradition/venue). See
`references/contribution-form-playbooks.md`.

| Axis | Field | Values |
|---|---|---|
| **FORM** (what the contribution is) | `primary_form` (+ optional `secondary_form`) | `empirical`, `artifact`, `method`, `conceptual_theoretical`, `dataset_corpus`, `critical_artistic`, `replication` |
| **AREA** (domain) | `research_area` | free text, e.g. human-AI interaction, tangible/embodied, accessibility, CSCW (**`aihci` lives here, it is not a form**) |
| **TRADITION** (how knowledge is made) | `tradition` | free text, e.g. systems-building, research-through-design, controlled experiment, qualitative-field |
| **VENUE** | `venue` | CHI / UIST / CSCW / DIS / IUI / TEI … |

`from_idea` projects do NOT pick a form during the exploratory `forge` phase — the
form is set later (see the state machine below). When a form is needed, load that
form's playbook; add tradition modifiers and the media-fit lens as the playbook
specifies. Record the resolved axes in `hci_spine_output/contribution_form.md`.

**Mixed is executable**, not a label: with `primary_form` + `secondary_form`, load
the primary form's section arc + honesty checklist and **merge** the secondary
form's reviewer card + honesty checklist (strictest-wins on overlapping rows).

## Project state (the operating-system core)

Every project carries dynamic state, not just a flow. Manage it with
`scripts/hci_state.py` (HCI_STATE.json + the lifecycle below); regenerate
`OUTPUT_MANIFEST.md` (anti-drift) and `HANDOFF.md` (cold resume) from it.

```
forge → lock → prototype_gate → ethics → study_design → pilot
      → instrumentation → data_freeze → analysis → claim_lock → paper
```

Each transition has an entry gate (`hci_state.py advance` refuses + logs a blocker
when unmet; `--force` logs an override). `forge` is exploratory and forces no form.
`prototype_gate → ethics` requires the **media-fit** attestation (item: the medium
must earn itself). The Non-Negotiable Route below runs *inside* the `paper`-track
work; the lifecycle gates govern the whole project.

## Required Configuration

Prefer `hci_spine_output/hci_spine_config.json`. If missing, launch the intake
wizard (see **Command-Line UI** below) rather than hand-asking a long checklist:

| Field | Allowed Values |
|---|---|
| `primary_form` | `undecided` (forge default), or `empirical`, `artifact`, `method`, `conceptual_theoretical`, `dataset_corpus`, `critical_artistic`, `replication` |
| `secondary_form` | one of the above or empty (enables executable mixed) |
| `research_area` | free text (e.g. human-AI interaction, tangible) |
| `tradition` | free text (e.g. systems-building, research-through-design) |
| `workflow` | `rewrite_existing`, `build_from_materials`, `from_idea` |
| `venue` | free text (e.g. `CHI 2027`, `UIST 2027`) |
| `tier` | `flash`, `pro` |
| `output_language` | `en`, `zh` |
| `materials_dir` | path or empty (study data, logs, figures, notes) |
| `draft_path` | path or empty |
| `user_motivation` | free text or empty |
| `codex_roles` | subset of `review`, `dual_write`, `cite_verify`, `data_audit` |
| `reference_mode` | `local_first`, `specified_paths`, `web` |
| `reference_paths` | list; default `["."]` |
| `citation_target_count` | integer; default `25` |

If `workflow` is `from_idea` and the idea is vague, route to `idea-discovery`
(or `research-refine`) BEFORE Phase 1.

## Non-Negotiable Route

1. **Phase 0 axes recorded** in `contribution_form.md`. `primary_form` MAY be
   `undecided` during `forge`/`from_idea`; it MUST be committed (a real form) before
   leaving `lock` — the state machine enforces this. Area/tradition/venue recorded when known.
2. Create or verify `source_map.md`.
3. **Research** via `deep-research` (or `comm-lit-review`-style local-first flow):
   index local/default references per `reference_mode`, then supplement with web.
   Produce `research_dossier.md`, `exemplar_learning_dossier.md`,
   `style_profile.md`, and a genre-specific `sota_gap_map.md` that frames the gap
   in HCI terms (not just "no one did X" but "the interaction/experience problem
   is unaddressed"). Also produce `motivation_options_after_research.md`.
4. **Citation coverage (NOT a quota):** build `citation_support_bank.md` keyed by
   CLAIM — every claim needing support has the citation(s) that actually support it,
   layered as canonical / recent / opposing evidence. Verify each citation for BOTH
   existence AND that it supports the specific claim (`citation-audit` + Codex
   `cite_verify`). Completeness = claim coverage. Never substitute a candidate count
   or an N-year freshness quota for completeness (a quota forces in duplicate and
   marginal work and drops the canonical theory HCI needs).

The integrity work is split into FOUR ordered checkpoints (a single pre-draft gate
was wrong: the universal lint needs a manuscript). The lifecycle in `hci_state.py`
governs the project; these run inside the paper track.

5. **GATE A — pre-study integrity + motivation (HARD; no manuscript yet).** Confirm
   `confirmed_motivation.md` + explicit contribution statement in the FORM's
   vocabulary; scope + ethics resolved. **Red-team #1 (idea kill):** run
   `kill-argument` on the idea before locking — survive or revise. (state: `lock`.)
6. **GATE B — pre-draft evidence readiness (HARD; before writing Findings).** Data
   frozen; every planned claim has traceable evidence; run the form's data audit
   (`empirical`/`dataset_corpus`/`replication` → `experiment-audit` or Codex
   `data_audit`; `artifact` → eval numbers trace to logs/benchmarks, usability to the
   actual study, no phantom baselines). No finding may be written the evidence does
   not support. **Red-team #2 (media/AI necessity)** for `artifact`/`critical_artistic`
   (media-fit lens). **Red-team #3 (study-design attack)** for empirical work, before
   data collection. (state: `prototype_gate` / `study_design`.)
7. Create `section_blueprints.md` + the **HCI Rationale Matrix** (below) BEFORE drafting.
8. **Draft** via the form template (`templates/<form>.tex`) + playbook. If
   `codex_roles` includes `dual_write`, run `codex_role.sh --role dual_write` on
   load-bearing sections; reconcile against Claude's draft — never silently average.
9. **GATE C — pre-review completeness (HARD; manuscript now exists).** Run the
   universal lint `python3 scripts/check_universal.py PAPER --min-words … --max-words …
   [--tex-root DIR] [--anonymous] [--log build.log]` (word-count in range, no
   placeholders, `\input`/figure/bib/`\cite` resolve). Then verify citations in TWO
   halves: **existence** deterministically via `python3 scripts/verify_citations.py
   refs.bib --out verify_citations.json` (Crossref by DOI/title; a `no` is a likely
   fabrication) + **support** via Codex `cite_verify` (`codex_role.sh --role cite_verify`,
   which reads `verify_citations.json`) + `paper-claim-audit`. An all-`unsure`
   cite_verify is rejected by the validator (no real verification). Also run
   `artifact_check.py --require-through C` (deliverables exist + non-stub) and
   `humanize_check.py PAPER` (signature-style / anti-AI gate).
10. **GATE D — peer review.** `academic-paper-reviewer` (5 personas, form-configured
    via the playbook reviewer card) + `kill-argument` + Codex `review`
    (`codex_role.sh --role review`; MCP-independent; anti-anchoring; merge-don't-average).
    **Red-team #4 (final paper review)** lives here. → `review_synthesis.md` +
    `rebuttal_kit.md`.
11. Revise against the synthesis, then **LaTeX/PDF** (`paper-spine-latex` / `paper-compile`).
12. **GATE E — pre-submission audit (HARD).** Run the **teaching audit**
    `python3 scripts/hci_audit.py PAPER --root <proj> --min-words … --max-words …
    --require-through E` (aggregates `check_universal` + `artifact_check` +
    `humanize_check` into a what/where/root-cause/fix/impact report). Every [FLAG]
    resolved; venue format applied. **Bilingual:** `hci_translate.py` scaffolds
    `translation_<lang>/`, then `translate_guard.py` must PASS (every deliverable
    translated, table rows 1:1). No HARD-FAIL before declaring complete.

**Deterministic gate scripts** (all stdlib, tested): `artifact_check.py`
(required-deliverable existence per GATE A–E), `check_universal.py` (manuscript
honesty + LaTeX resolution), `humanize_check.py` (signature-style / anti-AI gate),
`verify_citations.py` (Crossref existence), `validate_codex_output.py` (Codex JSON),
`hci_audit.py` (teaching aggregate), `hci_translate.py` + `translate_guard.py`
(bilingual package). Run any at its gate; `hci_audit.py` runs the lint trio at once.

If a branch skill is unavailable, follow its workflow locally and produce the
same artifacts.

## HCI Rationale Matrix

Extends paper-spine's matrix with HCI-load-bearing columns. Built before final
writing, used as the execution plan:

| Row ID | Manuscript Unit | Function | Motivation Link | **Contribution-Type Move** | **Study/Design Rationale** | Exemplar Pattern Learned | Venue Norm | User Evidence Anchor | Planned Change | Final Check |
|---|---|---|---|---|---|---|---|---|---|---|

- **Contribution-Type Move**: how this unit advances the *declared* contribution
  (e.g. "establishes the interaction technique's novelty vs prior art" for a
  system paper; "operationalizes RQ2 into a measurable construct" for empirical).
- **Study/Design Rationale**: for `empirical` (or any form with an empirical secondary), why this study choice is valid
  (design, participants, measure, analysis, reliability); for system, why this
  evaluation answers "does the technique work"; for design, the design decision
  and its reflexive justification. The first data row must justify the whole
  contribution arc (formative → artifact/system → summative, or RQ → method →
  findings → implications), not a single section.

A shallow matrix ("improve clarity") is a failure — redo research/blueprint.

## Codex Integration (the four roles)

Codex is the independent second model. **Preferred invocation is MCP-independent:**
run `scripts/codex_review.sh --cd <project> --prompt <prompt_file> --out <out>`, which
resolves a *working* Codex binary even when the codex MCP is not connected to this
session and when the PATH `codex` shim is broken (it falls back to the Codex.app
native binary at `/Applications/Codex.app/Contents/Resources/codex`). Use the
`mcp__codex__codex` tool only if that MCP is actually connected. Two standing rules,
proven out in the v1 dogfood:

- **Anti-anchoring.** The Codex prompt contains ONLY the paper + the questions —
  NEVER the Claude panel's verdict. The leg's value is an *independent* judgment.
- **Merge, don't average.** The synthesizer pulls **Codex-only findings** into
  `review_synthesis.md` and flags verdict divergence explicitly; it never silently
  averages the two models' scores.

All four roles run via one MCP-independent dispatcher,
`scripts/codex_role.sh --role R --cd DIR --out OUT [...]` (shared resolution in
`scripts/codex_lib.sh`). The two structured roles emit JSON against a schema and are
checked by `scripts/validate_codex_output.py --role R FILE`. Roles are opt-in via
`codex_roles`:

| Role | Hook | Dispatcher call | Output / validator |
|---|---|---|---|
| `review` | Gate 10 | `codex_role.sh --role review --paper P` (or free-form `codex_review.sh --prompt`) | prose review |
| `dual_write` | Step 8 | `codex_role.sh --role dual_write --section S --paper P` | prose draft of ONE section; Claude reconciles |
| `cite_verify` | Gate 9 | `codex_role.sh --role cite_verify --paper P --bib B` | JSON (`cite_verify.schema.json`) → `validate_codex_output.py` |
| `data_audit` | Gate 6 | `codex_role.sh --role data_audit --data D --claims C` | JSON (`data_audit.schema.json`) → `validate_codex_output.py` |

Prompt templates + schemas live in `references/codex-roles/`. `--dry-run` resolves
the binary and prints the command without calling Codex (used by `test_codex_role.sh`).

Default `codex_roles` by `primary_form`: `data_audit` + `cite_verify` for
`empirical` / `dataset_corpus` / `replication`; `review` for `artifact` /
`conceptual_theoretical` / `critical_artistic`; `review` + `cite_verify` for
`method`. Always allow the user to add `dual_write`.

## Standard Artifacts (under `hci_spine_output/`)

`hci_spine_config.json`, `contribution_form.md`, `source_map.md`,
`research_dossier.md`, `exemplar_learning_dossier.md`, `style_profile.md`,
`sota_gap_map.md`, `motivation_options_after_research.md`,
`citation_support_bank.md`, `confirmed_motivation.md`, `section_blueprints.md`,
`hci_rationale_matrix.md`, genre-specific audit (`data_audit.md` /
`technical_eval_trace.md` / `portfolio_annotation_trace.md`),
`review_synthesis.md`, `rebuttal_kit.md`, `final_paper/main.tex`,
`final_paper/paper.pdf`.

## Branch Map

For the complete end-to-end map (Stage 0 idea → Stage 1 hci-spine → Stage 2
two-stage Codex polish → Stage 3 submit), read `references/full-pipeline.md`.

When a branch output fails audit, route back to the branch that owns the weak
artifact instead of patching the final paper. Idea: `idea-discovery` /
`research-refine`. Research: `deep-research`. Citation: `citation-audit` /
`paper-claim-audit`. Review: `academic-paper-reviewer` / `kill-argument` /
`auto-review-loop`. Data: `experiment-audit`. LaTeX: `paper-spine-latex` /
`paper-compile`.

## Command-Line UI

When `hci_spine_config.json` is missing or incomplete, configure via the bundled
intake wizard instead of hand-asking a long checklist. Resolve the launcher's
absolute path (it lives beside this skill):

```bash
bash ~/.claude/skills/hci-spine/scripts/launch_hci_spine_ui.sh <output_dir>      # macOS/Linux
powershell -ExecutionPolicy Bypass -File ~/.claude/skills/hci-spine/scripts/launch_hci_spine_ui.ps1 <output_dir>  # Windows
```

This opens an external Terminal window with an arrow-key TUI (↑/↓ field, ←/→
choice, Enter to edit text, `S` save, `Q` quit) and writes
`<output_dir>/hci_spine_config.json` + `.md`. `primary_form` is the first
field by design. If no window can open (headless/sandboxed) or stdin is not a
tty, run the in-place numbered fallback in the current terminal:

```bash
python3 ~/.claude/skills/hci-spine/scripts/intake_wizard.py --in-place --output-dir <output_dir>
```

Only fall back to chat-based structured questions if both paths are impossible.
Never silently skip configuration. The wizard pre-selects sensible
`codex_roles` defaults from the chosen `primary_form`.

## Distribution (canonical + adapters)

This skill is authored ONCE here (canonical: `~/.claude/skills/hci-spine`). Codex's
validator rejects the `argument-hint` / `allowed-tools` frontmatter and wants an
`agents/openai.yaml`, so regenerate the Codex copy with
`python3 scripts/build_adapters.py` (real-file copy — not a symlink, which breaks
Windows/zip; strips the incompatible keys; idempotent). Never hand-edit the generated
`~/.codex/skills/hci-spine` (it carries `ADAPTER_GENERATED.md`); edit canonical and re-run.

## Optional Vision Lens

If the user asks to frame the contribution at a longer horizon, invoke
`hiroshi-ishii-perspective` on `confirmed_motivation.md` — pull the
vision-driven framing into the Intro's opening move only. Off by default.
