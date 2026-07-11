#!/usr/bin/env bash
# Commit the exact state inspected by the gates/reviewer, then tag that commit.
# Any editor/humanizer follow-up happens after this checkpoint and is gated next lap.
set -euo pipefail
cd "$(dirname "$0")/.."
ITER="${1:-0}"

git add -A
git commit -m "loop: iteration $ITER" --allow-empty -q
harness/ratchet.sh "$ITER" || true
