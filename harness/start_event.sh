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

for cmd in codex tectonic llama-completion llama-tokenize git curl lsof pdfinfo pdftotext; do need "$cmd"; done
need python3
need caffeinate
command -v timeout >/dev/null 2>&1 || command -v gtimeout >/dev/null 2>&1 \
  || fail "GNU timeout/gtimeout missing"

codex --version
make test
bash harness/gates/check_frozen.sh

if [[ -z "${SKIP_WANDB:-}" ]]; then
  WANDB_PYTHON="${WANDB_PYTHON:-}"
  if [[ -z "$WANDB_PYTHON" ]] && command -v wandb >/dev/null 2>&1; then
    WANDB_PYTHON=$(head -1 "$(command -v wandb)" | sed 's/^#!//')
  fi
  [[ -n "$WANDB_PYTHON" && -x "$WANDB_PYTHON" ]] \
    || fail "could not locate the Python runtime used by the wandb executable"
  "$WANDB_PYTHON" -c 'import wandb' >/dev/null 2>&1 \
    || fail "$WANDB_PYTHON cannot import wandb"
  if [[ -z "${WANDB_API_KEY:-}" ]] && ! grep -q 'api.wandb.ai' "$HOME/.netrc" 2>/dev/null; then
    fail "W&B login missing (set WANDB_API_KEY or run python3 -m wandb login); use SKIP_WANDB=1 only intentionally"
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

cleanup() {
  trap - EXIT INT TERM
  [[ -n "$DASH_PID" ]] && kill "$DASH_PID" 2>/dev/null || true
  [[ -n "$WANDB_PID" ]] && kill "$WANDB_PID" 2>/dev/null || true
  [[ -n "$LOOP_PID" ]] && kill "$LOOP_PID" 2>/dev/null || true
  rm -f "$PIDS"
}
trap cleanup EXIT INT TERM

echo "STARTING research loop (PUSH=${PUSH:-1})"
caffeinate -is env PUSH="${PUSH:-1}" harness/loop.sh &
LOOP_PID=$!

harness/dashboard.sh >"$DASH_LOG" 2>&1 &
DASH_PID=$!

if [[ -z "${SKIP_WANDB:-}" ]]; then
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
if [[ -n "$WANDB_PID" ]]; then
  kill -0 "$WANDB_PID" 2>/dev/null || fail "W&B mirror exited; inspect $WANDB_LOG"
fi

echo "EVENT RUNNING"
echo "  dashboard: http://127.0.0.1:8788/harness/dashboard/"
echo "  dashboard log: $DASH_LOG"
echo "  W&B log: $WANDB_LOG"
echo "  process file: $PIDS"
echo "Press Ctrl-C only when the event run should stop."

wait "$LOOP_PID"
