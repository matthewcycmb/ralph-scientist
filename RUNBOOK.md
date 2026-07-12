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
2. The organizers do not provide OpenAI credits. Preserve the remaining Codex
   allowance for the calibrated reviewer and emergency fallback. Claude Code is
   the primary worker when a Claude Max subscription is available:
   `claude auth login`, then verify `claude auth status` reports `loggedIn: true`.
   The event launcher uses `WORKER_BACKEND=claude` with the `fable` model alias.
   If Claude reports a quota/rate limit, the same lap automatically retries on
   Codex. If Codex is exhausted, work returns to Fable. The editor and prose
   roles and routine scientific reviews use Fable too. Codex is reserved for one
   deliberate audit of the final candidate near 15:30, or emergency fallback if
   Claude is unavailable. If both providers fail consecutively, the loop backs
   off instead of spinning.
3. If organizers announce constraints (topic rules, submission format),
   this is the LAST moment SPEC.md can be edited. Then hands off.
4. Open Terminal and run, exactly:

```
cd ~/ralphm/Ralphm
tmux new -s ralph
# pane 1 — before 12:30, preflight only:
WORKER_BACKEND=claude harness/start_event.sh --check
# at or just after 12:30 KST, start the official loop:
WORKER_BACKEND=claude harness/start_event.sh
# split pane: press Ctrl-b then %  — then in pane 2, the live status view:
tail -f VERIFY.log
```

(tmux survives a closed window: `tmux attach -t ralph` reconnects.)

The launcher starts the local dashboard at
`http://127.0.0.1:8788/harness/dashboard/`. W&B is optional: when credentials
and its runtime are available the mirror starts, but a W&B failure never blocks
paper production.

That's it. That is the entire "how do I run it."

## Official timeline

- 11:00–12:30: research specification and preflight; do not run experiments.
- 12:30–15:30: autonomous Ralph Loop.
- 15:30–16:30: human editing, final title/abstract, anonymity check, and submission.
- 16:30: hard submission cutoff and matching snapshot.
- 16:35–17:00: Track 1 self-review.

## During the loop (12:30–15:30 KST)

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

## Submission (hard cutoff 16:30) + self-review (16:35–17:00 KST)

Agent review is assignment-only and API-only through `https://openagentreview.org`.
The organizer-triggered assignment set contains exactly ten distinct papers, with
real papers first and explicitly labeled rehearsal papers afterward. Review only
the returned assignments. Exact operational instructions live in
`harness/ASSIGNMENT_REVIEW.md`.

- 15:30: stop the loop and begin the human editing window. Select the best
  reviewed `paper-vN`, falling back to the highest green tag if necessary.
- Submit the anonymous PDF, title, and abstract by 16:30. Code, logs, the public
  repo, and W&B are optional and must not delay these three required artifacts.
- Provenance: `event-day-start` preserves the earlier pre-event boundary;
  `official-loop-start-20260712-1230` marks the official autonomous run.
- ASSIGNMENT-REVIEW WINDOW — your reviews are also graded. Use the machine's
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
