# Paper Outline

Draft from this outline into `paper/main.tex`. Every empirical quantity must appear
through a macro generated in `paper/values.tex`.

## Abstract

- Name the exact frozen Qwen2.5 model artifact and the synthetic contract-clause task.
- State the measured context tiers and probe counts through macros.
- Lead with the strongest comparison the design genuinely supports.
- Call sparse or inconclusive axes inconclusive; do not promote pilot evidence.
- Close with the practical takeaway and the narrow scope.

## Introduction

- Open with the one recurring scene: a vendor clause and a look-alike buyer clause in a
  long contract.
- Explain that the probes are synthetic, gradeable versions of that situation.
- End with four plain questions: context amount, target position, filler quality, and
  the paired keyword-pruning mitigation.
- Preview only results supported by matched comparisons and adequate cell counts.

## Related Work

- Use `liu2023lost` for position effects and `levy2024same` for input length.
- Use `shi2023distracted` for irrelevant context.
- Use `hsieh2024ruler` and `modarressi2025nolima` for hard retrieval evaluation.
- Use `qwen2024qwen25` for the model family and `dodge2019show` for reporting practice.
- State precisely how this laptop-scale deterministic grid differs from each precedent.

## Probe Design

- Name `qwen2.5-0.5b-instruct-q8_0.gguf`, its checksum, llama.cpp, greedy decoding,
  and the fixed seed.
- Explain tokenizer-measured context tiers and report actual counts, never planning labels.
- Define target clause, distractor clause, literal and paraphrased questions, and filler types.
- Generate a scenario family independently of target position, then move only the target
  clause across start, middle, and end. This makes the position result paired.
- Balance relevant and irrelevant filler within every tier used for a quality comparison.
- Place distractors independently of target position.
- Explain the resumable manifest and one-file-per-output layout.

## Scoring and Comparisons

- Define exact-answer scoring, distractor capture, invalid output, and exact-output compliance.
- Report per-cell n and Wilson intervals for every accuracy estimate.
- Amount: compare adequately populated tokenizer-measured tiers; do not claim a threshold
  unless the grid can locate one.
- Position: use the matched scenario families and report paired changes.
- Quality: compare matched cases at the same amount, position, and question wording.
- Mitigation: compute the pruning gain only over scenarios having both full and pruned runs.
- Include closed-book, regex, and deterministic-random baselines.

## Results

- Answer each question directly before presenting tables.
- Use no more tables than the evidence needs. Prefer one central paired-position table,
  one amount/quality table with explicit n, and one mitigation/baseline table.
- After each table, give one plain-language contract-clause interpretation.
- Separate findings, null results, and design limitations. Never make an unpaired contrast
  sound like an intervention.

## Limitations

- One small quantized model; findings may not transfer to larger models.
- Synthetic lookups, not natural contracts or general model capability.
- CPU-budgeted grid and any sparse cells.
- Greedy decoding only; no sampling variance.
- Simple keyword filter, not a learned retrieval system.
- Any remaining unmatched or exploratory comparison named explicitly.

## Reproducibility

- Trace model checksum → probe manifest/raw outputs → `run_all.py` → `results.json` →
  `values.tex` → PDF.
- State that `make all` rebuilds scoring and the paper from cached raw outputs.
- State separately that `make clean-deep && make all` repeats model inference.
- Name the frozen-input, citation, numeric-literal, freshness, sanity, style, and compile gates.
