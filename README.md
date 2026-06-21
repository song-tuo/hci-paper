# HCI Paper

`hci-spine` is a cross-platform skill for developing Human–Computer Interaction
projects from an early idea through evidence, review, writing, and submission.
It separates contribution form, research area, research tradition, and venue;
maintains resumable project state; and adds independent review, citation triage,
data auditing, and LaTeX-oriented integrity checks.

## What it includes

- A gated project lifecycle from `forge` to `paper`
- Seven contribution-form playbooks
- Primary/secondary contribution support for mixed papers
- Project anchors, decision and evidence ledgers, manifests, and handoffs
- Four optional Codex roles: review, dual-write, citation triage, and data audit
- Universal manuscript linting for word limits, placeholders, TeX assets,
  citations, anonymity, and compile-log problems
- LaTeX skeletons for every contribution form

## Install

Clone the repository, then install for Codex or Claude Code:

```bash
git clone https://github.com/song-tuo/hci-paper.git
cd hci-paper
bash install.sh codex
# or: bash install.sh claude
```

The installer refuses to overwrite an existing installation. Move or back up an
existing `hci-spine` directory before reinstalling.

## Use

Invoke the skill explicitly:

```text
Use $hci-spine to develop this HCI project from the idea stage.
Use $hci-spine to audit and rebuild this CHI paper from existing materials.
Use $hci-spine to review this artifact paper before submission.
```

For a new project, initialize state:

```bash
python3 ~/.codex/skills/hci-spine/scripts/hci_state.py \
  --root /path/to/project init --project "Project title"
```

Read `skills/hci-spine/references/full-pipeline.md` for the complete workflow.

## Requirements

- Python 3.9+
- Bash
- Codex CLI only for optional cross-model roles
- A LaTeX environment only when compiling paper templates

The orchestrator can call other research or paper skills when they are installed.
When a named dependency is unavailable, `SKILL.md` instructs the agent to follow
the equivalent workflow locally.

## Validation

```bash
bash verify.sh
```

The verification suite checks skill metadata, Python and shell syntax, state
transitions, intake validation, manuscript linting, Codex-role dispatch, and
structured-output contracts. Dry-run tests do not send content to external models.

## Privacy

The repository contains no telemetry and no embedded personal profile, project
history, credentials, email addresses, or institution data. Optional Codex roles
send only the files explicitly selected by the caller. Review `PRIVACY.md` before
using them with sensitive research data.

## Contributors and provenance

This skill was directed and curated by the repository owner, with implementation
and review support from both Claude Code and GPT/Codex-assisted workflows. The
public GitHub contributors graph reflects commit authorship only; see
`CONTRIBUTORS.md` for the intended project-level attribution.

## Current limitations

- Lifecycle phases are intentionally explicit; projects that do not use a phase
  should record a justified exemption rather than silently skipping it.
- Citation triage is not authoritative source verification. Verify important
  citations against primary sources, DOI records, or trusted scholarly indexes.
- The bundled TeX files are contribution-form skeletons, not current venue
  templates. Always obtain submission formatting from the venue's official site.
- Multi-file TeX projects should still be compiled and inspected; the lint checks
  referenced file existence but does not fully flatten every included source.

## License

MIT. See `LICENSE`.
