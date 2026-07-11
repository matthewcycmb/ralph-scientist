#!/usr/bin/env bash
# Gate: compile the ICML paper and reject known silent presentation failures.
set -euo pipefail

BUILD_LOG=$(mktemp)
TEXT=$(mktemp)
trap 'rm -f "$BUILD_LOG" "$TEXT"' EXIT

if ! tectonic paper/main.tex >"$BUILD_LOG" 2>&1; then
  cat "$BUILD_LOG"
  echo "FAIL: Tectonic did not compile paper/main.tex"
  exit 1
fi

if grep -q 'Overfull \\hbox' "$BUILD_LOG"; then
  grep 'Overfull \\hbox' "$BUILD_LOG"
  echo "FAIL: paper has overfull horizontal boxes; shorten prose or tables"
  exit 1
fi

[[ -f paper/main.pdf ]] || { echo "FAIL: Tectonic did not produce paper/main.pdf"; exit 1; }
pdftotext paper/main.pdf "$TEXT"
if grep -q 'Title Suppressed Due to Excessive Size' "$TEXT"; then
  echo "FAIL: ICML suppressed the running title; preserve the short \\smash-wrapped running title"
  exit 1
fi

PAGES=$(pdfinfo paper/main.pdf | awk '/^Pages:/ {print $2}')
if [[ ! "$PAGES" =~ ^[0-9]+$ ]] || (( PAGES < 2 || PAGES > 4 )); then
  echo "FAIL: paper must be 2-4 pages, got ${PAGES:-unknown}"
  exit 1
fi

echo "PASS: paper compiles, fits 2-4 pages, has no suppressed title or overfull boxes"
