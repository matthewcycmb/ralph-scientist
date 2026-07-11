# TODO

Seed state — the loop has not started. Highest leverage first.

- [ ] analysis/run_probes.py — seeded generators (fixed seed) build the haystack/probe
  grid from SPEC.md: amount (~2k/4k/8k tokens) × position (start/middle/end) × quality
  (relevant-redundant vs irrelevant filler), literal AND paraphrase probes with
  near-match distractors; verify tier sizes with llama-tokenize BEFORE the run
  (instant; measured tokens decide the tier labels — never chars-per-token
  estimates); run the frozen model on each (llama-completion, --temp 0
  --seed 42, see SPEC for the exact command); raw outputs → data/probes/. Size the grid
  to the 45-minute budget (~6s/16s/28s per probe at 2k/4k/8k) — ~200 probes total.
- [ ] analysis/run_all.py — read data/probes/ ONLY (never call the model), score with
  deterministic match rules, aggregate per grid cell → results.json per
  analysis/RESULTS_SCHEMA.md (sampleSize = total scored probes; report per-cell counts)
- [ ] make values → paper/values.tex macros from results.json
- [ ] Draft the paper OUTLINE first (as comments in main.tex), then prose from the
  outline — outline-first measurably beats draft-first
- [ ] Write sections in the ICML template using macros only; claims DESCRIPTIVE of the
  tested model, never "all LLMs"; report probe counts for every estimate; state the CPU
  probe budget honestly
- [ ] RQ4 mitigation comparison: key-fact-first/last placement and keyword-overlap
  pruning, measured on the same grid
- [ ] At least 2 tables/figures; 2–4 pages (host rule); honest Limitations (small quantized model,
  synthetic probes, retrieval ≠ general capability, greedy decoding only);
  Reproducibility Statement
- [ ] Cite only verified entries (context-wing exemplars pre-verified in paper/refs.bib +
  data/cache/citations/; full texts in data/exemplars/ — READ them before Related Work);
  new citations must survive the harness citation gate
- [ ] First full gate pass + reviewer ≥ 6 → paper-v1
