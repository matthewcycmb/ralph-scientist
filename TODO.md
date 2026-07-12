# TODO

Laps 1-2 complete the full probe grid and cheap scoring pipeline. See DONE.md.
Highest leverage next:

- [ ] Draft paper/main.tex from paper/OUTLINE.md (NEXT). Name the exact GGUF and checksum.
  Lead with the paired end-position recency effect and the matched pruning backfire.
  Amount is inconclusive: among the 12 scenarios shared across all tiers, accuracy rises
  8.3 points from 2k to 4k and is flat from 4k to 8k. Do not use the confounded full-tier
  33.3/40.0/58.3 pattern as an amount effect.
- [ ] Report the matched quality result: relevant filler is 22.2 points worse at 2k and
  13.3 points worse at 4k. Treat 8k quality cells as sparse (six probes per filler type).
- [ ] Explain why keyword pruning backfires: it keeps the literal-form distractor while
  the answer-bearing clause is paraphrased. Matched accuracy falls 33.3 points over 30
  pairs (one win, eleven losses, eighteen ties).
- [ ] Anonymous ICML submission: 2-4 page body, >=2 tables/figures, four questions
  answered by number, required limitations (state the 45-min CPU budget), Reproducibility
  paragraph, \label{main-body-end} before references.
- [ ] Related Work from data/exemplars/ full texts only; citations must resolve via the
  harness gate (cache: data/cache/citations/).
- [ ] First full eight-gate pass + rubric >= 6 tags paper-v1.
- [ ] GATE FAIL (prose-style, iter 1): FAIL: abstract has 1 sentences; use 4-7 for question, design, principal estimate, qualification, and takeaway FAIL: paper has 0 result displays; a 2-4 page paper should use 2-4 selective displays 2 style failure(s) in paper/main.tex 
- [ ] GATE FAIL (submission-ready, iter 1): FAIL: abstract is not submission-ready (5 words; require at least 50) 
- [ ] GATE FAIL (latex-compiles, iter 1): FAIL: compiled paper must contain at least 2 pages, got 1 
