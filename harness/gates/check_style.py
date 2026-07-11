#!/usr/bin/env python3
"""Gate: the paper's prose must be clear, direct, and free of AI-slop.

Matthew's editorial rules (2026-07-04), made deterministic:
  - No em dashes: no U+2014/U+2013 characters, no LaTeX ``---``. ASCII ``--``
    is allowed ONLY between digits (page/number ranges like 1980--84).
  - No AI-cliche vocabulary or filler phrases (list below). Say the plain
    thing instead: "use" not "leverage", "important" not "crucial", drop
    "moreover" and start the sentence.

Checks paper/main.tex prose only; LaTeX comments are stripped first.
Every hit is reported with its line number so the fix is mechanical.
"""
import re
import sys
from pathlib import Path

TEX = Path("paper/main.tex")

BANNED_WORDS = [
    "delve", "delves", "delving",
    "leverage", "leverages", "leveraging",
    "crucial", "crucially",
    "pivotal",
    "multifaceted",
    "tapestry",
    "showcase", "showcases", "showcasing",
    "foster", "fosters", "fostering",
    "moreover", "furthermore",
    "paradigm",
    "cutting-edge",
    "comprehensive", "comprehensively",
    "landscape",
    "underscore", "underscores", "underscoring",
]
BANNED_PHRASES = [
    "it is important to note",
    "it is worth noting",
    "plays a vital role",
    "plays a crucial role",
    "in the realm of",
    "in today's",
    "rapidly evolving",
    "a wide range of",
]

WORD_RE = re.compile(r"\b(" + "|".join(BANNED_WORDS) + r")\b", re.IGNORECASE)
PHRASE_RE = re.compile("|".join(re.escape(p) for p in BANNED_PHRASES), re.IGNORECASE)
# ASCII -- (not ---) is fine only as digit--digit; --- is always an em dash.
TRIPLE_DASH_RE = re.compile(r"---")
DOUBLE_DASH_RE = re.compile(r"(?<![-\d])--(?![-\d])")


def strip_comments(line: str) -> str:
    return re.sub(r"(?<!\\)%.*$", "", line)


def main() -> int:
    if not TEX.exists():
        print("PASS: paper/main.tex does not exist yet (nothing to check)")
        return 0
    errors = 0
    for lineno, raw in enumerate(TEX.read_text(errors="replace").splitlines(), 1):
        line = strip_comments(raw)
        if not line.strip():
            continue
        for ch, name in (("—", "em dash (U+2014)"), ("–", "en dash (U+2013)")):
            if ch in line:
                print(f"FAIL: line {lineno}: {name} — rewrite with a comma, period, or parentheses")
                errors += 1
        if TRIPLE_DASH_RE.search(line):
            print(f"FAIL: line {lineno}: '---' (LaTeX em dash) — rewrite with a comma, period, or parentheses")
            errors += 1
        if DOUBLE_DASH_RE.search(line):
            print(f"FAIL: line {lineno}: '--' outside a digit range — only allowed as 1980--84 style ranges")
            errors += 1
        for m in WORD_RE.finditer(line):
            print(f"FAIL: line {lineno}: banned word '{m.group(0)}' — say the plain thing instead")
            errors += 1
        for m in PHRASE_RE.finditer(line):
            print(f"FAIL: line {lineno}: banned phrase '{m.group(0)}' — delete it or state the point directly")
            errors += 1
    if errors:
        print(f"{errors} style failure(s) in paper/main.tex")
        return 1
    print("PASS: prose is clean (no em dashes, no AI-slop vocabulary)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
