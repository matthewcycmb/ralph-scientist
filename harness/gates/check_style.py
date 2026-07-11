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
    # Casual rehearsal-v13 language that weakens a professional research register.
    "made-up",
    "knob", "knobs",
    "readout", "readouts",
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
    "in this run",
    "current grid",
]

WORD_RE = re.compile(r"\b(" + "|".join(BANNED_WORDS) + r")\b", re.IGNORECASE)
PHRASE_RE = re.compile("|".join(re.escape(p) for p in BANNED_PHRASES), re.IGNORECASE)
# ASCII -- (not ---) is fine only as digit--digit; --- is always an em dash.
TRIPLE_DASH_RE = re.compile(r"---")
DOUBLE_DASH_RE = re.compile(r"(?<![-\d])--(?![-\d])")
REPETITION_LIMITS = [
    (re.compile(r"\bthis paper\b", re.IGNORECASE), 2, "This paper"),
    (re.compile(r"\bin the contract example\b", re.IGNORECASE), 1, "In the contract example"),
]


def strip_comments(line: str) -> str:
    return re.sub(r"(?<!\\)%.*$", "", line)


def plain_tex(text: str) -> str:
    """Reduce LaTeX prose enough for conservative sentence-shape checks."""
    text = "\n".join(strip_comments(line) for line in text.splitlines())
    text = re.sub(r"\$[^$]*\$|\\\([^)]*\\\)", " ", text, flags=re.S)
    text = re.sub(r"\\begin\{[^}]+\}|\\end\{[^}]+\}", " ", text)
    text = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", text)
    return re.sub(r"[{}~&]", " ", text)


def sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if re.search(r"[A-Za-z]", part)]


def main() -> int:
    if not TEX.exists():
        print("PASS: paper/main.tex does not exist yet (nothing to check)")
        return 0
    errors = 0
    raw_text = TEX.read_text(errors="replace")
    for lineno, raw in enumerate(raw_text.splitlines(), 1):
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
    prose = "\n".join(strip_comments(line) for line in raw_text.splitlines())
    for pattern, limit, label in REPETITION_LIMITS:
        count = len(pattern.findall(prose))
        if count > limit:
            print(
                f"FAIL: repeated frame '{label}' appears {count} times (limit {limit}) — "
                "vary sentence structure and lead with the evidence"
            )
            errors += 1
    if "\\begin{document}" in raw_text:
        abstract_match = re.search(
            r"\\begin\{abstract\}(.*?)\\end\{abstract\}", raw_text, flags=re.S
        )
        if not abstract_match:
            print("FAIL: paper has no abstract environment")
            errors += 1
        else:
            abstract_sentences = sentences(plain_tex(abstract_match.group(1)))
            if not 4 <= len(abstract_sentences) <= 7:
                print(
                    f"FAIL: abstract has {len(abstract_sentences)} sentences; use 4-7 "
                    "for question, design, principal estimate, qualification, and takeaway"
                )
                errors += 1

        displays = len(re.findall(r"\\begin\{(?:table|figure)\*?\}", raw_text))
        if not 2 <= displays <= 4:
            print(f"FAIL: paper has {displays} result displays; a 2-4 page paper should use 2-4 selective displays")
            errors += 1

        body_sentences = sentences(plain_tex(raw_text))
        word_counts = [len(re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)?", item)) for item in body_sentences]
        for index, count in enumerate(word_counts, 1):
            if count > 45:
                print(f"FAIL: sentence {index} has {count} words (limit 45) — split the claim from its qualification")
                errors += 1
        for index in range(len(word_counts) - 2):
            streak = word_counts[index : index + 3]
            if all(2 <= count <= 6 for count in streak):
                print(
                    f"FAIL: sentences {index + 1}-{index + 3} are three consecutive short sentences "
                    f"({streak} words) — combine related evidence into professional prose"
                )
                errors += 1
                break
    if errors:
        print(f"{errors} style failure(s) in paper/main.tex")
        return 1
    print("PASS: prose meets deterministic professional-style checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
