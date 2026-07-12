#!/usr/bin/env python3
"""Gate the three required submission artifacts: anonymous PDF source, title, abstract."""

from __future__ import annotations

import re
import sys
from pathlib import Path


TEX = Path("paper/main.tex")
SENSITIVE = (
    "matthew chan",
    "jchanh@gmail.com",
    "ralph scientist",
    "ralphthon @icml",
    "track one",
)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def plain_words(value: str) -> list[str]:
    value = re.sub(r"(?m)%.*$", " ", value)
    value = re.sub(r"\\[A-Za-z@]+(?:\[[^]]*\])?", " ", value)
    value = re.sub(r"[{}~\\]", " ", value)
    return re.findall(r"[A-Za-z][A-Za-z'-]*", value)


def main() -> int:
    if not TEX.is_file():
        fail("paper/main.tex is missing")
    source = TEX.read_text(encoding="utf-8")
    active = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("%"))
    lowered = active.lower()

    if re.search(r"\\usepackage\s*\[[^]]*accepted[^]]*\]\s*{icml2026}", active):
        fail("ICML `accepted` mode exposes author information")
    exposed = [term for term in SENSITIVE if term in lowered]
    if re.search(r"ralphthon\s*@?\s*icml", lowered):
        exposed.append("ralphthon/icml affiliation")
    if exposed:
        fail("source contains identifying submission text: " + ", ".join(exposed))
    if "\\label{main-body-end}" not in active:
        fail("main-body page boundary label is missing")

    title = re.search(r"\\icmltitle\s*{(.*?)}\s*\\icmlsetsymbol", active, re.DOTALL)
    if not title:
        fail("could not extract \\icmltitle")
    title_words = plain_words(title.group(1))
    if len(title_words) < 6 or any(word.lower() in {"todo", "pending", "placeholder"} for word in title_words):
        fail("title must be concrete and descriptive")

    abstract = re.search(r"\\begin{abstract}(.*?)\\end{abstract}", active, re.DOTALL)
    if not abstract:
        fail("abstract environment is missing")
    abstract_words = plain_words(abstract.group(1))
    if len(abstract_words) < 50:
        fail(f"abstract is not submission-ready ({len(abstract_words)} words; require at least 50)")
    if any(term in abstract.group(1).lower() for term in ("todo", "pending", "placeholder")):
        fail("abstract still contains placeholder language")

    print(f"PASS: anonymous source, concrete title, and {len(abstract_words)}-word abstract")
    return 0


if __name__ == "__main__":
    sys.exit(main())
