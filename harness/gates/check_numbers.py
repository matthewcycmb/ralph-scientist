#!/usr/bin/env python3
"""Gate: no numeric result literals in paper prose.

Every number in the paper must arrive via a macro from paper/values.tex
(generated from results.json by analysis/make_values.py). This gate scans the
LaTeX source the agent writes and fails on hand-typed numbers.

Rules (strict on purpose — the agent adapts, the gate doesn't):
  FORBIDDEN in paper/*.tex (except values.tex):
    - any number containing a decimal point        (0.34, 12.5)
    - any number attached to % / \\%               (12%, 12\\%)
    - any number with thousands separators         (40,000)
    - any number preceded by a currency \\$        (\\$500)
    - any bare integer > 120, unless it looks like a year (1900-2100)
  ALLOWED:
    - bare integers 0-120 (ages, grades, small counts: "age 30", "grade 9")
    - years 1900-2100 ("since 1997", "\\usepackage{icml2025}")
    - anything inside comments is stripped first, but don't hide numbers there:
      comments are for humans, results are for results.json
"""
import re
import sys
from pathlib import Path

PAPER_DIR = Path("paper")
EXEMPT = {"values.tex"}


def strip_tex(text: str) -> str:
    """Remove comments, reference-like commands, and layout dimensions."""
    text = re.sub(r"(?<!\\)%.*", "", text)  # comments (not \%)
    text = re.sub(
        r"\\(cite[pt]?|ref|eqref|label|input|include|includegraphics|bibliography"
        r"|bibliographystyle|usepackage|documentclass|begin|end|pagenumbering)"
        r"(\[[^\]]*\])?\{[^}]*\}",
        " ",
        text,
    )
    # layout dimensions: \vskip 0.3in, \hspace{2em}, 0.5\linewidth, 10pt ...
    # (unit must be attached to the number — "30 in 2014" prose is NOT matched)
    text = re.sub(r"\\[vh]s(?:kip|pace)\*?\s*\{?\s*-?[\d.]+\s*[a-z]{2}\}?", " ", text)
    text = re.sub(r"-?\d+(?:\.\d+)?(?:in|pt|em|ex|cm|mm|bp|pc|sp)\b", " ", text)
    text = re.sub(r"[\d.]+\\(?:line|text|column)width", " ", text)
    return text


def violations_in(text: str):
    out = []
    for m in re.finditer(r"(\\\$\s*)?\d[\d,]*(\.\d+)?(\s*\\?%)?", text):
        tok = m.group(0)
        has_currency = tok.startswith("\\$")
        has_decimal = "." in tok
        has_pct = tok.rstrip().endswith("%")
        has_comma = "," in tok.rstrip(",")  # trailing sentence comma isn't a separator
        core = tok.lstrip("\\$ ").rstrip("\\% ").rstrip(",")
        try:
            intpart = int(core.split(".")[0].replace(",", ""))
        except ValueError:
            continue
        is_year = 1900 <= intpart <= 2100 and not (has_decimal or has_pct or has_currency or has_comma)
        small_int = intpart <= 120 and not (has_decimal or has_pct or has_currency or has_comma)
        if not (is_year or small_int):
            out.append(tok.strip())
    return out


def main() -> int:
    if not PAPER_DIR.is_dir():
        print("FAIL: paper/ directory does not exist yet")
        return 1
    tex_files = [p for p in PAPER_DIR.glob("*.tex") if p.name not in EXEMPT]
    if not tex_files:
        print("FAIL: no .tex files in paper/ yet")
        return 1
    bad = 0
    for path in tex_files:
        for lineno, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            for tok in violations_in(strip_tex(line)):
                print(f"FAIL {path}:{lineno}: hand-typed number '{tok}' — "
                      f"use a macro from values.tex (generated from results.json)")
                bad += 1
    if bad:
        print(f"{bad} numeric literal(s) found. Numbers must be computed, not typed.")
        return 1
    print(f"PASS: no hand-typed result numbers in {len(tex_files)} tex file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
