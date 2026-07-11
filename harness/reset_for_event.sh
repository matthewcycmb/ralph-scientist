#!/usr/bin/env bash
# Create the clean event-day starting state on a fresh orphan branch.
#
# Keeps (the declared pre-built inputs): harness/, SPEC.md, PROMPT.md, Makefile,
# frozen model (CHECKSUMS.txt + FETCH.sh) + data caches + citation cache, exemplar
# library, ICML template + skeleton main.tex, verified refs.bib, venv pins, docs
# (README/FLOWCHART/PLAN).
# Removes (event work must be born at the event): the practice paper's prose,
# analysis scripts the agents wrote, raw probe outputs (data/probes/), results.json,
# values.tex, reviews, logs, VERIFY.log, DONE.md. TODO.md resets to the canonical seed.
#
# Practice history stays untouched on the original branch.
set -euo pipefail
cd "$(dirname "$0")/.."
BRANCH="${1:-event-day}"

git diff --quiet && git diff --cached --quiet || { echo "ABORT: working tree dirty — commit first"; exit 1; }
git rev-parse --verify "$BRANCH" >/dev/null 2>&1 && { echo "ABORT: branch $BRANCH already exists"; exit 1; }

git checkout --orphan "$BRANCH"

rm -f results.json paper/values.tex paper/main.pdf VERIFY.log DONE.md EDITORIAL.md
rm -rf reviews logs drafts runs data/probes
mkdir -p reviews logs drafts data/exemplars
# Agent-written analysis from practice runs (harness tools make_values.py / RESULTS_SCHEMA.md stay):
find analysis -name "*.py" ! -name "make_values.py" -delete
cp harness/seed/main.tex paper/main.tex
cp harness/seed/TODO.md TODO.md

git add -A
git commit -q -m "Pre-built inputs: harness, SPEC, frozen model + data caches (declared; authored before event start)"
echo "Event branch '$BRANCH' ready (single clean commit)."
# NOTE: never push --tags from this repo — it would carry every practice tag (and the
# commits they reach) into the public event repo. Event tags push individually as minted.
echo "Next: create the public GitHub repo, then: git push -u origin $BRANCH"
