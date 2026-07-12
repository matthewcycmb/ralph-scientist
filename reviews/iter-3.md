## 1. Summary

The paper reports a deterministic, reproducible evaluation of Qwen2.5-0.5B-Instruct on synthetic contract-clause retrieval. It varies prompt length, answer-clause position, filler type, and keyword pruning. The strongest observed pattern is recency: end-position clauses substantially outperform start and middle positions. Relevant filler and keyword pruning reduce accuracy, apparently because both introduce or favor code-bearing text with high lexical overlap. The length experiment finds no observed decline through 7,992 tokens, but its longest-tier comparison contains only two scenario families and cannot establish absence of degradation.

## 2. Strengths

- Strong provenance: the model artifact is named and checksummed, all 120 outputs are present, and paper values are generated from `results.json`.
- Position, amount, quality, and pruning contrasts use explicit matched keys rather than subtracting unrelated aggregates.
- The paper reports denominators, Wilson intervals, and paired wins/losses/ties.
- Limitations correctly identify the single quantized model, synthetic task, restricted CPU budget, retrieval-only outcome, and greedy decoding.
- The three-page main body includes all required sections and three tables.
- The introduction is accessible, restrained, and clear that no natural contracts were tested.
- The negative pruning result is useful and is tied to a plausible, inspectable failure mechanism.

## 3. Weaknesses

- The principal framing converts low power into a negative finding. The title claims that context amount did not hurt, whereas the abstract and Results concede that the amount comparison is inconclusive. Twelve observations at the longest tier represent only two scenario families crossed with filler and position. This is failure to detect degradation, not evidence that degradation did not occur. The abstract’s claim that placement mattered more than amount is likewise unsupported because those effects were estimated with very different power.

- The quality manipulation does not isolate topicality. Every relevant-filler template introduces business entities and code-shaped candidates, while irrelevant filler contains no codes. Thus code density, candidate-set size, semantic domain, and topicality all change together. The reported harm cannot specifically be attributed to relevant context.

- The uncertainty analysis treats correlated probes as independent Bernoulli observations. For example, the amount denominator of 12 derives from only two families, while position and quality denominators repeatedly reuse six or fewer families. Wilson intervals at the probe level therefore overstate the effective sample size. The paper does not define a population of scenarios, justify fixed-seed families as a sample from it, or provide family-clustered uncertainty. Paired changes receive no intervals or paired tests.

- The mitigation evidence is too narrow for a meaningful retriever conclusion. The sole filter is structurally predisposed to retain the lexical decoy and discard the paraphrased answer. There is no oracle filter, random pruning control, code-density-matched filter, BM25-style baseline, or ablation showing whether pruning fails because of lexical selection rather than simply removing the answer.

- The practical implication remains weak. Moving a known answer clause to the end presupposes knowing which clause answers the question; that is not generally available in retrieval or document-QA settings. The paper distinguishes itself from prior work through matched filler quality and laptop reproducibility, but does not turn that distinction into a credible deployment recommendation.

- The claimed position control is not literally exact. `assemble()` reinserts both clauses by sorted indices, so moving the answer across the distractor can shift the distractor’s final sentence index by one. This is unlikely to explain the large effect, but contradicts the statement that only the answer clause changes position.

- Bibliographic verification is incomplete. NoLiMa resolves as a real title, but `refs.bib` lists Ryan A. Kim and Tong Zhao, whereas the cached exemplar metadata lists Ryan A. Rossi and Seunghyun Yoon. Title-only resolution did not catch inaccurate author metadata.

- PDF audit: the running title is present on pages 2–4, so it is not suppressed. No table visibly crosses a column boundary, but all three are aggressively scaled and crowded; Table 1 is particularly small. More seriously, page 1 visibly prints `AUTHORERR: Missing \icmlcorrespondingauthor` in the affiliation block. The main body occupies three pages and references occupy page 4.

- Language audit: the prose is readable but not fully polished. The title phrase “More Context Did Not Hurt” overstates an underpowered null result. “lowered matched accuracy by -33.3 points” combines a directional verb with a negative quantity and is editorially inconsistent; standardize directional reporting. “support this explanation without proving it for other tasks” is a defensive caveat placed before the concrete diagnostic result; move secondary scope qualifications to Limitations. Results paragraphs also repeat the same bold-claim/effect-size/caveat frame, giving them a mechanically templated cadence. I found no casual “made-up” wording, unnecessary definitions of ordinary terms, or excessive reuse of the contract example.

## 4. Criticism ledger (machine-readable)

LEDGER: new | underpowered-null-overclaim | title treats failure to detect length degradation as evidence of no harm  
LEDGER: new | quality-code-density-confound | filler quality is confounded with code density and candidate count  
LEDGER: new | clustered-probes-ignored | Wilson intervals treat repeated scenario-family probes as independent  
LEDGER: new | paired-uncertainty-missing | paired effect changes lack uncertainty intervals or paired tests  
LEDGER: new | weak-pruning-baselines | mitigation uses only one filter predisposed to select the decoy  
LEDGER: new | weak-practical-implication | end placement assumes prior knowledge of the answer-bearing clause  
LEDGER: new | distractor-position-shift | clause insertion can shift the distractor despite the claimed fixed position  
LEDGER: new | inaccurate-bib-authors | NoLiMa author metadata conflicts with the cached exemplar  
LEDGER: new | pdf-author-error | compiled first page exposes a missing-corresponding-author error  
LEDGER: new | crowded-tables | scaled tables are technically contained but uncomfortably small  
LEDGER: new | language-polish | negative-direction phrasing and templated result frames remain unpolished  

## 5. Spot checks

### Citations

- Liu et al., *Lost in the Middle*: real and resolved in `data/cache/citations/23391...json` through Crossref, DOI `10.1162/tacl_a_00638`. The cited sentence about a U-shaped position curve in multi-document QA and key-value retrieval is supported by the cached abstract and full text.

- Levy et al., *Same Task, More Tokens*: real and resolved in `data/cache/citations/90d356...json`, DOI `10.18653/v1/2024.acl-long.818`. The sentence stating that matched problems were padded and degraded before the technical context limit is supported by the cached abstract and methods.

- Modarressi et al., *NoLiMa*: real and resolved in `data/cache/citations/3a6879...json` through Semantic Scholar. Its content supports the claim that literal lexical matches can make needle retrieval artificially easy. However, the paper’s BibTeX author list conflicts with the cached exemplar metadata.

### Numbers

- **120 probes:** `data/probes/manifest.json` records 120/120 completed probes. `run_probes.py` generates and executes the grid; `run_all.py:88–94` reads each raw output, and `run_all.py:146` stores `len(scored)` as `sampleSize`. `results.json` contains `sampleSize = 120`, which `make_values.py` emits as `\sampleSize`. Chain complete.

- **58.3-point shortest-tier start-to-end gain:** raw scoring gives 2/12 correct at the start and 9/12 at the end. `run_all.py:172–177` invokes the paired comparison, and `run_all.py:129–144` computes \(75.0-16.7=58.3\) points. `results.json` stores `positionTwoStartEndChange = 58.333...`; the generated macro rounds it to 58.3. Chain complete.

- **−33.3-point pruning change:** the matched middle-tier cells contain 12/30 correct full-context outputs and 2/30 correct pruned outputs. `run_probes.py:344–353` constructs the pruned variants; `run_all.py:206–220` intersects matched keys and computes \(6.7-40.0=-33.3\) points. `results.json` stores `pruningChange = -33.333...`. Chain complete.

## 6. Questions for the authors

1. What population supports your confidence intervals, and how would the conclusions change under family-clustered inference where the longest tier contains only two independent scenario families?

2. How can you attribute the quality result to topical relevance when relevant filler contains many code-shaped candidates and irrelevant filler contains none?

3. Given the inconclusive amount experiment, what evidence justifies the title and the cross-axis claim that placement mattered more than amount?

## 7. Scores

### Official ICML-style competition scores

- **Soundness: 2/4.** Provenance and pairing are strong, but the quality axis is confounded, dependence is ignored in uncertainty estimates, and the null length result is overclaimed.
- **Presentation: 2/4.** Generally readable and well organized, but the compiled author error, tiny tables, negative-direction phrasing, and templated Results prose require correction.
- **Significance: 1/4.** One very small model, six seeded families, synthetic adversarial probes, and no directly actionable mitigation substantially limit impact.
- **Originality: 2/4.** Matched filler quality and laptop-scale reproducibility offer a modest distinction, but the position and length questions closely follow established work.
- **Overall: 2/6.** Reject. Core empirical artifacts are verifiable, but revision is insufficient without redesigning the quality comparison, expanding independent families, and correcting the central framing.
- **Confidence: 5/5.** Source, compiled PDF, raw manifest, aggregation scripts, result registry, citation caches, and cached paper content were available.

### Rubric score

**5/10.** The paper satisfies most structural and provenance requirements: three main-body pages, required sections, three tables, measured denominators, explicit limitations, and a reproducible chain from raw outputs to macros. It loses substantial credit for overclaiming the underpowered amount result, the code-density confound in the purported quality axis, inappropriate probe-level uncertainty, weak mitigation baselines, limited practical significance, inaccurate citation metadata, and a visible PDF submission error.

{"overall":2,"rubric":5,"soundness":2,"presentation":2,"significance":1,"originality":2,"confidence":5,"recommendation":"reject"}