# Event-Day Runbook — Ralphthon @ICML, July 12, 2026

You type three commands all day. Everything else is watching and presenting.

## Before the event (July 10–11, at home)

1. Freeze the harness — no more code changes after the dress rehearsal.
2. `harness/reset_for_event.sh` → creates the clean `event-day` branch:
   one commit containing ONLY the declared pre-built inputs (harness, SPEC,
   frozen data). The practice paper, its analysis, and all practice history
   stay behind on the practice branch. The script creates `event-day-start` as
   the declared boundary. If a final pre-run repair is needed, move that tag to
   the reviewed repair commit before starting; everything after the tag is event work.
3. Create the public GitHub repo, push the event branch.
4. Charge laptop + power bank; pack charger and phone (hotspot backup).
5. Print or save FLOWCHART.md (the crib sheet + judge script).
6. Verify `codex` auth still works (`codex exec "say ok"`).
7. Run `make test`; the event-critical checkpoint and integrity regressions must pass.
8. Codex CLI health check — lesson of 2026-07-03, when Codex.app's signing cert
   was revoked overnight and macOS silently SIGKILLed the CLI (exit 137, no
   output): run `codex --version`. If it prints nothing / exit 137, diagnose
   with `spctl -a -vv /Applications/Codex.app` and reinstall the standalone
   CLI: `npm install -g @openai/codex` (auth in ~/.codex carries over).
9. `git status --short` must be empty. The loop intentionally refuses to start from a
   dirty tree so pre-run repairs cannot be misrepresented as autonomous event work.

## At the venue (before the gun, ~8:30–9:30)

1. Wifi + power. Set macOS to never sleep, or run everything under
   `caffeinate -is`. Re-run the codex health check (`codex --version` +
   `codex exec "say ok"`) — things break overnight; they must break NOW,
   not at the gun.
2. Event Codex credits: if organizers hand out API keys, wire them in
   (`OPENAI_API_KEY` or `codex login` per their instructions). This is NOT
   optional-nice-to-have: the ChatGPT-plan quota capped out after ~1.7M
   tokens in practice (≈2 hours of running) — a full event day needs the
   provided credits. Plan auth is the fallback only. If the loop logs
   "QUOTA:" lines, it is backing off automatically; it resumes by itself.
3. If organizers announce constraints (topic rules, submission format),
   this is the LAST moment SPEC.md can be edited. Then hands off.
4. Open Terminal and run, exactly:

```
cd ~/ralphm/Ralphm
tmux new -s ralph
# pane 1 — preflight, then the machine + dashboard + W&B mirror:
harness/start_event.sh --check
harness/start_event.sh
# split pane: press Ctrl-b then %  — then in pane 2, the live status view:
tail -f VERIFY.log
```

(tmux survives a closed window: `tmux attach -t ralph` reconnects.)

The launcher starts the local dashboard at
`http://127.0.0.1:8788/harness/dashboard/` and the authenticated W&B mirror.
This is also the demo screen: put it on the projector. Set `SKIP_WANDB=1` only
if you intentionally need the research loop to continue without the mirror.

That's it. That is the entire "how do I run it."

## During the loop (9:30 → ~4:40 PM; papers due 5 PM)

- DO NOT touch the laptop. The rule is the format; the format is the demo.
- Watch pane 2: gates flipping, tags appearing (`green-vN`, then `paper-vN`).
  With PUSH=1 every lap pushes to GitHub — judges can watch commits land live.
- Something looks catastrophically wedged (no commits for 30+ min, loop
  crashed)? That is literally what the lobster costume is for: suit up,
  restart the loop (`harness/loop.sh` again — the repo is the memory, nothing
  is lost), de-suit.
- NEVER edit harness files while the loop runs — the tamper guard cannot tell
  you from an agent and will revert the edit. Stop the loop, edit, restart.
- Laptop dies? Clone the pushed repo on any machine, `python3 -m venv .venv &&
  .venv/bin/pip install -r requirements.txt`, `brew install tectonic coreutils`,
  restart the loop. (This is why PUSH=1 matters.)

## Submission (5 PM) + peer review (next ~30 min)

Format (host post, 2026-07-03): conference-style review, not stage judging.
Papers due 5 PM → 30 min of peer review (you review other Track 1 papers;
Track 2's AI review agents review yours) → AC reviewers read papers +
reviews → SAC final pass. Live demo NOT confirmed — check the email reply.

- ~4:30 PM: stop expecting new tags; the best `paper-vN` is the submission.
  Leave the loop running until the deadline — a late tag is free upside.
- Submit: PDF of the best tag + public repo link + declare the line:
  `event-day-start` = declared inputs, everything after = born at the event.
- PEER-REVIEW HALF HOUR — your reviews are also graded. Use the machine's
  own checklist on each paper, ~5 min each: (1) pick one number — can you
  trace where it came from? (2) pick one citation — does the paper exist?
  (3) is the claim bigger than the evidence? (4) are limitations honest or
  hidden? (5) can you follow it without jargon? Write 3 specific sentences
  per paper: strongest thing, weakest thing, one question. Specific beats
  clever — "Table 2's n is never stated" is a great review line.
- If a demo slot DOES exist: FLOWCHART 30-second script + the kill shot
  (`make clean && make all` — scoring and the PDF regenerate live). The full
  inference proof is `make clean-deep && make all` and takes about 45 minutes.

## If everything goes wrong

- Loop keeps failing gates all day → shadow `green-vN` tags mean the last
  verified state is always submittable.
- No tags at all → the git log + VERIFY.log of honest failed attempts is
  STILL a demo: "here is a machine that refuses to publish what it cannot
  verify" — argue the thesis with the evidence you have.
