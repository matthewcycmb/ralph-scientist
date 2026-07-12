#!/usr/bin/env bash
# Ralph loop: fresh Codex iteration -> deterministic gates -> periodic adversarial review -> ratchet.
set -uo pipefail
cd "$(dirname "$0")/.."
# Never inherit a live stdin: a silent-but-open input pipe from the launcher made
# codex wait for EOF until the role timeout killed it (reviews died this way twice,
# 2026-07-07). The loop needs no stdin — sever it once, for every child.
exec < /dev/null

# Event provenance depends on starting from a declared commit. Refuse to let
# pre-run harness edits or forgotten files become "iteration 1" by accident.
if [[ -n "$(git status --porcelain --untracked-files=normal)" ]]; then
  echo "FATAL: working tree is dirty. Commit the declared pre-run state before starting the loop."
  git status --short
  exit 1
fi

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

# Pin the event agent configuration independently of the operator's global Codex
# defaults. All five roles use the same model and reasoning effort so a machine-
# local xhigh setting cannot silently make laps slower during the event.
CODEX_MODEL="${CODEX_MODEL:-gpt-5.6-sol}"
CODEX_REASONING_EFFORT="${CODEX_REASONING_EFFORT:-high}"
WORKER_BACKEND="${WORKER_BACKEND:-codex}"
CLAUDE_MODEL="${CLAUDE_MODEL:-fable}"
CLAUDE_EFFORT="${CLAUDE_EFFORT:-high}"
if [[ "$WORKER_BACKEND" != "codex" && "$WORKER_BACKEND" != "claude" ]]; then
  echo "FATAL: WORKER_BACKEND must be codex or claude, got $WORKER_BACKEND"
  exit 1
fi
echo "AGENTS: worker=$WORKER_BACKEND codex=$CODEX_MODEL/$CODEX_REASONING_EFFORT claude=$CLAUDE_MODEL/$CLAUDE_EFFORT"

# --- Anti-reward-hacking guard (risk A) --------------------------------------
# Fingerprint the harness in memory at loop start. Agents can write anywhere in
# the workspace, but this loop process (and the baseline) live outside their
# reach: any lap that modifies harness/ or Makefile gets auto-reverted + logged.
START_SHA=$(git rev-parse HEAD)
harness_fingerprint() {
  cat harness/loop.sh harness/checkpoint.sh harness/review_due.sh harness/run_gates.sh harness/ratchet.sh harness/REVIEWER.md harness/ASSIGNMENT_REVIEW.md \
      harness/extract_claude_result.py \
      harness/EDITOR.md harness/HUMANIZER.md harness/gates/* Makefile PROMPT.md SPEC.md \
      analysis/make_values.py analysis/RESULTS_SCHEMA.md data/models/CHECKSUMS.txt \
      data/models/FETCH.sh data/cache/nlsy97/CHECKSUMS.txt requirements.txt \
      paper/model.tex paper/*.sty paper/*.bst 2>/dev/null | shasum -a 256 | cut -d' ' -f1
}
BASELINE_FP=$(harness_fingerprint)

restore_protected_files() {
  if [[ "$(harness_fingerprint)" != "$BASELINE_FP" ]]; then
    echo "TAMPER: protected harness inputs modified at iter $ITER — restoring from $START_SHA" | tee -a VERIFY.log
    git checkout "$START_SHA" -- harness/loop.sh harness/checkpoint.sh harness/review_due.sh harness/run_gates.sh \
      harness/ratchet.sh harness/REVIEWER.md harness/ASSIGNMENT_REVIEW.md harness/EDITOR.md harness/HUMANIZER.md \
      harness/extract_claude_result.py \
      harness/gates Makefile PROMPT.md SPEC.md analysis/make_values.py \
      analysis/RESULTS_SCHEMA.md data/models/CHECKSUMS.txt data/models/FETCH.sh \
      data/cache/nlsy97/CHECKSUMS.txt requirements.txt paper/*.sty paper/*.bst
    git checkout "$START_SHA" -- paper/model.tex
    echo "- [ ] TAMPER DETECTED (iter $ITER): an agent modified protected harness or frozen-input metadata. The harness restored it; fix the underlying problem instead." >> TODO.md
  fi
}

citation_fingerprint() {
  find data/cache/citations -type f -print 2>/dev/null | LC_ALL=C sort | while IFS= read -r file; do
    shasum -a 256 "$file"
  done | shasum -a 256 | cut -d' ' -f1
}

ITER=0
while true; do
  ITER=$((ITER + 1))
  # Bounded runs for rehearsal: MAX_ITERS=3 harness/loop.sh
  if [[ -n "${MAX_ITERS:-}" && "$ITER" -gt "$MAX_ITERS" ]]; then
    echo "=== MAX_ITERS=$MAX_ITERS reached, loop ends ==="
    exit 0
  fi
  echo "=== iteration $ITER $(date +%H:%M:%S) ==="
  CITATION_FP=$(citation_fingerprint)

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
  REVIEW_CAP_MIN="${REVIEW_CAP_MIN:-12}"
  ROLE_CAP_MIN="${ROLE_CAP_MIN:-8}"
  # Log goes straight to the file (no tee): $! must hold the timeout/codex process
  # itself so the watchdog's kill reaches the agent, not a log pipe. Live view:
  # tail -f the iter log. GNU timeout forwards TERM to its child.
  echo "agent streaming to logs/iter-$ITER.log"
  ACTIVE_WORKER_BACKEND="$WORKER_BACKEND"
  if [[ "$ACTIVE_WORKER_BACKEND" == "claude" ]]; then
    "$TIMEOUT" "${AGENT_CAP_MIN}m" claude -p --model "$CLAUDE_MODEL" \
      --effort "$CLAUDE_EFFORT" --permission-mode acceptEdits \
      --no-session-persistence --output-format stream-json --verbose \
      --include-partial-messages "$(cat PROMPT.md)" > "logs/iter-$ITER.log" 2>&1 &
  else
    "$TIMEOUT" "${AGENT_CAP_MIN}m" codex exec -m "$CODEX_MODEL" \
      -c "model_reasoning_effort=\"$CODEX_REASONING_EFFORT\"" \
      -s workspace-write --skip-git-repo-check \
      -o "logs/last-msg-$ITER.txt" "$(cat PROMPT.md)" > "logs/iter-$ITER.log" 2>&1 &
  fi
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
  if [[ "$ACTIVE_WORKER_BACKEND" == "claude" ]]; then
    .venv/bin/python harness/extract_claude_result.py \
      "logs/iter-$ITER.log" "logs/last-msg-$ITER.txt" || true
  fi

  # Quota-outage backoff (found in endurance run 2026-07-02): a lap that dies on
  # usage limits must not spin no-op laps — sleep and let the quota window recover.
  if grep -Eqi "hit your usage limit|usage limit|rate[_ -]?limit" "logs/iter-$ITER.log" 2>/dev/null; then
    if [[ "$ACTIVE_WORKER_BACKEND" == "claude" ]]; then
      echo "QUOTA: Claude limit hit at iter $ITER — retrying this lap with Codex" | tee -a VERIFY.log
      WORKER_BACKEND=codex
      ITER=$((ITER - 1))
      continue
    fi
    echo "QUOTA: usage limit hit at iter $ITER — sleeping 10 min before retry" | tee -a VERIFY.log
    ITER=$((ITER - 1))   # quota waits don't consume the lap budget
    sleep 600
    continue
  fi

  # 2. Anti-reward-hacking: restore protected code and reject citation-cache records
  #    written by the worker. Only the networked harness citation gate may add cache files.
  restore_protected_files
  if [[ "$(citation_fingerprint)" != "$CITATION_FP" ]]; then
    echo "TAMPER: citation cache modified by worker at iter $ITER — restoring committed cache" | tee -a VERIFY.log
    git checkout HEAD -- data/cache/citations 2>/dev/null || true
    git clean -fd -- data/cache/citations >/dev/null 2>&1 || true
    echo "- [ ] TAMPER DETECTED (iter $ITER): citation cache changes must come from the networked citation gate, not a worker." >> TODO.md
  fi

  # 3. Deterministic gates (never skipped, never agent-run). Failures land in TODO.md.
  harness/run_gates.sh "$ITER" || true

  # 4. Decide whether review is due, then checkpoint BEFORE spending reviewer time.
  #    This guarantees a green fallback tag even if review hits the event deadline.
  REVIEW_DUE=0
  REVIEW_COMPLETED=0
  if bash harness/review_due.sh "$ITER"; then
    REVIEW_DUE=1
  fi

  # Commit the exact gated state and mint its green fallback immediately. This fixes
  # both the historical one-lap tag lag and the deadline risk from slow reviewers.
  bash harness/checkpoint.sh "$ITER"

  # 5. Review the first fully green paper immediately, then every three completed
  #    laps. The read-only reviewer cannot edit the checkpoint it judges.
  if [[ "$REVIEW_DUE" -eq 1 ]]; then
    # Draft archive: snapshot the compiled paper every review lap — the progress story.
    mkdir -p drafts
    [[ -f paper/main.pdf ]] && cp paper/main.pdf "drafts/iter-$ITER.pdf"

    # Criticism ledger anchor: the previous review, captured BEFORE this lap's review
    # file exists. The confirmation read reconciles against the same anchor.
    PREV_REVIEW=$(ls -t reviews/iter-*.md 2>/dev/null | head -1)
    REVIEWER_PROMPT="$(cat harness/REVIEWER.md)

Previous review for the ledger: ${PREV_REVIEW:-none — first review, every ledger item is new}"

    # -o captures ONLY the reviewer's final message (the review); full stream -> logs/.
    "$TIMEOUT" "${REVIEW_CAP_MIN}m" codex exec -m "$CODEX_MODEL" \
      -c "model_reasoning_effort=\"$CODEX_REASONING_EFFORT\"" \
      -s read-only --skip-git-repo-check \
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
        "$TIMEOUT" "${REVIEW_CAP_MIN}m" codex exec -m "$CODEX_MODEL" \
          -c "model_reasoning_effort=\"$CODEX_REASONING_EFFORT\"" \
          -s read-only --skip-git-repo-check \
          -o "reviews/confirm-$ITER.md" "$REVIEWER_PROMPT" > "logs/confirm-$ITER.log" 2>&1 || true
      fi
      # Promote the already-committed checkpoint using the fresh review. Do not create
      # a second green tag for the same commit.
      RATCHET_PAPER_ONLY=1 harness/ratchet.sh "$ITER" || true
      REVIEW_COMPLETED=1
    else
      echo "REVIEW FAILED at iter $ITER (quota or timeout) — will retry next review lap" | tee -a VERIFY.log
    fi
  fi

  # 6. Strategy/prose roles run only after the verified checkpoint. Their changes are
  #    intentionally not included in this lap's tag; the next lap's gates inspect them.
  if [[ "$REVIEW_COMPLETED" -eq 1 ]]; then
    "$TIMEOUT" "${ROLE_CAP_MIN}m" codex exec -m "$CODEX_MODEL" \
      -c "model_reasoning_effort=\"$CODEX_REASONING_EFFORT\"" \
      -s workspace-write --skip-git-repo-check \
      -o "logs/editor-msg-$ITER.txt" "$(cat harness/EDITOR.md)" > "logs/editor-$ITER.log" 2>&1 || true
    echo "HUMANIZER pass at iter $ITER" | tee -a VERIFY.log
    "$TIMEOUT" "${ROLE_CAP_MIN}m" codex exec -m "$CODEX_MODEL" \
      -c "model_reasoning_effort=\"$CODEX_REASONING_EFFORT\"" \
      -s workspace-write --skip-git-repo-check \
      -o "logs/humanizer-msg-$ITER.txt" "$(cat harness/HUMANIZER.md)" > "logs/humanizer-$ITER.log" 2>&1 || true
    restore_protected_files
    if [[ -n "$(git status --porcelain -- data/cache/citations)" ]]; then
      echo "TAMPER: citation cache modified by post-review role at iter $ITER — restoring checkpoint" | tee -a VERIFY.log
      git checkout HEAD -- data/cache/citations 2>/dev/null || true
      git clean -fd -- data/cache/citations >/dev/null 2>&1 || true
      echo "- [ ] TAMPER DETECTED (iter $ITER): a post-review role modified the citation cache; the checkpoint copy was restored." >> TODO.md
    fi
  fi

  # Persist ratchet logs and post-review edits without moving the verified tag.
  git add -A
  if ! git diff --cached --quiet; then
    git commit -m "harness: follow-up after iteration $ITER" -q
  fi
  # PUSH=1: livestream progress to the public repo (judges watch commits land).
  # --follow-tags (NOT --tags): only annotated tags on the pushed lineage go out —
  # --tags would leak every practice tag and its commit history to the public repo.
  if [[ -n "${PUSH:-}" ]]; then git push -q origin HEAD --follow-tags 2>/dev/null || true; fi
done
