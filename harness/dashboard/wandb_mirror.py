#!/usr/bin/env python3
"""Mirror the live dashboard's numbers to Weights & Biases (event observability
partner). Strictly decoupled, write-only telemetry:

  - Reads ONLY what the dashboard already generates (logs/status.json) plus
    results.json. Never writes anything the loop or agents read.
  - Opt-in: does nothing without WANDB_API_KEY (or WANDB_MODE=offline for a
    dry run). If W&B is down or the key is wrong, the machine never notices.
  - Run with the Python named by the installed `wandb` executable (the project's
    pinned .venv stays frozen). `harness/start_event.sh` discovers it automatically.

Git remains the source of truth; this is a public live window onto it.
"""
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATUS = ROOT / "logs" / "status.json"
RESULTS = ROOT / "results.json"
INTERVAL = 30  # seconds between mirror ticks

HEADLINE_KEYS = [
    "sampleSize", "accTwoK", "accFourK", "accEightK",
    "accStart", "accMiddle", "accEnd",
    "accLiteral", "accParaphrase", "accClosedBook", "accKeywordPruned",
]


def read_json(path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def snapshot():
    """One flat dict of everything worth mirroring. Missing pieces are skipped."""
    out = {}
    s = read_json(STATUS)
    if s:
        try:
            out["lap"] = int(s.get("last_gates", {}).get("iter", 0))
        except (TypeError, ValueError):
            pass
        gates = s.get("last_gates", {}).get("gates", [])
        if gates:
            out["gates_passed"] = sum(1 for g in gates if g.get("ok"))
            out["gates_total"] = len(gates)
        reviews = s.get("reviews") or []
        if reviews:
            last = reviews[-1]
            for k in ("rubric", "overall", "soundness", "presentation", "significance", "originality"):
                if isinstance(last.get(k), (int, float)):
                    out[f"review_{k}"] = last[k]
        rd = s.get("readability")
        if rd:
            out["readability_flesch"] = rd.get("flesch")
            out["readability_grade"] = rd.get("grade")
            out["paper_words"] = rd.get("words")
        tags = s.get("tags") or []
        out["paper_tags"] = sum(1 for t in tags if t.startswith("paper"))
        out["green_tags"] = sum(1 for t in tags if t.startswith("green"))
        out["loop_running"] = bool(s.get("loop_running"))
    r = read_json(RESULTS)
    if r:
        vals = r.get("values", {})
        for k in HEADLINE_KEYS:
            v = vals.get(k, {}).get("value")
            if isinstance(v, (int, float)):
                out[k] = v
    return {k: v for k, v in out.items() if v is not None}


def has_stored_login():
    try:
        return "api.wandb.ai" in (Path.home() / ".netrc").read_text()
    except Exception:
        return False


def main():
    if (not os.environ.get("WANDB_API_KEY") and not has_stored_login()
            and os.environ.get("WANDB_MODE") != "offline"):
        print("wandb_mirror: no W&B credentials found — exiting quietly.")
        print("  to enable: `python3 -m wandb login <key>` once, then rerun.")
        return 0
    import wandb  # imported late so the no-key path needs nothing installed
    run = wandb.init(
        project=os.environ.get("WANDB_PROJECT", "ralph-scientist"),
        name=os.environ.get("WANDB_RUN_NAME", "event-day"),
        config={"source": "logs/status.json + results.json (mirror, read-only)"},
    )
    print(f"wandb_mirror: streaming every {INTERVAL}s -> {run.url if hasattr(run, 'url') else 'offline'}")
    last = None
    once = "--once" in sys.argv
    while True:
        snap = snapshot()
        if snap and snap != last:
            try:
                wandb.log(snap, step=int(snap.get("lap", 0)) or None)
                last = snap
            except Exception as e:
                print(f"wandb_mirror: log failed ({e}); machine unaffected, retrying next tick")
        if once:
            break
        time.sleep(INTERVAL)
    wandb.finish()
    return 0


if __name__ == "__main__":
    sys.exit(main())
