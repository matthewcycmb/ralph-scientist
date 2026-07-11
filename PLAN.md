# Ralphthon @ICML "Auto Research" — Prep Plan

Event: Sunday **July 12, 2026**, 9:30 AM–8:00 PM KST, NAVER D2SF Gangnam, Seoul.
Track 1 (AI Scientist): build an agent that autonomously produces a paper-style research artifact.
Papers are reviewed by Track 2 teams' Review Agents **in ICML review format**; judges look at papers, reviews, and the agent workflows behind them.

## Confirmed event facts (from Luma, 2026-07-01)

- 5th Ralphthon edition (SF → Singapore → Busan → Seoul @ICML). Presented partner: OpenAI Codex.
- Prizes: Grand $10k API credits + 6mo ChatGPT Pro; each track $5k + 6mo Pro.
- Ralph rule: once the loop starts you cannot touch the coding agent (lobster costume to touch laptop).
- RSVP is **"Request to Join"** (approval) and the page says: *"You will be asked to verify token ownership with your wallet."* → crypto wallet apparently required.
- No age restriction stated anywhere.
- Judges (expanded list, seen 2026-07-06 — 7 reviewers now): Younghoon Kim (Planar,
  ex-OpenAI Trust & Safety), Kyoung Whan Choe PhD (RLWRLD, robotics/cog-neuro),
  Mathew Vanherreweghe (Logical Intelligence, MTS), Jae Gon Kim (Xenoscube, lead MTS),
  Sigrid Jin (founder, instruct.kr — Korean LLM open-source community), Jungyoon Lim
  (Math Inc, founding engineer — formal-math/verification space), Daniel Nam (Kakao
  Brain, researcher). Read: panel skews technical + verification-minded; at least one
  judge will know the long-context literature cold. Implications: (1) the can't-fake-
  numbers / deterministic re-run story is aimed at this room's center of mass; (2) have
  the one-breath answer to "how is this different from Lost in the Middle?" — quality
  axis, mitigation head-to-head, laptop-scale determinism, and the position inversion
  if it survives; (3) SKILL.md artifact + runs-on-anyone's-laptop angle lands with the
  community-builder judge; (4) 7 judges = less time per team — the 60-second legibility
  bar and the dashboard matter more than ever.
- The guide at ralphthon.team-attention.com/guide is still the **Busan edition** — Seoul guide not published as of 2026-07-01. Re-check weekly.
- Host's LinkedIn post (2026-07, in Korean): OpenAI support totals **$20,000 credits + 6mo ChatGPT Pro**; framing: can AI agents handle the research loop — "see problems differently, design experiments differently," "good research is hard to replicate." Post loosely implies Track 1 ideas may lean ICML/ML-related — **not stated as a rule anywhere**; our topic knowingly trades theme fit for story + verifiability (defense drafted in FLOWCHART Q&A). Confirm domain freedom in the event Discord if wanted.
- Language: no official statement. Evidence points bilingual with English fully workable: Luma page is English-first bilingual, guide pages are English, Discord channels are English-named, prior editions were SF/Singapore, it's ICML week with international attendees, and judges publish/work in English. Post itself was Korean (local audience).
- Likely carryover from Busan guide: 3-min live demo; scorecard = Live Demo 0–4 + Creativity 0–3 + Impact 0–3; max team 4 (solo OK); public repo required; "new work only, judges will check."
- **FORMAT CHANGE (host post, 2026-07-03): conference-review process replaces stage judging.**
  Track 1 papers due **5 PM** (not 8 PM); Track 2 review agents due "5 AM" (likely typo —
  verify). Then: 30-min peer review (Track 1 participants review each other; Track 2 AI
  agents review Track 1 papers) → AC (judge) review of papers + reviews → SAC final pass.
  "Reviewer" not "judge"; review quality itself is evaluated. Busan scorecard likely
  superseded; live demo unconfirmed — asked in Matthew's email (also asked: English OK,
  pre-built harness ruling, topic freedom, API credits, submission format). Implications
  shipped: SPEC reproducibility-note requirement; RUNBOOK peer-review half-hour routine;
  Matthew drills 5-min-per-paper reviewing in dress rehearsal.

## Event format update (host post, seen 2026-07-10)

- **Papers are 2–4 pages** (was assumed 4–8) — SPEC, reviewer, and seed updated.
- After submission: self-review + peer review (reviewers examine papers AND review
  agents) → **poster session** → **oral presentation**. Prep: the FLOWCHART one-pager
  prints as poster material; the crib page's judge answers are the oral's skeleton.
- Host's own framing of the bar: "a sense of choosing problems, a skeptical attitude
  toward experimentation, persistence in enduring reviews... how far an agent can
  handle the loop of organizing ideas, creating experiments, writing results in paper
  form, receiving reviews, and revising." That is a description of this machine —
  quote it back in the oral.

## Decision log (grill session, 2026-07-01)

1. **Artifact type: experiments-first.** Every number/table/figure is the output of code committed in the repo. Literature is only for related-work framing.
2. **Domain: ML meta-science.** Public, keyless data about the ML research ecosystem (OpenReview, arXiv metadata, Papers With Code, Semantic Scholar).
3. **Loop: authentic Ralph outer loop + hard gates.** Fresh `codex exec` each iteration with the same PROMPT.md; memory lives in SPEC.md / TODO.md / git. Verification is deterministic and lives OUTSIDE the agent (harness scripts); failures are auto-appended to TODO.md. A separate adversarial-reviewer Codex call (full ICML review form, harness/REVIEWER.md) fires every 3rd iteration once a draft exists.
4. **Number gate: build-time injection.** Analysis scripts write `results.json` → generator emits `paper/values.tex` (`\newcommand` macros) → prose uses macros only. Gate greps the .tex for raw numeric literals. Final gate: clean-room re-run regenerates results.json and the PDF.
5. **Stop condition: ratchet, never stop.** First full pass → git tag `paper-v1`. Loop continues improving; harness advances the tag only if all gates pass AND reviewer score ≥ previous tag. Submit highest tag at event end.
6. **Format: ICML LaTeX → PDF.** Real ICML template; `latexmk` compile is a gate; compile errors feed back into TODO.md verbatim.
7. **Prep stance: bring the harness pre-built** (user decision; interprets SPEC/harness as inputs to the agent, the paper as the event work). Hedge: ask the host for a ruling in the logistics email — a "no" before the event is recoverable, on the day it isn't.

## Topic (RE-LOCKED 2026-07-04 — pivot to ML-topical; feasibility spike passed)

**"Does more context degrade model performance? If so, when does it start, and by how much?"** — how the amount, position, and quality of
context change a small LM's retrieval accuracy, measured deterministically on the event
laptop (Qwen2.5-0.5B-Instruct Q8 via llama.cpp, frozen + checksummed in data/models/).
RQ1 amount (~2k→8k), RQ2 position (lost-in-the-middle at small scale), RQ3 quality
(relevant-redundant vs irrelevant filler — the novel axis), RQ4 cheap mitigations.
Full spec in SPEC.md. Why the pivot: organizers signal the paper must be ML-related;
Matthew's brain dump (2026-07-04) converged here — it keeps the you-test ("I felt this
building with AI"), the demo story gets STRONGER (the experiment re-runs live,
byte-identical, no network), and the spike measured the budget (~6/16/28s per probe at
2k/4k/8k → ~200-probe grid, 45-min clean-room re-run). Fallback #1: the NLSY97
grades→net-worth paper (fully prepped, three rehearsal papers produced, battle-tested).

Topic history: LLM-fingerprints/ICLR ratified then retired same day (failed the
"Matthew can explain it" test); NLSY97 grades→net-worth locked 2026-07-01, demoted to
fallback 2026-07-04 (not ML-topical); Wikipedia attention decay retired as fallback
(needs live network; the pivot topic runs fully offline).

### Pilot grid findings (2026-07-04, 57 probes, 13.9 min inference — topic is GO)

Grid: {2k,4k,8k} tokens × {start,mid,end} needle × {literal,paraphrase} × 3 reps,
plus a quality mini-cell; every haystack carried 3 literal-form near-match distractors.

- **Literal probes saturate** (26/27 correct): too easy alone, keep as a small control.
- **Paraphrase probes carry the paper** (5/27): the model falls back to literal keyword
  matching — ALL 24 errors were distractor picks, zero garbage answers. NoLiMa's
  headline reproduces on a 0.5B laptop model. Distractor-capture rate is a first-class
  metric (it is the mechanism, not just an error).
- **Possible novel wrinkle:** paraphrase accuracy was better mid-context than at the
  edges (inverted vs Liu et al.'s U-shape) — but the pilot confounded distractor
  placement with needle position; the real grid must place distractors independently
  before believing this.
- **Quality axis has signal** at n=3 (relevant filler 2/3 vs irrelevant 1/3) — direction
  TBD, needs ~20 probes/cell.
- **Budget confirmed:** 6.9/11.8/25.7 s per probe at 2k/4k/8k → ~180 mixed-length probes
  fit the 45-min clean-room re-run. SPEC's ~200-probe estimate stands.
- **Determinism trap found:** Python `hash()` is salted per process — seeding generators
  with it makes `make clean-deep && make all` non-reproducible. SPEC now forbids it.
- Difficulty needs a middle tier (soft paraphrase keeping one keyword) so cells sit off
  the floor and the length gradient is visible.

Pilot code in session scratchpad (not committed — same precedent as the 07-04
determinism spike; findings live here and in SPEC's constraints).

## Open items (blocking, do first)

1. ~~Email host / RSVP~~ — **Matthew registered 2026-07-01. Done.**
2. ~~Pull the NLSY97 extract~~ — **DONE 2026-07-02.** No account needed (Investigator
   guest mode worked end-to-end). 71 variables × 8,984 respondents, NLSY97 rounds 1-21
   (Jan 2026 release), frozen + checksummed in data/cache/nlsy97/ with tagset for exact
   reproduction. All key variables verified present. Next: build gates + analysis scaffold.

## Prep timeline (11 days)

- **Jul 1–3:** Harness v0 + data. Solve Codex CLI network/sandbox config for unattended runs (#1 practical unknown). Write the two gate scripts + Makefile + ICML template scaffold. Pull and freeze the NLSY97 extract; verify Crossref/Semantic Scholar citation APIs live; verify + cache exemplar papers (French et al. 2015 GPA→earnings; Zagorsky 2007 IQ→wealth on NLSY79 — confirm both exist).
- **Jul 4–6:** Practice run #1 (small budget) on the real frozen NLSY97 data. Goals: loop survives 2 hours unattended; gates catch a planted fake citation and a planted hand-typed number; reviewer calibration (must reject a sabotaged paper, accept a good exemplar).
- **Jul 7–9:** Dress rehearsal on the primary topic, ~$10–20 Codex budget. Measure: iterations/hour, cost/iteration, time-to-first-tag. Tune reviewer cadence and PROMPT.md from what actually goes wrong.
  - **A/B experiment (Matthew's hypothesis, 2026-07-02):** same-agent continuation
    (`codex exec resume`) vs fresh agents — 6 laps each arm, compare rubric movement,
    criticism-resolution rate, and token cost. Switch architectures if resume wins.
  - Post-run fix list from the v2 shakedown: ratchet must remember which review it
    cashed (one tag per fresh review); archive reviews/logs/drafts per-run at loop
    start; add EDITOR.md + dashboard to the tamper-guard fingerprint.
- **Jul 10–11:** Freeze harness. Write 3-min demo script. Crib sheet (gate list, repo layout, recovery moves) in case anything must be re-authored on-site. Re-check the guide URL for the Seoul edition rules.
- **Jul 12:** Arrive early, set SPEC topic final, start loop at gun, don't touch laptop.

## Demo plan (3 minutes, working screen > slides)

1. (0:30) The claim: "This agent wrote a real paper — every citation resolves, every number is compiled from experiments it ran."
2. (1:00) The loop, live: terminal with iterations scrolling; VERIFY.log gates flipping red→green; `git tag` ratchet history as the story of the run.
3. (1:00) The artifact: ICML-format PDF, one headline figure, the results.json → values.tex → PDF chain.
4. (0:30) The kill shot: clean-clone re-run reproducing a headline number in front of the judges.

## Risk register

Meta-insight behind the architectural risks: **the gates verify provenance, not truth or
quality** — everything they can't see is a place to fail.

### Architectural (severity-ordered)

| # | Risk | What happens | Fix |
|---|------|-------------|-----|
| A | Reward hacking | Agent edits a gate script to always pass instead of fixing the paper | Loop verifies sha256 of harness/ files each lap, auto-reverts via git (pinned in loop.sh). Practice test: order a test agent to cheat, confirm it's caught |
| B | Hollow paper (Goodhart) | Easiest way to pass "no fake numbers" is few numbers — vague gate-green mush | Substance gates: min figures, min result-macros used, all RQs answered. Reviewer told: hollow = reject |
| C | Reproducible ≠ correct | Buggy analysis → wrong number; clean re-run reproduces the same wrong number | Keep analyses simple (counting > modeling); sanity gates (% in 0–100, n above floor, dates in range, n reported); reviewer reads the headline-result code |
| D | Reviewer goes soft | LLM reviewer gives 7/10 to everything; ratchet becomes meaningless | Calibration test (Jul 4–6): one sabotaged paper + one good exemplar; harden prompt until it separates them |
| E | Wedged/thrashing loop | Hung codex call freezes loop; or agents oscillate on the same fix | 15-min timeout per agent call (done); repeat-failure escalation (pinned); watchdog: no tag in 2h → "simplify scope" directive |
| F | Nothing tagged by 8 PM | Reviewer threshold never met → zero paper-vN tags | Shadow tags: every all-gates-green commit tagged green-vN regardless of score (pinned in loop.sh) |
| G | External world fails | Data API rate-limits/down mid-event; wifi blip; laptop sleeps | Download data as task #1, cache-first, retry+backoff; tmux + caffeinate; fallback topic uses a DIFFERENT data source |
| H | Logbook corruption | Agent mangles TODO.md, factory loses its memory | Git commit every lap = nothing lost; tiny gate: TODO.md exists and is sane |

### Logistics

- **Wallet/age/RSVP** — unresolved; email to bong@ is the mitigation. Highest severity overall.
- **Codex sandbox networking** — gates and data downloads need network in unattended mode; must be solved in practice week, not on the day.
- **Credit burn** — fresh context per iteration keeps prompts small; measure cost/iteration in rehearsal and set an iteration budget.
- **LaTeX stall** — compile-error gate pipes errors verbatim into TODO.md; rehearsal shows if Codex self-recovers.
- **Busan "NOT TO DO" list carryover** (basic RAG, Streamlit, analyzers...) — our entry is none of these, but re-check the Seoul guide when it publishes.
