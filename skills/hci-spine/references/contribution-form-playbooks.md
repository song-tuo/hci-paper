# HCI Contribution-Form Playbooks

Loaded after Phase 0. **Four orthogonal axes — never conflate them** (this fixes the
old router, which mixed form, area, tradition, and venue into one "type"):

| Axis | What it answers | Drives | Examples |
|---|---|---|---|
| **FORM** | what the contribution *is* | section arc + honesty checklist + reviewer card | the 7 forms below |
| **AREA** | what domain | related-work scope, reviewer expertise | human-AI interaction, tangible/embodied, accessibility, CSCW |
| **TRADITION** | how knowledge is made | modifiers added on top of the form | systems-building, research-through-design, controlled experiment, qualitative-field |
| **VENUE** | where it goes | length, format, reviewer norms | CHI, UIST, CSCW, DIS, IUI, TEI |

`aihci` is an **AREA**, not a form. `research-through-design` (annotated portfolio,
strong concepts) is a **TRADITION**, not a form — most artifacts do not use it.
State the four separately in `HCI_STATE.json` (`contribution.primary_form`,
`secondary_form`, `research_area`, `tradition`).

Reference frame: Wobbrock & Kientz, "Research Contributions in HCI" (CHI 2016).

---

## Universal honesty checks (ALL forms — run before the form-specific rows)

Genre-agnostic; the integrity gate runs these first. (Cross-model Codex caught this
class in the v1 dogfood.)

- **Submission-completeness vs venue.** Word count inside the venue range (not just
  ≥70% of floor); references resolved (no `⏳` / "at LaTeX time" placeholders); no
  unrendered `[Figure: …]` / `[Table N]`; `\input`/BibTeX/figure files resolve;
  anonymity respected; compile log clean (no unresolved refs).
- **Internal numeric consistency.** A quantity repeated anywhere must agree; a
  breakdown must sum to its stated total (recompute every "X total" vs its parts).
- **Absolute quantifier vs counterexample.** Check every "never / always / all /
  none / 100%" against the paper's own reported exceptions.
- **Scope/corpus accounting.** Multiple sample sets in one place must state their
  sampling relationship.
- **Claim↔evidence locator.** Every headline number names its source file/table
  (delegate to `citation-audit` / `paper-claim-audit` / Codex `cite_verify`).

---

## The 7 FORMS

### 1. `empirical` — a claim about people/use, evidence from a study
- **Arc:** Intro + RQs → Related → Method (participants, procedure, measures, analysis plan) → Findings → Discussion + implications → Limitations.
- **Reviewer card:** design↔RQ fit; sample size/composition justified; analysis validity (stats correctness OR qualitative rigor); over-claiming/causation; ethics.
- **Honesty:** every statistic recomputable (test, df, p, effect size); each thematic claim names its evidence; N agrees text/tables/data; no HARKing; nulls reported.
- **Figures:** design diagram, participant/condition table, results with CIs, quotes.

### 2. `artifact` — a built thing is the contribution (system, tool, technique, OR design artifact)
- **Arc:** Intro + "why is this hard" → Related (technique lineage) → Design goals/rationale → The artifact → Walkthrough → Evaluation (technical and/or usability and/or demonstration) → Discussion → Limitations.
- **Reviewer card:** is the artifact/technique novel (not a new app of known methods); why is it hard; does the evaluation test the *claimed* contribution; demo credibility; generality vs cherry-picking. **+ Media-fit lens (below) for physical/tangible artifacts.**
- **Honesty:** every eval number traces to a log/study; no phantom baseline; walkthrough shows real outputs (label mockups/WoZ); simulated ≠ deployed — say which.
- **Figures:** teaser, architecture, walkthrough sequence, eval plots.
- *Note:* annotated portfolio / strong concepts are a **research-through-design tradition** modifier — not required for all artifacts.

### 3. `method` — a new way of doing research/design is the contribution
- **Arc:** Intro (the methodological gap) → Related methods → The method (steps, when to use it) → Validation/demonstration (apply it; show it works or adds value) → Guidance → Limitations.
- **Reviewer card:** is the method genuinely new and needed; is it *validated* not merely proposed; reproducibility; transfer beyond the demo case.
- **Honesty:** validation evidence real; the method's own failure modes stated; not over-generalized from a single application.
- **Figures:** method workflow, before/after, validation results.

### 4. `conceptual_theoretical` — a concept, framework, theory, or design space
- **Arc:** Intro (the conceptual gap) → Related → The construct (definitions, scope, boundaries) → Grounding (cases/data/argument) → Generativity (how others use it) → Limitations.
- **Reviewer card:** genuinely new/clarifying vs prior frameworks; grounded not merely asserted; generative; bounded/falsifiable, not circular.
- **Honesty:** novelty checked against existing frameworks; grounding examples real; scope stated; the construct is not a relabeling.
- **Figures:** framework diagram, design-space map.

### 5. `dataset_corpus` — a dataset/corpus/benchmark is the contribution
- **Arc:** Intro (the data gap) → Related data → Collection (provenance, sampling, consent/license) → Composition/stats → Validation/baselines → Use cases → Ethics + Limitations.
- **Reviewer card:** provenance + sampling rigor; ethics/consent/license; documentation completeness (datasheet); bias; reusability.
- **Honesty:** collection method disclosed; license/consent verified; biases reported; splits/stats accurate; no train/test leakage.
- **Figures:** composition stats, datasheet table.

### 6. `critical_artistic` — critical, speculative, or artistic contribution
- **Arc:** Intro (the provocation/question) → Positioning (critical/artistic lineage) → The work → Reading/interpretation → Reflection (discourse contribution) → Limitations.
- **Reviewer card:** is the provocation substantive; situated in critical/artistic discourse; reflexive; does it open new questions. **+ Media-fit lens.**
- **Honesty:** reception/effect claims not overstated without evidence; artistic choices argued, not decorative; positioned honestly.
- **Figures:** the work, documentation plates.

### 7. `replication` — replicating/reproducing prior work is the contribution
- **Arc:** Intro (what + why replicate) → Original-study summary → Replication method (faithful vs conceptual; deviations) → Results vs original → Interpretation (replicates? boundary conditions?) → Limitations.
- **Reviewer card:** fidelity to original; preregistration; honest reporting of (non)replication; power; what is learned either way.
- **Honesty:** deviations disclosed; outcome reported regardless of direction; no spin on a null; power adequate.
- **Figures:** original-vs-replication comparison.

---

## Tradition modifiers (add on top of the form)
- **research-through-design:** add annotated-portfolio plates + strong-concept articulation + reflexive process documentation.
- **systems-building:** add teaser + technical evaluation + working demo.
- **controlled experiment:** add preregistration + power analysis + statistical-reporting standards.
- **qualitative-field:** add positionality, coding/reliability or reflexive-TA stance, saturation.

## Media-fit lens (artifact / critical_artistic; mirrors PROJECT_ANCHOR, item 11)
A required reviewer lens for physical/tangible/AI artifacts — the medium must earn itself:
- Why not paper, or a plain screen?
- Is the AI removable without losing the point? (the "why AI" test)
- Does the interaction *act* participate in meaning-making, or is it decoration?
- Is the artifact more than a technical assembly — do **form, mechanism, and meaning cohere**?
A "no" to all four is a contribution-strength block, not a copy-edit.

## Mixed execution (now runnable)
Config carries `primary_form` + `secondary_form`. **Load the primary form's section
arc + honesty checklist. Merge the secondary form's reviewer card + honesty checklist;
strictest-wins on overlapping rows.** Common combos:
- `artifact` + `empirical` — a system with a summative study (merge empirical data-audit).
- `conceptual_theoretical` + `empirical` — a framework grounded in a study.
- `method` + `empirical` — a new method validated by a study.
- `artifact` + `critical_artistic` — a built work making a critical argument (both media-fit lenses).
