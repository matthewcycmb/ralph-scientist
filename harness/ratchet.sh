#!/usr/bin/env bash
# Ratchet: tag paper-vN iff all gates green AND latest reviewer rubric >= last tagged score.
# The tag is always the submittable state; the loop can never regress below it.
set -uo pipefail
cd "$(dirname "$0")/.."
ITER="${1:-0}"

# All gates green? Parse the final complete gate block rather than assuming a fixed
# number of gates or lines. checkpoint.sh has already committed this exact state.
LAST_GATE_BLOCK=$(awk '
  /^--- gates @ iteration / { block = "" }
  { block = block $0 ORS }
  END { printf "%s", block }
' VERIFY.log 2>/dev/null)
grep -q '^gates failed: 0$' <<< "$LAST_GATE_BLOCK" || exit 0

# Shadow tag: EVERY all-gates-green checkpoint is verified and submittable, regardless
# of review score. A post-review promotion sets RATCHET_PAPER_ONLY=1 so it does not mint
# a duplicate green tag for the same checkpoint.
if [[ -z "${RATCHET_PAPER_ONLY:-}" ]]; then
  # Numbering is GLOBAL (no --merged): tag names are repo-wide, so a sim branch sharing
  # .git with practice tags must continue the sequence or creation collides and fails.
  LAST_GREEN=$(git tag -l 'green-v*' --sort=-v:refname | head -1)
  if [[ -z "$LAST_GREEN" ]]; then GN=1; else GN=$(( ${LAST_GREEN#green-v} + 1 )); fi
  git tag -a "green-v$GN" -m "gates=green iter=$ITER" \
    && echo "SHADOW: tagged green-v$GN (iter=$ITER)" | tee -a VERIFY.log \
    || echo "SHADOW FAILED: could not tag green-v$GN (iter=$ITER)" | tee -a VERIFY.log
fi

# Latest reviewer score (JSON line at end of newest review). No review yet -> require one.
# Rubric score (fixed bar vs SPEC) preferred; holistic 'overall' as fallback for old files.
get_score() {
  local s
  s=$(grep -o '"rubric": *[0-9]*' "$1" 2>/dev/null | tail -1 | grep -o '[0-9]*$')
  [[ -z "$s" ]] && s=$(grep -o '"overall": *[0-9]*' "$1" 2>/dev/null | tail -1 | grep -o '[0-9]*$')
  echo "${s:-}"
}
LATEST_REVIEW=$(ls -t reviews/iter-*.md 2>/dev/null | head -1)
[[ -n "${LATEST_REVIEW:-}" ]] || exit 0
SCORE=$(get_score "$LATEST_REVIEW")
[[ -n "$SCORE" ]] || exit 0
# Two-read decisions: if a confirmation review exists for this iter, use the MINIMUM.
REVIEW_N=$(basename "$LATEST_REVIEW" | grep -o '[0-9]*')
CONFIRM="reviews/confirm-$REVIEW_N.md"
if [[ -s "$CONFIRM" ]]; then
  CSCORE=$(get_score "$CONFIRM")
  [[ -n "$CSCORE" && "$CSCORE" -lt "$SCORE" ]] && SCORE=$CSCORE
fi
[[ "${SCORE:-0}" -ge 6 ]] || exit 0   # SPEC threshold for first tag (rubric-based)

# ONE TAG PER REVIEW (shakedown bug #2): the newest paper tag records the content
# hash of the review it cashed — the same review can never mint a second tag.
REVIEW_ID=$(shasum -a 256 "$LATEST_REVIEW" | cut -c1-12)
NEWEST_PAPER=$(git tag -l 'paper-v*' --sort=-v:refname --merged HEAD | head -1)
if [[ -n "$NEWEST_PAPER" ]] && git tag -l --format='%(contents)' "$NEWEST_PAPER" | grep -q "review=$REVIEW_ID"; then
  exit 0  # this review already produced a tag
fi

# Previous tagged score (stored in the tag message). Lineage = current branch only,
# but the NUMBER continues the repo-global sequence (tag names are repo-wide).
LAST_TAG=$(git tag -l 'paper-v*' --sort=-v:refname --merged HEAD | head -1)
if [[ -n "$LAST_TAG" ]]; then
  LAST_SCORE=$(git tag -l --format='%(contents)' "$LAST_TAG" | grep -o 'score=[0-9]*' | grep -o '[0-9]*') || LAST_SCORE=0
  [[ "$SCORE" -ge "${LAST_SCORE:-0}" ]] || exit 0
fi
GLOBAL_PAPER=$(git tag -l 'paper-v*' --sort=-v:refname | head -1)
if [[ -z "$GLOBAL_PAPER" ]]; then N=1; else N=$(( ${GLOBAL_PAPER#paper-v} + 1 )); fi

git tag -a "paper-v$N" -m "score=$SCORE iter=$ITER gates=green review=$REVIEW_ID" \
  && echo "RATCHET: tagged paper-v$N (score=$SCORE, iter=$ITER)" | tee -a VERIFY.log \
  || echo "RATCHET FAILED: could not tag paper-v$N (score=$SCORE, iter=$ITER)" | tee -a VERIFY.log
