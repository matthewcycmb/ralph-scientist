#!/usr/bin/env bash
# Gate: pipeline-fresh — regenerating results.json and values.tex from the raw
# data must reproduce EXACTLY what the agent left in the working tree.
#
# Catches, with one check:
#   - hand-edited results.json or values.tex (tampering: regen overwrites the lie)
#   - stale values (agent changed analysis but forgot make results/values —
#     the compiled paper would show numbers that no longer match the code)
#   - non-deterministic analysis (same data, different numbers = a bug)
# Allows: legitimate analysis changes, as long as the agent regenerated both
# files itself before finishing the lap (SPEC requires it).
set -uo pipefail
SNAP=$(mktemp -d)
trap 'rm -rf "$SNAP"' EXIT

cp results.json "$SNAP/results.json" 2>/dev/null || { echo "FAIL: results.json missing (run make results)"; exit 1; }
cp paper/values.tex "$SNAP/values.tex" 2>/dev/null || { echo "FAIL: paper/values.tex missing (run make values)"; exit 1; }

make -s results values || { echo "FAIL: pipeline did not rebuild (make results values errored)"; exit 1; }

ok=0
cmp -s results.json "$SNAP/results.json" || { echo "FAIL: regenerated results.json differs from what the lap left — hand-edit, staleness, or non-determinism"; ok=1; }
cmp -s paper/values.tex "$SNAP/values.tex" || { echo "FAIL: regenerated values.tex differs from what the lap left — hand-edit or stale (run make values after changing analysis)"; ok=1; }

[[ $ok -eq 0 ]] && echo "PASS: pipeline rebuilds and reproduces the lap's exact outputs"
exit $ok
