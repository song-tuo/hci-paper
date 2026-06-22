#!/usr/bin/env bash
# Shared Codex invocation library for hci-spine. Source it; do not execute.
# Single source of truth for binary resolution + read-only exec, so codex_review.sh
# and codex_role.sh never drift apart.

# Resolve a WORKING codex binary even when the PATH shim is broken (the
# ~/.local/bin/codex shim points at a node runtime inside Codex.app that may be
# missing). Prints the path; returns 1 if none works.
hci_resolve_codex() {
  if command -v codex >/dev/null 2>&1 && codex --version >/dev/null 2>&1; then
    command -v codex; return 0
  fi
  local c
  for c in \
    "/Applications/Codex.app/Contents/Resources/codex" \
    "$HOME/Applications/Codex.app/Contents/Resources/codex"; do
    if [ -x "$c" ] && "$c" --version >/dev/null 2>&1; then echo "$c"; return 0; fi
  done
  return 1
}

# hci_run_codex <prompt_file> <cd_dir> <out_file> <model> <reasoning> <schema_or_-> <dry_run 0|1>
# Read-only, stdin-piped (no hang). With a schema file (not "-"), adds --output-schema.
hci_run_codex() {
  local prompt="$1" cd_dir="$2" out="$3" model="$4" reasoning="$5" schema="$6" dry="$7"
  [ -f "$prompt" ] || { echo "ERROR: prompt file missing: $prompt" >&2; return 2; }

  local codex; codex="$(hci_resolve_codex)" || {
    echo "ERROR: no working Codex binary (PATH shim broken AND Codex.app binary absent)." >&2
    echo "Install/repair Codex, or run via the codex MCP if connected." >&2
    return 1
  }
  [ -f "$HOME/.codex/auth.json" ] || echo "WARN: ~/.codex/auth.json not found — Codex may be unauthenticated." >&2

  local schema_args=()
  [ "$schema" != "-" ] && [ -n "$schema" ] && schema_args=(--output-schema "$schema")

  echo "Using Codex: $codex ($("$codex" --version 2>/dev/null))" >&2
  if [ "$dry" = "1" ]; then
    echo "DRY-RUN — would execute:" >&2
    echo "  cat '$prompt' | '$codex' exec --sandbox read-only --skip-git-repo-check -m '$model' -c model_reasoning_effort='$reasoning' ${schema_args[*]:-} -C '$cd_dir'  → $out" >&2
    return 0
  fi

  mkdir -p "$(dirname "$out")"
  {
    echo "# Codex output ($model, read-only)"
    echo "Binary: $codex | schema: $schema | started: $(date)"
    echo '```'
    cat "$prompt" | "$codex" exec --sandbox read-only --skip-git-repo-check \
        -m "$model" -c model_reasoning_effort="$reasoning" ${schema_args[@]+"${schema_args[@]}"} -C "$cd_dir" 2>&1
    echo '```'
    echo "Finished: $(date)"
  } > "$out"
  echo "Codex output written to: $out" >&2
}
