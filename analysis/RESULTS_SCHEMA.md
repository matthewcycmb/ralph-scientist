# results.json — the contract

Single file at repo root. ONLY analysis scripts write it (never by hand — the
clean-room re-run gate deletes and regenerates it). Everything the paper
states numerically must live here.

```json
{
  "meta": {
    "generated_by": "analysis/run_all.py",
    "data": "data/probes/ (raw outputs of the frozen model in data/models/)",
    "model_file": "data/models/qwen2.5-0.5b-instruct-q8_0.gguf",
    "model_sha256": "ca59ca7f13d0e15a8cfa77bd17e65d24f6844b554a7b6c12e07a5f89ff76844e",
    "manifest_complete": true,
    "missing_probe_count": 0
  },
  "values": {
    "sampleSize":       {"value": 216,  "unit": "count", "desc": "total probes scored across the full grid", "script": "analysis/run_all.py"},
    "accTwoK":          {"value": 91.7, "unit": "pct", "fmt": ".1f", "desc": "retrieval accuracy at ~2k-token context, all positions", "script": "analysis/run_all.py"},
    "middleDropEightK": {"value": 25.0, "unit": "pct", "fmt": ".1f", "desc": "accuracy drop, middle vs start position, at ~8k tokens", "script": "analysis/run_all.py"}
  }
}
```

Rules (enforced by harness/gates/check_sanity.py):
- `values` keys: **letters only** (each becomes the LaTeX macro `\keyName`).
- Every entry: finite numeric `value`, non-empty `desc` and `script`.
- Units: `pct` ∈ [0,100] · `corr` ∈ [-1,1] · `pvalue` ∈ [0,1] · `count` · `tokens` ·
  `seconds` · `raw` (`usd` stays legal for the NLSY fallback topic).
- Reserved key `sampleSize` is REQUIRED and must be ≥ 100 — here it means the
  total number of scored probes; report per-cell probe counts as their own entries.
- Optional `fmt`: Python format spec used by make_values.py (e.g. `.2f`, `,.0f`).
- `meta.generated_by` and every value's `script` must name existing repository Python files.
- Units are restricted to the list above; counts are non-negative integers, while token
  means and durations may be non-negative decimals.
- For the primary topic, record the exact model file/checksum and manifest completion in
  `meta`. A partial manifest is valid work-in-progress but must be described as such.
- Include matched position, filler-quality, and pruning summaries. The pruning gain must use
  the paired full/pruned denominator. Include exact-output compliance and invalid-output count.

Two-tier pipeline: `make probes` runs `analysis/run_probes.py` (you create it) —
seeded generators emit every prompt file, the frozen model runs on each
(llama-completion, --temp 0 --seed 42), raw outputs land in `data/probes/`.
`make results` runs `analysis/run_all.py` (you create it; it may import
siblings) — it reads `data/probes/` ONLY, never invokes the model, and must
finish in under a minute: the pipeline-fresh gate re-runs it every lap.
Scoring must be deterministic code (exact/normalized match rules you define),
never another model call.
