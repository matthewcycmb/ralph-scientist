# Ralph Scientist pipeline. The loop's gates call these targets.
PY := .venv/bin/python
TECTONIC := tectonic

.PHONY: all probes results values paper verify test clean clean-deep

all: results values paper

# TIER 1 — expensive, deterministic inference. The agent creates
# analysis/run_probes.py: seeded generators build every prompt file, the frozen
# model runs on each (llama-completion, --temp 0 --seed 42), raw outputs land in
# data/probes/. Re-run explicitly whenever the experiment grid changes.
probes:
	$(PY) analysis/run_probes.py

# Raw probe outputs are rebuilt automatically only when absent (clean-deep).
data/probes:
	$(PY) analysis/run_probes.py

# TIER 2 — fast (< 1 min), re-run by the pipeline-fresh gate every lap.
# The agent creates analysis/run_all.py — reads data/probes/, scores and
# aggregates into results.json (contract: analysis/RESULTS_SCHEMA.md).
results: | data/probes
	$(PY) analysis/run_all.py

values:
	$(PY) analysis/make_values.py

paper: values
	$(TECTONIC) paper/main.tex

verify:
	harness/run_gates.sh manual

test:
	PYTHONDONTWRITEBYTECODE=1 $(PY) -m unittest discover -v tests

# Wipe the cheap tier's artifacts; probes stay (they are expensive and frozen).
clean:
	rm -f results.json paper/values.tex paper/main.pdf

# Clean-room proof: wipe EVERYTHING computed, including raw model outputs.
# `make clean-deep && make all` re-runs all inference (budget: ~45 min).
clean-deep: clean
	rm -rf data/probes
