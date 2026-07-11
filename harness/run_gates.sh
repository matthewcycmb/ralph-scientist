#!/usr/bin/env bash
# Deterministic verification gates. Output -> VERIFY.log; failures appended to TODO.md.
# NOTE: uses `exec > >(tee ...)` (not a pipe) so FAILS survives to the exit code —
# a pipe puts the counter in a subshell and the script would always exit 0.
set -uo pipefail
cd "$(dirname "$0")/.."
ITER="${1:-0}"
FAILS=0
exec > >(tee -a VERIFY.log) 2>&1

echo "--- gates @ iteration $ITER $(date +%H:%M:%S) ---"

run_gate() {  # run_gate <name> <cmd...>
  local name="$1"; shift
  if "$@" > /tmp/gate_out 2>&1; then
    echo "PASS  $name"
  else
    echo "FAIL  $name"
    FAILS=$((FAILS + 1))
    # TODO(practice week): de-dup repeated failures of the same gate and add an attempt
    # counter — after ~3 consecutive fails, escalate the TODO message to "N failed
    # attempts: stop retrying the same fix, try a fundamentally different approach".
    {
      echo "- [ ] GATE FAIL ($name, iter $ITER): $(head -c 400 /tmp/gate_out | tr '\n' ' ')"
    } >> TODO.md
  fi
}

# Order matters: regenerate truth (results -> values) BEFORE compiling, so the
# PDF can never be built from hand-edited macros.
run_gate "citations-resolve"   .venv/bin/python harness/gates/check_citations.py  # refs.bib ↔ Crossref/S2, cached
run_gate "no-number-literals"  .venv/bin/python harness/gates/check_numbers.py    # scan paper/*.tex for raw numerics
run_gate "pipeline-fresh"      bash harness/gates/check_fresh.sh                  # regen from raw data must reproduce the lap's exact results.json + values.tex (tamper/stale/non-determinism)
run_gate "results-sane"        .venv/bin/python harness/gates/check_sanity.py     # schema + sanity bounds
run_gate "prose-style"         .venv/bin/python harness/gates/check_style.py      # no em dashes, no AI-slop vocabulary (Matthew's editorial bar)
run_gate "latex-compiles"      tectonic paper/main.tex                            # ICML 2026 template, compiled from regenerated truth

echo "gates failed: $FAILS"
exit "$FAILS"
