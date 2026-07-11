#!/usr/bin/env bash
# Ralph loop: fresh Codex iteration -> deterministic gates -> periodic adversarial review -> ratchet.
# UNTESTED SKELETON — validate codex CLI flags + sandbox/network config during practice week.
set -uo pipefail
cd "$(dirname "$0")/.."
# Never inherit a live stdin: a silent-but-open input pipe from the launcher made
# codex wait for EOF until the role timeout killed it (reviews died this way twice,
# 2026-07-07). The loop needs no stdin — sever it once, for every child.
exec < /dev/null

# Archive the previous run's working state — lap numbers and review files repeat
# across runs, and stale state must never bleed into this run's records.
if [[ -s VERIFY.log || -n "$(ls reviews 2>/dev/null)" || -n "$(ls logs 2>/dev/null)" ]]; then
  STAMP=$(date +%Y%m%d-%H%M%S)
  mkdir -p "runs/$STAMP"
  [[ -f VERIFY.log ]] && mv VERIFY.log "runs/$STAMP/"
  for d in reviews logs drafts; do
    [[ -d $d && -n "$(ls "$d" 2>/dev/null)" ]] && mv "$d" "runs/$STAMP/$d"
  done
  echo "ARCHIVED previous run state to runs/$STAMP"
fi
mkdir -p logs reviews drafts

# GNU timeout: `timeout` on Linux, `gtimeout` from coreutils on macOS.
TIMEOUT=$(command -v timeout || command -v gtimeout) || {
  echo "FATAL: need GNU timeout (brew install coreutils)"; exit 1; }

# --- Anti-reward-hacking guard (risk A) --------------------------------------
# Fingerprint the harness in memory at loop start. Agents can write anywhere in
# the workspace, but this loop process (and the baseline) live outside their
# reach: any lap that modifies harness/ or Makefile gets auto-reverted + logged.
START_SHA=$(git rev-parse HEAD)
harness_fingerprint() {
  cat harness/loop.sh harness/run_gates.sh harness/ratchet.sh harness/REVIEWER.md \
      harness/EDITOR.md harness/HUMANIZER.md harness/gates/* Makefile PROMPT.md SPEC.md 2>/dev/null | shasum -a 256 | cut -d' ' -f1
}
BASELINE_FP=$(harness_fingerprint)

ITER=0
while true; do
  ITER=$((ITER + 1))
  # Bounded runs for rehearsal: MAX_ITERS=3 harness/loop.sh
  if [[ -n "${MAX_ITERS:-}" && "$ITER" -gt "$MAX_ITERS" ]]; then
    echo "=== MAX_ITERS=$MAX_ITERS reached, loop ends ==="
    exit 0
  fi
  echo "=== iteration $ITER $(date +%H:%M:%S) ==="

  # 1. One fresh agent iteration. Flags VERIFIED 2026-07-01 on codex-cli 0.128.0 (bundled
  #    in Codex.app, symlinked to ~/.npm-global/bin/codex). Smoke test passed: auth via
  #    ~/.codex/auth.json, trivial lap ~30k tokens. Design choice: the agent runs OFFLINE
  #    (workspace-write sandbox, no network) — all network (citation APIs, data) happens
  #    in the harness gates instead.
  #
  # Timeout redesign (shakedown #1 finding, 2026-07-04): inference laps legitimately
  # run 30+ min, so a flat 15m cap guillotined `make probes` mid-run. Worker laps now
  # get a generous hard cap (AGENT_CAP_MIN, default 75m) plus a STALL watchdog:
  # activity = the lap's log growing OR files changing under data/probes/. A lap with
  # no activity for STALL_KILL_MIN minutes (default 10) is wedged — killed and logged
  # loudly to VERIFY.log (the dashboard surfaces it). Slow is allowed; stuck is not.
  AGENT_CAP_MIN="${AGENT_CAP_MIN:-75}"
  STALL_KILL_MIN="${STALL_KILL_MIN:-10}"
  # Log goes straight to the file (no tee): $! must hold the timeout/codex process
  # itself so the watchdog's kill reaches the agent, not a log pipe. Live view:
  # tail -f the iter log. GNU timeout forwards TERM to its child.
  echo "agent streaming to logs/iter-$ITER.log"
  "$TIMEOUT" "${AGENT_CAP_MIN}m" codex exec -s workspace-write --skip-git-repo-check \
    -o "logs/last-msg-$ITER.txt" "$(cat PROMPT.md)" > "logs/iter-$ITER.log" 2>&1 &
  AGENT_JOB=$!
  LAST_SIG=""
  STALL=0
  while kill -0 "$AGENT_JOB" 2>/dev/null; do
    sleep 60
    SIG=$( { wc -c < "logs/iter-$ITER.log" 2>/dev/null; \
            find data/probes -type f -exec stat -f '%z %m' {} + 2>/dev/null; } | cksum )
    if [[ "$SIG" == "$LAST_SIG" ]]; then
      STALL=$((STALL + 1))
      if (( STALL >= STALL_KILL_MIN )); then
        echo "WEDGED: iter $ITER produced no output for ${STALL_KILL_MIN}m — killing lap" | tee -a VERIFY.log
        kill "$AGENT_JOB" 2>/dev/null
        sleep 10
        kill -0 "$AGENT_JOB" 2>/dev/null && kill -9 "$AGENT_JOB" 2>/dev/null
        break
      fi
    else
      STALL=0
    fi
    LAST_SIG="$SIG"
  done
  wait "$AGENT_JOB" 2>/dev/null

  # Quota-outage backoff (found in endurance run 2026-07-02): a lap that dies on
  # usage limits must not spin no-op laps — sleep and let the quota window recover.
  if grep -q "hit your usage limit" "logs/iter-$ITER.log" 2>/dev/null; then
    echo "QUOTA: usage limit hit at iter $ITER — sleeping 10 min before retry" | tee -a VERIFY.log
    ITER=$((ITER - 1))   # quota waits don't consume the lap budget
    sleep 600
    continue
  fi

  # 2. Anti-reward-hacking: verify the harness fingerprint; on mismatch restore the
  #    originals from the loop-start commit and log it. Agents fix papers, not gates.
  if [[ "$(harness_fingerprint)" != "$BASELINE_FP" ]]; then
    echo "TAMPER: harness/SPEC/PROMPT modified at iter $ITER — restoring from $START_SHA" | tee -a VERIFY.log
    git checkout "$START_SHA" -- harness/loop.sh harness/run_gates.sh harness/ratchet.sh \
      harness/REVIEWER.md harness/EDITOR.md harness/HUMANIZER.md harness/gates Makefile PROMPT.md SPEC.md
    echo "- [ ] TAMPER DETECTED (iter $ITER): an agent modified the harness, Makefile, SPEC.md or PROMPT.md. Forbidden (SPEC hard rules) — fix the underlying problem instead." >> TODO.md
  fi

  # 3. Deterministic gates (never skipped, never agent-run). Failures land in TODO.md.
  harness/run_gates.sh "$ITER" || true

  # 4. Adversarial ICML-style review every 3rd iteration once a draft exists.
  #    read-only sandbox: the reviewer judges, it must not be able to edit anything.
  if [[ -f paper/main.tex && $((ITER % 3)) -eq 0 ]]; then
    # Draft archive: snapshot the compiled paper every review lap — the progress story.
    mkdir -p drafts
    [[ -f paper/main.pdf ]] && cp paper/main.pdf "drafts/iter-$ITER.pdf"

    # Criticism ledger anchor: the previous review, captured BEFORE this lap's review
    # file exists. The confirmation read reconciles against the same anchor.
    PREV_REVIEW=$(ls -t reviews/iter-*.md 2>/dev/null | head -1)
    REVIEWER_PROMPT="$(cat harness/REVIEWER.md)

Previous review for the ledger: ${PREV_REVIEW:-none — first review, every ledger item is new}"

    # -o captures ONLY the reviewer's final message (the review); full stream -> logs/.
    "$TIMEOUT" 25m codex exec -s read-only --skip-git-repo-check \
      -o "reviews/iter-$ITER.md" "$REVIEWER_PROMPT" > "logs/review-$ITER.log" 2>&1 || true
    # Guarantee the review reaches the logbook — agents can't miss what's in TODO.
    if [[ -s "reviews/iter-$ITER.md" ]]; then
      SCORE_LINE=$(grep -o '"rubric": *[0-9]*' "reviews/iter-$ITER.md" | tail -1)
      echo "- [ ] NEW REVIEW (iter $ITER, ${SCORE_LINE:-score unknown}/10 rubric): address weaknesses in reviews/iter-$ITER.md" >> TODO.md

      # Two-read tag decisions: a score at/above the threshold gets a second,
      # independent read (reviews/confirm-$ITER.md); the ratchet uses the MINIMUM.
      RSCORE=$(grep -o '"rubric": *[0-9]*' "reviews/iter-$ITER.md" | tail -1 | grep -o '[0-9]*$' || true)
      if [[ -n "${RSCORE:-}" && "$RSCORE" -ge 6 ]]; then
        echo "CONFIRM: rubric $RSCORE >= 6 at iter $ITER — running confirmation review" | tee -a VERIFY.log
        "$TIMEOUT" 25m codex exec -s read-only --skip-git-repo-check \
          -o "reviews/confirm-$ITER.md" "$REVIEWER_PROMPT" > "logs/confirm-$ITER.log" 2>&1 || true
      fi

      # Editor lap: after every review, the strategy layer reads everything and
      # restructures TODO around the paper's honest thesis. May only edit
      # TODO.md and EDITORIAL.md (tamper guard + gates cover the rest).
      "$TIMEOUT" 15m codex exec -s workspace-write --skip-git-repo-check \
        -o "logs/editor-msg-$ITER.txt" "$(cat harness/EDITOR.md)" > "logs/editor-$ITER.log" 2>&1 || true

      # Humanizer lap (Matthew's rule, 2026-07-04): after review+editor, one pass
      # that rewrites prose for human flow. Facts are untouchable — macros, numbers,
      # claims, citations. Its edits are gated at the next lap; tags only ever point
      # at fully gated commits, so a bad rewrite can delay a tag but never fake one.
      echo "HUMANIZER pass at iter $ITER" | tee -a VERIFY.log
      "$TIMEOUT" 15m codex exec -s workspace-write --skip-git-repo-check \
        -o "logs/humanizer-msg-$ITER.txt" "$(cat harness/HUMANIZER.md)" > "logs/humanizer-$ITER.log" 2>&1 || true
    else
      echo "REVIEW FAILED at iter $ITER (quota or timeout) — will retry next review lap" | tee -a VERIFY.log
    fi
  fi

  # 5. Ratchet: tag paper-vN iff all gates green AND reviewer score >= last tagged score.
  #    TODO(practice): also shadow-tag every all-gates-green commit as green-vN regardless
  #    of review score, so there is ALWAYS a verified fallback to submit at 8 PM.
  harness/ratchet.sh "$ITER" || true

  git add -A && git commit -m "loop: iteration $ITER" --allow-empty -q
  # PUSH=1: livestream progress to the public repo (judges watch commits land).
  # --follow-tags (NOT --tags): only annotated tags on the pushed lineage go out —
  # --tags would leak every practice tag and its commit history to the public repo.
  if [[ -n "${PUSH:-}" ]]; then git push -q origin HEAD --follow-tags 2>/dev/null || true; fi
done
