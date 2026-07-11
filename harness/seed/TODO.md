# TODO

Seed state — the loop has not started. Highest leverage first.

- [ ] Build analysis/run_probes.py around MATCHED scenario families. Generate answer,
  distractor, filler, and question once per family; move only the target clause across
  start/middle/end. Keep distractor placement independent. This is required for a valid
  paired position result.
- [ ] Size the tokenizer-verified grid before inference. Fully populate the shortest and
  middle tiers; reserve about 12 balanced probes for the largest tier as SPEC requires.
  Never repeat rehearsal v13's 3-probe middle/largest tiers. Stay within the measured
  45-minute CPU budget and make every probe resumable by stable id.
- [ ] Balance relevant/irrelevant filler inside every tier used for RQ3. Include literal and
  paraphrased questions with near-match distractors. Record exact model filename, SHA-256,
  seed, command, measured token counts, and manifest completeness.
- [ ] Build analysis/run_all.py from data/probes/ only. Score exact-code compliance,
  accuracy, invalid outputs, and distractor captures. Aggregate amount with per-tier n;
  position from matched families; quality from matched cells; pruning gain from the same
  scenarios under full and pruned context. Never subtract unmatched populations.
- [ ] Generate results.json per analysis/RESULTS_SCHEMA.md, then `make values`. Report all
  per-cell counts, uncertainty intervals, paired wins/losses, missing probes, and exact-output
  compliance. A partial manifest is valid work-in-progress but cannot be presented as final.
- [ ] Draft from paper/OUTLINE.md. Name the exact Qwen artifact. Make the honest thesis
  follow the strongest supported comparison; call sparse or null axes inconclusive.
- [ ] Produce a 2–4 page ICML paper with at least 2 useful tables/figures, the recurring
  contract example, all four questions answered, required limitations, and Reproducibility.
- [ ] Cite only verified context-wing exemplars. Read their frozen full text before writing
  Related Work. New citations must be resolved by the harness citation gate.
- [ ] First full seven-gate pass plus reviewer rubric >= 6 produces paper-v1. Confirm that
  the tag targets the verified checkpoint, not the preceding lap.
