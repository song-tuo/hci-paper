# Privacy

HCI Paper runs locally and contains no telemetry.

## Local processing

State files, project ledgers, manifests, manuscript checks, and intake data are
written to the project directory selected by the user.

## Optional model calls

The Codex-role scripts are optional. When invoked, they send the prompt and the
explicitly referenced project files to the configured Codex service. Review
manuscripts, participant data, interview transcripts, images, and logs before
using an external model. Remove direct identifiers and follow the applicable
ethics approval, consent language, data-management plan, and institutional rules.

## Credentials

This repository does not contain or request API keys. Authentication is handled
by the separately installed Codex CLI. Never commit authentication files, raw
participant identifiers, or private project state to a public repository.
