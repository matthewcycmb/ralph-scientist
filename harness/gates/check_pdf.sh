#!/usr/bin/env bash
# Gate: compile the ICML paper and reject known silent presentation failures.
set -euo pipefail

BUILD_LOG=$(mktemp)
TEXT=$(mktemp)
trap 'rm -f "$BUILD_LOG" "$TEXT"' EXIT

if ! tectonic --keep-intermediates paper/main.tex >"$BUILD_LOG" 2>&1; then
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
if [[ ! "$PAGES" =~ ^[0-9]+$ ]] || (( PAGES < 2 )); then
  echo "FAIL: compiled paper must contain at least 2 pages, got ${PAGES:-unknown}"
  exit 1
fi

MAIN_BODY_PAGE=$(sed -n 's/.*\\newlabel{main-body-end}{{[^}]*}{\([0-9][0-9]*\)}.*/\1/p' paper/main.aux | tail -1)
if [[ ! "$MAIN_BODY_PAGE" =~ ^[0-9]+$ ]]; then
  echo "FAIL: add \\label{main-body-end} immediately before references/appendices"
  exit 1
fi
if (( MAIN_BODY_PAGE < 2 || MAIN_BODY_PAGE > 4 )); then
  echo "FAIL: main body must be 2-4 pages, ends on page $MAIN_BODY_PAGE"
  exit 1
fi

if grep -Eiq 'Matthew Chan|jchanh@gmail\.com|Ralph Scientist|Ralphthon *@?ICML|Track One|Seoul' "$TEXT"; then
  echo "FAIL: PDF exposes author, affiliation, email, or event identity; submission must be anonymous"
  exit 1
fi
PDF_AUTHOR=$(pdfinfo paper/main.pdf | sed -n 's/^Author:[[:space:]]*//p')
if [[ -n "$PDF_AUTHOR" ]] && ! grep -Eiq '^anonymous( authors?)?$' <<<"$PDF_AUTHOR"; then
  echo "FAIL: PDF Author metadata is not anonymous: $PDF_AUTHOR"
  exit 1
fi

echo "PASS: paper compiles, main body fits 2-4 pages, identity is hidden, and layout is clean"
