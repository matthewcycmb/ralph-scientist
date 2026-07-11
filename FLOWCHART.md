## ⎙ · The one-page flowchart (print this one)
```
                 RALPH SCIENTIST — HOW THE WHOLE THING WORKS

We built an agent that designs context experiments, runs them on a
> frozen local model, tracks every result, critiques its own paper, and
> iterates until the paper survives adversarial review — with no human
> touching the laptop.

 ┌───────────────────────── BEFORE · the human ──────────────────────────┐
 │  Matthew writes SPEC.md (the rules + the research question) and      │
 │  saves a locked copy of the AI model + reference papers in advance,   │
 │  so nothing can change or be swapped mid-run. Starts the loop.        │
 │  After that: no touching the laptop.                                  │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     ▼
 ┌────────────────────────────── THE LOOP ───────────────────────────────┐
 │                                                                       │
 │  1 · NEW AGENT      starts with zero memory. Reads the rules          │
 │                     (SPEC.md), the to-do list (TODO.md), and the      │
 │                     latest check results (VERIFY.log).                │
 │                                   ▼                                   │
 │  2 · ONE TASK       picks the single most useful task and does it.    │
 │       most laps:    write or fix one section of the paper, or         │
 │                     improve the analysis and update the numbers       │
 │       rarely:       the experiment design changed → re-run the model  │
 │                     on the full quiz grid (the slow, expensive step)  │
 │                     (watchdog: 10 minutes of silence = lap killed)    │
 │                                   ▼                                   │
 │  3 · TAMPER CHECK   if the agent edited the rules or the checkers,    │
 │                     the edit is reverted and logged.                  │
 │                                   ▼                                   │
 │  4 · SEVEN CHECKS   simple scripts. Every lap. Cannot be skipped.     │
 │       · frozen model and fallback data still match their checksums     │
 │       · every cited paper really exists (checked in paper databases)  │
 │       · no number typed by hand — numbers only come from the code     │
 │       · re-running the scoring gives the exact same results.json      │
 │         (proves no number was edited by hand or gone stale)           │
 │       · results make basic sense (percentages 0-100, enough           │
 │         quizzes behind every number)                                  │
 │       · no em dashes or banned filler words in the paper              │
 │       · the paper compiles into a PDF                                 │
 │       any FAIL is written into TODO.md → a later lap must fix it      │
 │                                   ▼                                   │
 │  5 · EVERY 3RD LAP                                                    │
 │       REVIEWER    reads the paper like a harsh conference reviewer.   │
 │                   Scores it /10. Keeps a list of every complaint:     │
 │                   new / still open / fixed.                           │
 │       EDITOR      looks at the actual numbers and decides what the    │
 │                   paper's main point should be. Reorders TODO.md.     │
 │       HUMANIZER   rewrites hard-to-read sentences in plain language.  │
 │                   Not allowed to change numbers or claims.            │
 │                                   ▼                                   │
 │  6 · VERSION TAG   commit the checked state; all seven checks pass    │
 │                    AND review held/rose → tag that exact commit.       │
 │                    Every all-green lap also gets a backup tag, so     │
 │                    there is always a finished version to submit.      │
 │                                   ▼                                   │
 │  7 · FOLLOW-UP     editor/humanizer changes wait for next lap's gates.│
 │                                   │                                   │
 │                                   └────► next new agent (back to 1)   │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     ▼
 ┌───────────────────────────── 5 PM · submit ───────────────────────────┐
 │  Submit the best tagged version. Anyone can then delete every result  │
 │  and re-run everything — the same numbers come back, exactly.         │
 └────────────────────────────────────────────────────────────────────────┘
```

---

## ☑ · Event day: everything to remember (print this too)

```
 THE NIGHT BEFORE (Jul 11)
   · harness is FROZEN — change nothing but your sleep schedule
   · charge the laptop; check codex login works (codex --version)
   · print this page and the flowchart page

 THE REAL CLOCK (Seoul schedule, confirmed 07-11)
   10:00  opening + sponsor talks (Codex, W&B, VESSL)
   11:00  "research specification" block: push the repo, confirm the
          event credits landed, re-read SPEC once. Ask two questions:
          may the loop run into the editing hour? oral: slides allowed?
   12:30  THE GUN — the loop gets exactly 3 hours
   15:30  "human editing" hour: TOUCH NOTHING. Other teams hand-patch;
          your exhibit is the unedited tag + clean git history
   16:30  submission snapshot -> 16:35 review agents -> 17:00 judging
   17:30  poster session (printed sheet + live dashboard on laptop)
   19:00  orals: winners only — deck is ready if called

 THE MORNING (before the gun)
   1. harness/reset_for_event.sh        -> builds the clean event-day branch
   2. create the public GitHub repo, push the branch
   3. tmux new -s ralph                  (survives a closed window)
   4. caffeinate -is env PUSH=1 harness/loop.sh    <- the gun, 12:30
      (3-hour window: the first lap builds + runs the experiment,
       ~1 hour; expect ~8-12 fast laps after; first tag ~lap 6)
   5. open the dashboard: http://127.0.0.1:8788/harness/dashboard/
   5b. after the W&B talk (optional, sponsor-friendly): grab a W&B key,
       export WANDB_API_KEY=<key>
       python3 harness/dashboard/wandb_mirror.py &
       -> your dashboard's numbers stream to W&B live; loop unaffected
   6. hands off. For the rest of the day you are a spectator with a title.

 WHAT IS NORMAL (do not panic, do not touch)
   · first lap is SLOW (~1 hour): it builds the experiment and runs the
     model on the whole quiz set once. Later laps are minutes.
   · a red check now and then — it gets written down and fixed next lap
   · a quota nap: the loop sleeps ~10 min and retries. Costs ~30-60 min
     once a day. It recovers by itself.
   · killed lap after 10 silent minutes — the watchdog working
   · laptop dies? clone the pushed repo on any machine, remake the venv,
     restart the loop. Nothing is ever lost; git has every lap.

 NUMBERS TO KNOW COLD
   · one quiz costs ~14s / ~25s / ~76s at small / medium / large size
   · the whole experiment re-runs from nothing in under 45 minutes
   · rehearsal findings: WHERE the answer sits beats HOW MUCH text there
     is (start ~100%, end ~19% at small scale; length alone 2k->8k barely
     moved accuracy). Every single failure = the model confidently
     quoting a look-alike decoy. With no document at all: 0% — proof the
     answers come from reading, not memory.
   · three papers already tagged in rehearsal (v11, v12, v13, all
     scored 6+ twice, independently)

 IF A JUDGE ASKS
   "Isn't this just Lost in the Middle?"  — That was big API models. We
     test a model anyone can run at home, add the question nobody
     isolated (does GOOD extra text hurt less than junk?), race the
     fixes head-to-head, and every number re-runs in front of you.
   "Why such a small model?"              — Because it makes the paper
     checkable. Delete the results, type make all, watch identical
     numbers come back. No API paper can do that.
   "Your own reviewer scores it 3/10?"    — That's the novelty score;
     our reviewer grades like a real conference. The quality bar it
     enforces (6+, confirmed twice) is what tags a version.
   "Did you write any of this?"           — I wrote the rulebook before
     the event. Every experiment, number, and sentence after the gun is
     the machine's. The git history is the alibi.
   "Why not the partner GPUs (VESSL)?"    — Cloud GPUs would weaken my
     proof: different hardware can give different numbers. My whole
     paper re-runs byte-identical, offline, on this laptop. Determinism
     IS the contribution.
   "Are you using W&B?"                   — Yes, as the live window: my
     dashboard mirrors to W&B in real time. But the numbers are BORN in
     git, where they can't be edited, only re-run. W&B shows you the
     run; the git history proves it.

 5 PM
   · submit the highest paper-vN tag (there is ALWAYS one — every clean
     lap also makes a backup tag)
   · then the peer-review half hour: 5 minutes per paper — find the
     claim, find the evidence, check one number, write two honest
     sentences. You have drilled this.
   · then the POSTER SESSION: your printed flowchart page IS the poster
     story — walk people down the seven steps, dashboard on the laptop
   · then the ORAL: the judge answers above are your script; end on the
     kill shot (delete results, make all, same numbers return)
   · paper is 2-4 PAGES — short is the format, the machine knows

 NEVER
   · never touch the laptop while the loop runs (lobster costume rule)
   · never run the reset script twice — it is for the morning, once
   · never push all git tags — practice tags stay home
```

---

## ★ · The visible research loop (the theme, on one screen)

> **We built an agent that designs context experiments, runs them on a
> frozen local model, tracks every result, critiques its own paper, and
> iterates until the paper survives adversarial review — with no human
> touching the laptop.**

The theme is AUTO RESEARCH. The judges' bar is not "did an agent write a
paper at the end" — it is "can I SEE the agent doing research": making a
decision, testing it, reading the result, changing course. Our machine
does not just contain this loop; it leaves physical evidence of every
turn of it.

```
  idea ──► experiment ──► result tracking ──► analysis ──► next idea ─┐
    ▲                                                                 │
    └────────────── the loop turns all day, every lap ◄───────────────┘
                                  │
                                  ▼  best tagged version at 5 PM
                             final paper
```

Where each stage is VISIBLE, on disk, in public git history:

1. **Idea** — The research questions live in SPEC.md, and the editor keeps a
   running thesis in EDITORIAL.md. Once the paper reaches version 2, the agent
   is allowed to propose and test a hypothesis of its own.
2. **Experiment** — `make probes` runs the quiz grid against the frozen model.
   Everything is seeded and deterministic, so anyone can re-run it and get the
   identical numbers.
3. **Result tracking** — Every lap ends in a git commit, every number lands in
   results.json, and the live dashboard shows it all in real time. Nothing can
   be edited after the fact, only re-run.
4. **Analysis** — `make results` scores every answer, and every third lap a
   skeptical reviewer attacks the paper in full ICML review format.
5. **Next idea** — The reviewer's complaints go into a ledger (new / still
   open / fixed) and the editor rewrites the to-do list around them. Each lap
   starts from what just failed, not from a script.
6. **Final paper** — A version only gets tagged if it passes every check AND
   holds or raises the review score; we submit the best tag at 5 PM. The
   reviews plus DONE.md double as the "reviewer response": what worked, what
   failed, what to test next.

> **Say:** "The theme is a research loop, so let me show you the loop
> itself: idea, experiment, tracking, analysis, next idea — scroll the
> git history and you can watch it make every research decision alone.
> The paper is just the last lap."

---

## 0 · The big picture

```
   BEFORE  (me)               DURING  (the machine)             5:00 PM
 ┌───────────────┐  press   ┌───────────────────────┐  best   ┌────────┐
 │ I write the   │  ENTER   │ agent loop runs all   │  tag    │ submit │
 │ rulebook      │ ───────► │ day — I can't touch   │ ──────► │ + demo │
 │ (SPEC.md)     │ hands off│ the laptop            │         │        │
 └───────────────┘          └───────────────────────┘         └────────┘
```

> **Say:** "I only choose the topic and write the rules. After I press
> enter, the agent does 100% of the research and writing alone."

---

## 1 · The agent's memory — four files

```
 ┌──────────────────────────────────────────────────────────────────┐
 │  SPEC.md      = the RULEBOOK     mission, rules, and the         │
 │                                  checklist the paper is graded   │
 │                                  against. Never changes.         │
 │  TODO.md      = the LOGBOOK      what's done, what's broken      │
 │  VERIFY.log   = the INSPECTION   which checks failed last lap    │
 │  EDITORIAL.md = the COMPASS      the editor's current story      │
 │                                  and marching orders             │
 └──────────────────────────────────────────────────────────────────┘

  Each agent lives ~5 minutes and remembers NOTHING.
  These files (plus git history) ARE the memory.
```

> **Say:** "Every agent is brand new — no memory. The project's memory
> lives in files, like shift workers sharing one logbook."

---

## 2 · The loop — the factory

```
        ┌───────────────────────────────────────────────────┐
        │                                                   │
        ▼                                                   │
  [1] WAKE      a brand-new agent reads the memory files    │
        │                                                   │
        ▼                                                   │
  [2] WORK      does exactly ONE task, saves to git         │
        │       (download data / run analysis /             │
        ▼        write a section / fix a failure)           │
  [3] INSPECT   dumb scripts — NOT AI — check everything    │
        │                                                   │
        ├── any fail ──► written into TODO.md ──────────────┤
        │                (next agent's first job: fix it)   │
        ▼  all pass                                         │
  [4] REVIEW    every 3rd lap: a separate skeptical agent   │
        │       grades the paper against the rulebook /10   │
        │       and updates the COMPLAINT SCOREBOARD:       │
        │       every complaint gets a permanent name and   │
        │       a status — new / still open / fixed.        │
        │       A passing grade (6+) gets a second read     │
        ▼       by a fresh reviewer; the LOWER one counts   │
  [4b] EDITOR   after each review: reads everything, sets   │
        │       the paper's honest STORY, and rewrites      │
        │       TODO.md around it. A complaint surviving    │
        │       two reviews gets the next lap to itself.    │
        │       Score stuck two reviews in a row? Then      │
        ▼       fix the OLDEST open complaint first.        │
  [5] RATCHET   all checks green + grade 6 or higher?       │
        │       → tag this version "safe to submit"         │
        │                                                   │
        └────────────── repeat until 5 PM ──────────────────┘
```

> **Say:** "The writer is creative and untrusted. The protected checks are
> deterministic. The reviewer is skeptical and keeps score of every
> complaint. The editor sets the story. Four roles, and none of them
> can do another's job."

---

## 3 · The three locks — how fabrication becomes visible

```
 LOCK 1 · numbers have only ONE road into the paper
 ─────────────────────────────────────────────────
   internet ──► data/cache/ ──► analysis ──► results.json ──► blanks ──► PDF
   (public       (frozen         (scripts      (every           (fill-in
    data)         copy)           do all        number           the-blank
                                  the math)     lives here)      paper)

   If the agent types a numeric literal directly into the paper,
   a script spots it instantly → FAIL. Publication years are the exception.

 LOCK 2 · citations must be real
 ───────────────────────────────
   Every reference is looked up in real paper databases
   (Crossref, Semantic Scholar). Invented paper → no match → FAIL.

 LOCK 3 · the locks themselves are locked
 ────────────────────────────────────────
   The loop keeps checksums (digital fingerprints) of every checker.
   If an agent edits a checker to always say "pass",
   it gets auto-reverted and the attempt is logged.

 FINAL PROOF · the re-run
 ────────────────────────
   Every lap rebuilds scoring from cached raw outputs. Before submission,
   delete raw outputs too and repeat model inference from frozen weights.
```

> **Say:** "We never rely on asking the AI to be honest. Numbers must pass
> through public analysis code, citations must match real databases, frozen
> inputs are checksummed, and protected checks are restored after tampering.
> Reproduction proves traceability; reviewers still judge whether the design
> and scoring are scientifically correct."

---

## 4 · The safety net — the ratchet

```
   paper-v1 ────► paper-v2 ────► paper-v3 ────► ... ────► submit highest
      ▲               ▲
      first version    only tagged if all checks pass AND the
      to pass          grade didn't drop — the paper can get
      everything       better, but can never get worse
```

Plus: EVERY lap where all checks pass gets a backup tag (green-vN),
even if the grade is low. Something verified is always submittable.

> **Say:** "From the first tagged version onward, I always have a
> working, fully-verified paper — a broken submission at 5 PM is impossible."

---

## 5 · The run in numbers (measured, from-zero test 2026-07-03)

```
 one lap            ≈ 3–8 min including all checks (hard stop at 15)
 fuel per lap       ≈ 76k tokens on average
 review             every 3rd lap; a passing grade gets a second,
                    independent read — the lower score counts
 the from-zero test 15 laps in ~85 minutes: every check green,
                    first accepted paper at lap 6 (about half an
                    hour in), four accepted versions by lap 15
 full event day     ≈ 40–60 laps; runs on the event's API credits —
                    my personal plan caps out after ~2 hours
 acceptance bar     all checks green + checklist grade ≥ 6/10,
                    confirmed by the second read, and never lower
                    than the last accepted version
```

> **Say:** "One lap is about five minutes. In this morning's full test
> the machine went from an empty folder to an accepted, fully verified
> paper in six laps — about half an hour — and then kept improving it
> for the rest of the run."

---

## 6 · When things go wrong — they will, that's designed for

```
 a check fails          → written to TODO.md; the NEXT agent's first job
                          is the fix (fresh eyes, no ego)
 same complaint twice   → the next lap is spent ENTIRELY on that one
                          complaint, nothing else
 the grade stops moving → the scoreboard shows work is still happening
                          (complaints keep getting fixed); after two
                          flat grades, the oldest open complaint gets
                          fixed first
 agent hangs            → 15-min timeout kills the lap; loop continues
 agent edits a checker  → checksum mismatch → auto-revert + logged
 reviewer never gives 6 → every all-green version still gets a backup
                          tag (green-vN) — something verified is ALWAYS
                          submittable at 5 PM
 out of AI quota        → the loop notices, sleeps 10 minutes, retries —
                          it resumes by itself
 laptop / wifi dies     → git saved every lap; restart the loop,
                          nothing is lost
```

> **Say:** "The design assumes agents will fail, hang, and even try to
> cheat — and has a specific, boring answer for each one."

---

## 7 · Judge Q&A — the hard questions, answered

**"How is this different from just asking ChatGPT to write a paper?"**
One-shot AI papers can invent citations and make up numbers. Here numbers
must pass through public analysis code, citations must match real databases,
frozen inputs are checksummed, and deterministic scripts enforce those rules
every lap. Reviewers still inspect whether the analysis itself is sound.

**"Did you write any of the paper?"**
No. I wrote the rulebook before the start. The git log is the proof —
every commit during the event came from the loop.

**"How do you know the numbers are CORRECT, not just reproducible?"**
Honest answer: reproducibility proves traceability, not that the code is
bug-free. Three defenses: deliberately simple analyses, sanity checks
(percentages must be 0–100, sample sizes above a floor), and the reviewer
must read the code behind the headline result.

**"Why fresh agents instead of one long session?"**
Long sessions rot — the AI's context fills with its own mistakes and it
doubles down on them. A fresh agent has no ego about a previous agent's
bad idea. Bonus: a crash loses nothing, since the repo is the memory.

**"Why should your reviewer agent's grade mean anything?"**
Three reasons. It was calibrated before the event: shown the same paper
honest and sabotaged, it scored the honest one higher and rejected the
sabotage, naming the exact violation (evidence in harness/calibration/).
Its grade is anchored to a FIXED checklist — does the paper do what the
rulebook demands — not to taste, and any passing grade must survive a
second independent read (the lower score counts). And it never grades
alone — the dumb checkers catch the objective failures first.

**"The grade sits at 7 — is the paper stuck?"**
No, and I can prove it. The reviewer keeps a scoreboard of every
complaint: new, still open, or fixed. In testing, the grade sat at 7
while the machine fixed complaint after complaint — missing uncertainty
intervals, no held-out prediction test, under-reported models — and the
reviewer kept finding new, harder ones. That's what a working quality
process looks like: the bar keeps rising. The dashboard plots complaints
fixed right next to the grade, so you can watch the real progress.

**"What if your research question's answer is 'no effect'?"**
Then the paper honestly says so. A verified null result is still real
science — this machine optimizes for *verified*, not *exciting*.

**"What was built before the event vs during it?"**
Before: the harness (loop, checkers, reviewer) and the rulebook — my
inputs. During: every experiment, number, figure, and sentence of the
paper. The git timestamps draw that line publicly.

**"How is this different from STORM, or Sakana's AI Scientist?"**
STORM (Stanford) writes Wikipedia-style survey articles by reading and
summarizing existing sources — it runs no experiments. Sakana's AI
Scientist does run experiments and write ML papers end-to-end. Our emphasis
is a public chain from frozen inputs to paper macros, plus deterministic
checks and a skeptical review loop. The contribution is stronger verification
and auditability, not a claim that automated science becomes infallible.

**"This is an ML event — why isn't your paper about machine learning?"**
The track tests whether an agent can do verifiable research; the machine
is domain-agnostic and would run an ML topic identically. I picked the
question a 15-year-old actually has stakes in — do grades decide your
future? — because real curiosity makes better research than fake
curiosity. And a social-science paper is a harder verification test:
messy human data, survey weights, confounders — if the checks hold here,
they hold anywhere.

---

## 8 · The evidence — what to physically show

```
 the PDF        the paper itself, ICML format
 git tag list   the ratchet history = the story of the day
 the dashboard  grades, complaint scoreboard, complaints-fixed line,
                the live PDF — this is the projector screen
 VERIFY.log     every check result of every lap, timestamped
 git log        dozens of commits, none by a human hand
 the re-run     delete results.json → `make all` → same numbers
                come back. Do this LIVE if time allows.
```

---

## 9 · The research itself

```
 Question    : Does more context degrade an AI model's performance?
               If so, when does it start, and by how much?
 Data        : A small open model (Qwen2.5-0.5B) frozen on this laptop,
               answering hundreds of generated find-the-fact quizzes.
               No internet, temperature zero: same quiz, same answer,
               every single time — anyone can re-run it.
 Analysis    : (1) accuracy as the context grows (~2k → 8k tokens)
               (2) accuracy by WHERE the fact sits (start/middle/end)
               (3) does RELEVANT extra text hurt less than junk text?
               (4) which cheap fix recovers the most accuracy?
 Headline    : the point where adding context starts costing accuracy —
               and whether "good" context degrades too
 Limitations : one small model (may not transfer to big ones); synthetic
               quizzes, not real documents; retrieval accuracy is not
               general intelligence; grid capped by the CPU budget
```

> **Say:** "Everyone stuffs more context into these models and assumes
> more is better. While I wasn't allowed to touch my laptop, my agent
> measured exactly when that stops being true — on a model small enough
> that you can delete the results and watch every number come back."

> Rule: if I can't fill this section in from memory, the topic is wrong.

---

## The 30-second judge script (all five, in order)

1. "I wrote the rulebook; the agent did everything else — I never
   touched the laptop."
2. "Every five minutes a fresh agent with no memory wakes up, reads the
   shared logbook, does one task, and clocks out."
3. "Dumb scripts inspect every lap: every citation must exist in real
   databases, and the agent physically can't type numbers — every
   number is compiled from experiments in the repo."
4. "The checkers are fingerprinted, so it can't cheat by rewriting the
   rules — and the reviewer keeps a scoreboard of every complaint, so
   nothing it finds is ever forgotten."
5. "Every improvement gets tagged, so this paper was submit-ready for
   hours — and you can delete the results and re-run everything to
   watch the same numbers come back."

---

## Architecture changelog (print date = state date)

```
 2026-07-01  v1 designed: fresh-agent loop, 3 locks, skeptical reviewer,
             ratchet tags. Topic locked (NLSY97 grades → net worth at 30).
 2026-07-02  Data frozen and checksummed. Checkers built and live-tested.
             Sabotage test: 5 cheating attempts, 5 caught. Long practice
             runs. EDITOR role added (the strategy layer). Passing grades
             now need a second independent read. Live dashboard added.
             First accepted paper (grade 7, confirmed 7).
 2026-07-03  Two full from-zero test runs. Found and fixed: version tags
   morning    could collide with practice tags and fail silently — worse,
             the log claimed success anyway. Codex app broke overnight
             (Apple revoked its certificate) — switched to the npm
             version; health check added to the runbook. The machine's
             own reviewer caught leftover rules from an abandoned topic
             still sitting in the rulebook — fixed.
 2026-07-03  Complaint scoreboard added: the reviewer names every
   afternoon  complaint and marks it new / still open / fixed — nothing
             gets forgotten or quietly renamed. Stuck-score rule: two
             flat grades in a row → the next lap fixes the OLDEST open
             complaint. Dashboard now plots complaints-fixed beside the
             grade — the growth that keeps going when the grade
             flattens. Practice tags can no longer leak into the public
             event repo.
 2026-07-03  Third full test run: grade broke the ceiling — 5, 7, 8, 8,
   evening    8, four accepted versions, and the scoreboard proved nine
             complaints fixed. The loop also survived a 2.5-hour AI
             quota outage unattended and finished itself. But one
             focused lap was NOT enough to fix the hardest complaint —
             which led to today's rules:
 2026-07-04  A hard complaint now KEEPS the focus lap until the reviewer
   morning    confirms it fixed (not just "attempted"). Any complaint
             open for 3+ reviews must end in one of two states: fixed,
             or honestly owned in the paper's limitations with the
             claims narrowed to match — nothing stays open forever. The
             fixed-counter now counts unique complaints (a re-listed
             old win can't inflate it). Every paper must end with a
             reproducibility note — reviewers who never see a demo
             still read the proof. Event format learned: papers due
             5 PM, then conference-style peer review (other teams' AI
             reviewers grade our paper — the exam we rehearse daily).
 2026-07-04  TOPIC PIVOT: organizers signal papers must be ML-related.
   morning    New primary: "when does more context stop helping?" — a
             small frozen model quizzed deterministically on this
             laptop (spike passed: byte-identical re-runs, ~200-quiz
             grid fits a 45-min budget). Grades→net-worth becomes
             fallback #1. Pipeline goes two-tier: expensive model runs
             (make probes) feed a fast scoring step (make results) the
             checkers re-run every lap; clean-room proof now re-runs
             the model itself (make clean-deep && make all).
```
