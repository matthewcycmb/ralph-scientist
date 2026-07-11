#!/usr/bin/env bash
# Live dashboard: regenerates logs/status.json every 3s and serves the repo
# read-only on http://127.0.0.1:8788 — safe to run alongside the loop.
# Open: http://127.0.0.1:8788/harness/dashboard/
set -uo pipefail
cd "$(dirname "$0")/.."

( while true; do .venv/bin/python harness/dashboard/gen_status.py >/dev/null 2>&1; sleep 3; done ) &
GEN=$!

echo "Dashboard: http://127.0.0.1:8788/harness/dashboard/"
.venv/bin/python -m http.server 8788 --bind 127.0.0.1 &
SERVER=$!
trap 'kill $GEN $SERVER 2>/dev/null || true' EXIT INT TERM
wait "$SERVER"
