#!/usr/bin/env python3
"""Return success only when an agent log represents a real quota outage."""

from __future__ import annotations

import json
import sys
from pathlib import Path


QUOTA_PHRASES = (
    "hit your usage limit",
    "you've hit your limit",
    "usage limit reached",
    "usage limit exceeded",
    "rate limit exceeded",
)


def has_quota_outage(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    lowered = text.lower()
    if any(phrase in lowered for phrase in QUOTA_PHRASES):
        return True
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "rate_limit_event":
            status = str(event.get("rate_limit_info", {}).get("status", "")).lower()
            if status and status != "allowed":
                return True
        if event.get("type") == "result" and event.get("is_error"):
            rendered = json.dumps(event, sort_keys=True).lower()
            if "rate_limit" in rendered or any(phrase in rendered for phrase in QUOTA_PHRASES):
                return True
    return False


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_quota.py AGENT_LOG", file=sys.stderr)
        return 2
    return 0 if has_quota_outage(Path(sys.argv[1])) else 1


if __name__ == "__main__":
    raise SystemExit(main())
