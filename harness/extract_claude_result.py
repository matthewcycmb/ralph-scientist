#!/usr/bin/env python3
"""Extract Claude Code's final result from a stream-json log."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: extract_claude_result.py STREAM_LOG OUTPUT", file=sys.stderr)
        return 2
    stream = Path(sys.argv[1])
    output = Path(sys.argv[2])
    result = ""
    for line in stream.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "result" and isinstance(event.get("result"), str):
            result = event["result"].strip()
    if not result:
        print(f"no Claude result event found in {stream}", file=sys.stderr)
        return 1
    output.write_text(result + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
