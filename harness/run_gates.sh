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
    DETAIL=$(head -c 400 /tmp/gate_out | tr '\n' ' ')
    echo "DETAIL $name: $DETAIL"
    # Keep one open task per gate. Once an agent removes/completes it, a future
    # regression creates a fresh task; repeated red laps do not flood the logbook.
    if ! grep -Fq -- "- [ ] GATE FAIL ($name," TODO.md 2>/dev/null; then
      echo "- [ ] GATE FAIL ($name, iter $ITER): $DETAIL" >> TODO.md
    fi
  fi
}

# Order matters: regenerate truth (results -> values) BEFORE compiling, so the
# PDF can never be built from hand-edited macros.
run_gate "frozen-inputs"       bash harness/gates/check_frozen.sh                  # model + fallback data still match declared hashes
run_gate "citations-resolve"   .venv/bin/python harness/gates/check_citations.py  # refs.bib ↔ Crossref/S2, cached
run_gate "no-number-literals"  .venv/bin/python harness/gates/check_numbers.py    # scan paper/*.tex for raw numerics
run_gate "pipeline-fresh"      bash harness/gates/check_fresh.sh                  # regen from raw data must reproduce the lap's exact results.json + values.tex (tamper/stale/non-determinism)
run_gate "results-sane"        .venv/bin/python harness/gates/check_sanity.py     # schema + sanity bounds
run_gate "prose-style"         .venv/bin/python harness/gates/check_style.py      # no em dashes, no AI-slop vocabulary (Matthew's editorial bar)
run_gate "latex-compiles"      bash harness/gates/check_pdf.sh                   # compile + page/layout/running-title checks

echo "gates failed: $FAILS"
exit "$FAILS"
