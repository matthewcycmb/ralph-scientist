# DONE

## Lap 1 (2026-07-12)

- Built analysis/run_probes.py: matched scenario families (target clause,
  distractor, filler, question generated per family with zlib.crc32 seeds and
  no position in any seed; only the target clause moves across start/mid/end).
  Distractor depth fixed per family at 0.25 or 0.75, independent of target.
  Relevant/irrelevant filler balanced in every tier. Paraphrase design:
  question phrasing literally matches the DISTRACTOR clause, target clause
  states the answer in different words (NoLiMa-style). Literal-control probes
  at 2k reuse the identical filler as their paraphrase twins.
- Tokenizer-verified sizing: measured tier means 1989 / 3986 / 7992 tokens
  (nominal 2k/4k/8k), every probe's measured count in the manifest. Sizing
  counts and measured tokens cached in the manifest so resumes cost zero
  tokenize calls.
- Ran the FULL 120-probe grid to completion (~25 min wall, under the 45-min
  clean-room budget): 36 t2k full + 6 t2k literal + 30 t4k full + 30 t4k
  pruned + 12 t8k full + 6 closed-book. manifest_complete=true, raw outputs
  one file per probe in data/probes/out/, atomic writes, resumable by id.

## Lap 2 (2026-07-12)

- Built stdlib-only analysis/run_all.py. It reads only the manifest and raw
  outputs, strips the fixed runner trailer, and defines code-only compliance,
  normalized correctness, distractor capture, invalid output, and extra output.
- Generated results.json and paper/values.tex with Wilson intervals and counts.
  Amount uses the 12 families/filler/position cells shared across every tier;
  position uses paired clause moves; quality uses matched filler pairs; pruning
  uses the exact 30 full/pruned intersections with wins, losses, and ties.
- Confirmed the main signals: a strong end-position recency effect, worse results
  with relevant filler at the populated tiers, no degradation across the matched
  amount tiers, and a 33.3-point loss from keyword pruning.
- Individual sanity and numeric-literal gates pass. Cheap regeneration is
  deterministic and completes in well under one minute.

## Lap 3 (2026-07-12)

- Drafted the complete anonymous ICML short paper from the computed registry:
  five-sentence abstract, visible four-question list, paired design and scoring,
  three result tables, required limitations, and reproducibility statement.
- Centered the thesis on the paired end-position advantage and matched pruning
  backfire. Reported the amount result as inconclusive and the longest-tier
  position and quality cells as sparse.
- Activated only citations already present in the resolver cache. Individual
  number, style, submission, and citation gates pass.

## Lap 4 (2026-07-12)

- Fixed the sole iteration-2 compile-gate defect by placing the protected model
  checksum in a column-width box, preventing its unbreakable hexadecimal text
  from overflowing the column. The harness-side compile verdict remains pending.

## Lap 5 (2026-07-12)

- Removed the underpowered-null overclaim identified by the adversarial review.
  The title now centers the supported position and pruning results; the abstract,
  amount result, and limitations state that the sparse matched amount comparison
  cannot establish either benefit or degradation.

## Lap 6 (2026-07-12)

- Replaced probe-level Wilson intervals with deterministic percentile bootstrap
  intervals that resample whole scenario families. Added family counts and
  family-cluster intervals for every paired change, regenerated the result
  registry and LaTeX macros, and reported the core paired intervals in the paper.

## Lap 7 (2026-07-12)

- Corrected the NoLiMa bibliography entry to match the cached exemplar and full
  text: Ryan A. Rossi and Seunghyun Yoon replace the two inaccurate author names.

## Lap 8 (2026-07-12)

- Added the ICML template's required anonymous corresponding-author declaration,
  removing the visible missing-corresponding-author error from the affiliation block.

## Lap 9 (2026-07-12)

- Corrected the position-control description after checking the rendered clause
  indices. The paper now states that the competing clause keeps a fixed insertion
  index but shifts by one sentence when the answer is inserted before it.
