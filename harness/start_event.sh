#!/usr/bin/env bash
# One-command event launcher: preflight -> research loop -> dashboard -> W&B mirror.
set -euo pipefail
cd "$(dirname "$0")/.."

CHECK_ONLY=0
[[ "${1:-}" == "--check" ]] && CHECK_ONLY=1

fail() { echo "FATAL: $*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || fail "required command missing: $1"; }

[[ -z "$(git status --porcelain --untracked-files=normal)" ]] || fail "working tree is dirty"
[[ "$(git branch --show-current)" == "event-day" ]] || fail "start from the event-day branch"
git rev-parse event-day-start >/dev/null 2>&1 || fail "event-day-start tag missing"
git merge-base --is-ancestor event-day-start HEAD || fail "event-day-start is not on the current lineage"
git remote get-url origin >/dev/null 2>&1 || fail "origin remote missing"

for cmd in codex tectonic llama-completion llama-tokenize git curl lsof pgrep pdfinfo pdftotext; do need "$cmd"; done
need python3
need caffeinate
command -v timeout >/dev/null 2>&1 || command -v gtimeout >/dev/null 2>&1 \
  || fail "GNU timeout/gtimeout missing"

codex --version
if [[ "${WORKER_BACKEND:-codex}" == "claude" \
   || "${POST_REVIEW_BACKEND:-${WORKER_BACKEND:-codex}}" == "claude" \
   || "${REVIEW_BACKEND:-${WORKER_BACKEND:-codex}}" == "claude" ]]; then
  need claude
  claude auth status | grep -q '"loggedIn": true' \
    || fail "Claude worker requested but Claude Code is not logged in; run: claude auth login"
  claude --version
fi
make test
bash harness/gates/check_frozen.sh

WANDB_ENABLED=0
WANDB_PYTHON="${WANDB_PYTHON:-}"
if [[ -z "${SKIP_WANDB:-}" ]]; then
  if [[ -z "$WANDB_PYTHON" ]] && command -v wandb >/dev/null 2>&1; then
    WANDB_PYTHON=$(head -1 "$(command -v wandb)" | sed 's/^#!//')
  fi
  if [[ -n "$WANDB_PYTHON" && -x "$WANDB_PYTHON" ]] \
    && "$WANDB_PYTHON" -c 'import wandb' >/dev/null 2>&1 \
    && { [[ -n "${WANDB_API_KEY:-}" ]] || grep -q 'api.wandb.ai' "$HOME/.netrc" 2>/dev/null; }; then
    WANDB_ENABLED=1
  else
    echo "WARN: W&B unavailable; continuing because it is an optional event artifact" >&2
  fi
fi

if (( CHECK_ONLY )); then
  echo "PRECHECK PASS: event branch, tools, tests, frozen inputs, and W&B credentials are ready"
  exit 0
fi

if lsof -tiTCP:8788 -sTCP:LISTEN >/dev/null 2>&1; then
  fail "dashboard port 8788 is already in use"
fi

DASH_LOG=/tmp/ralph-dashboard.log
WANDB_LOG=/tmp/ralph-wandb.log
PIDS=/tmp/ralph-event.pids
LOOP_PID="" DASH_PID="" WANDB_PID=""

terminate_tree() {
  local root="${1:-}" pid child i
  [[ -n "$root" ]] || return 0
  # Snapshot the complete descendant tree before signalling. Background jobs
  # may create their own process groups, so group-only termination is not enough.
  local -a targets=("$root")
  i=0
  while (( i < ${#targets[@]} )); do
    pid="${targets[$i]}"
    while IFS= read -r child; do
      [[ -n "$child" ]] && targets+=("$child")
    done < <(pgrep -P "$pid" 2>/dev/null || true)
    i=$((i + 1))
  done
  for ((i=${#targets[@]}-1; i>=0; i--)); do
    kill -TERM "${targets[$i]}" 2>/dev/null || true
  done
  sleep 0.5
  for ((i=${#targets[@]}-1; i>=0; i--)); do
    kill -0 "${targets[$i]}" 2>/dev/null && kill -KILL "${targets[$i]}" 2>/dev/null || true
  done
}

cleanup() {
  trap - EXIT INT TERM
  terminate_tree "$LOOP_PID"
  terminate_tree "$DASH_PID"
  terminate_tree "$WANDB_PID"
  [[ -n "$LOOP_PID" ]] && wait "$LOOP_PID" 2>/dev/null || true
  [[ -n "$DASH_PID" ]] && wait "$DASH_PID" 2>/dev/null || true
  [[ -n "$WANDB_PID" ]] && wait "$WANDB_PID" 2>/dev/null || true
  rm -f "$PIDS"
}
trap cleanup EXIT INT TERM

NOW_HHMM=$(date +%H%M)
if [[ -z "${ALLOW_OUTSIDE_EVENT_WINDOW:-}" ]] && (( 10#$NOW_HHMM < 1230 || 10#$NOW_HHMM >= 1530 )); then
  fail "official Ralph Loop window is 12:30-15:30 KST (now $(date +%H:%M))"
fi
OFFICIAL_TAG="${OFFICIAL_TAG:-official-loop-start-20260712-1230}"
if git rev-parse "$OFFICIAL_TAG" >/dev/null 2>&1; then
  git merge-base --is-ancestor "$OFFICIAL_TAG^{commit}" HEAD \
    || fail "$OFFICIAL_TAG is not an ancestor of the restart commit"
else
  git tag -a "$OFFICIAL_TAG" -m "Official Ralph Loop boundary, 2026-07-12 12:30 KST"
fi

echo "STARTING research loop (worker=${WORKER_BACKEND:-codex}, PUSH=${PUSH:-1})"
# Monitor mode keeps top-level jobs distinct; cleanup also walks descendants
# because nested background agents can create additional process groups.
set -m
caffeinate -is env PUSH="${PUSH:-1}" harness/loop.sh &
LOOP_PID=$!

harness/dashboard.sh >"$DASH_LOG" 2>&1 &
DASH_PID=$!

if (( WANDB_ENABLED )); then
  "$WANDB_PYTHON" harness/dashboard/wandb_mirror.py >"$WANDB_LOG" 2>&1 &
  WANDB_PID=$!
fi

printf 'loop=%s\ndashboard=%s\nwandb=%s\n' "$LOOP_PID" "$DASH_PID" "${WANDB_PID:-disabled}" > "$PIDS"

for _ in {1..20}; do
  kill -0 "$LOOP_PID" 2>/dev/null || fail "research loop exited during startup"
  kill -0 "$DASH_PID" 2>/dev/null || fail "dashboard exited; inspect $DASH_LOG"
  if curl -fsS http://127.0.0.1:8788/harness/dashboard/ >/dev/null 2>&1; then break; fi
  sleep 1
done
curl -fsS http://127.0.0.1:8788/harness/dashboard/ >/dev/null \
  || fail "dashboard did not become healthy; inspect $DASH_LOG"
if [[ -n "$WANDB_PID" ]] && ! kill -0 "$WANDB_PID" 2>/dev/null; then
  echo "WARN: W&B mirror exited; paper loop continues (inspect $WANDB_LOG)" >&2
  WANDB_PID=""
fi

echo "EVENT RUNNING"
echo "  dashboard: http://127.0.0.1:8788/harness/dashboard/"
echo "  dashboard log: $DASH_LOG"
echo "  W&B log: $WANDB_LOG"
echo "  process file: $PIDS"
echo "Press Ctrl-C only when the event run should stop."

wait "$LOOP_PID"
