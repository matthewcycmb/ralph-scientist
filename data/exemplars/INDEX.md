# Exemplar & related-work library (frozen at prep time; agents read, never fetch)

12 papers: 5 with full text, 1 with abstracts.
Each <slug>.json = metadata + abstract; <slug>.txt = full text when open-access.
STYLE MODEL entries anchor tone/structure; the rest seed Related Work.

- **french2015-gpa-earnings** — UNRESOLVED (?) · closest prior work: GPA -> earnings (NLSY97)
- **zagorsky2007-iq-wealth** — UNRESOLVED (?) · wealth as outcome on NLSY79
- **chetty2014-mobility** — UNRESOLVED (?) · intergenerational mobility framing
- **borghans2016-grades-measure** — UNRESOLVED (?) · what GPA actually measures (PNAS)
- **heckman2006-noncognitive** — UNRESOLVED (?) · cognitive vs noncognitive skills -> outcomes
- **charles2003-wealth-generations** — UNRESOLVED (?) · parent-child wealth correlation (JPE)
- **killewald2017-wealth-inequality** — UNRESOLVED (?) · wealth accumulation review (Annu Rev Sociol)
- **pfeffer2018-wealth-mobility** — UNRESOLVED (?) · multigenerational wealth transmission
- **murnane1995-cognitive-skills** — UNRESOLVED (?) · test scores -> wages over time
- **kuncel2005-gpa-validity** — UNRESOLVED (?) · GPA as a measurement instrument (meta-analysis)
- **schaeffer2023-emergent-mirage** — UNRESOLVED (?) · STYLE MODEL: skeptical empirical paper, question->data->simple analysis->honest limits
- **dodge2019-showyourwork** — Show Your Work: Improved Reporting of Experimental Results (2019) · STYLE MODEL: reporting/verification norms in ML

## Context-degradation wing (PRIMARY topic, added 2026-07-04)

- **liu2023-lost-in-the-middle** — Lost in the Middle: How Language Models Use Long Contexts (2023) · CORE PRIOR WORK: big models use long-context info unevenly (U-shaped by position)
- **levy2024-same-task-more-tokens** — Same Task, More Tokens: the Impact of Input Length on the Reasoning Performance of Large Language Models (2024) · input length alone degrades reasoning, holding the task fixed
- **hsieh2024-ruler** — RULER: What's the Real Context Size of Your Long-Context Language Models? (2024) · real usable context is shorter than the advertised window
- **shi2023-distracted-irrelevant** — Large Language Models Can Be Easily Distracted by Irrelevant Context (2023) · irrelevant context hurts even when the model is told to ignore it (ICML) — our context-QUALITY axis
- **modarressi2025-nolima** — NoLiMa: Long-Context Evaluation Beyond Literal Matching (2025) · needle tests beyond literal keyword matching — hard-probe design
- **qwen2024-qwen25-report** — Qwen2.5 Technical Report (2024) · technical report for the model family under test
