#!/usr/bin/env bash
# Exit 0 only when a complete green paper is due for review.
set -uo pipefail
ITER="${1:-0}"

[[ -f paper/main.pdf && -f results.json ]] || exit 1
LAST_GATE_BLOCK=$(awk '
  /^--- gates @ iteration / { block = "" }
  { block = block $0 ORS }
  END { printf "%s", block }
' VERIFY.log 2>/dev/null)
grep -q '^gates failed: 0$' <<< "$LAST_GATE_BLOCK" || exit 1

LATEST=$(ls reviews/iter-*.md 2>/dev/null | sed -E 's/.*iter-([0-9]+)\.md/\1/' | sort -n | tail -1)
[[ -z "$LATEST" ]] && exit 0
(( ITER >= LATEST + 3 ))
