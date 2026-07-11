#!/usr/bin/env python3
"""Gate: every citation must be a real, resolvable paper.

For each entry in paper/refs.bib, resolve it against Crossref (primary) and
Semantic Scholar (fallback): the entry's title must match a real record
(fuzzy title similarity >= 0.85) and the first author's family name must
appear on that record. Results are cached in data/cache/citations/ so the
loop never re-queries what it has already verified (and the event can survive
API downtime for already-verified entries).

Also enforces: every \\cite key in the tex exists in refs.bib.
Unused bib entries are a warning, not a failure.

This gate runs OUTSIDE the agent (harness-side network); the agent itself is
offline. It proposes citations; this script verifies them.
"""
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

BIB = Path("paper/refs.bib")
PAPER_DIR = Path("paper")
CACHE = Path("data/cache/citations")
MAILTO = "jchanh@gmail.com"  # Crossref etiquette
SIM_THRESHOLD = 0.85


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def similar(a: str, b: str) -> float:
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def parse_bib(text: str):
    """Minimal BibTeX parser: returns {key: {field: value}}."""
    entries = {}
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)\n\}", text, re.S):
        etype, key, body = m.group(1).lower(), m.group(2), m.group(3)
        if etype in ("comment", "string", "preamble"):
            continue
        fields = {}
        for fm in re.finditer(r"(\w+)\s*=\s*[{\"]((?:[^{}]|\{[^{}]*\})*)[}\"]", body, re.S):
            fields[fm.group(1).lower()] = re.sub(r"\s+", " ", fm.group(2)).strip("{} ")
        entries[key] = fields
    return entries


def first_author_family(author_field: str) -> str:
    first = author_field.split(" and ")[0].strip()
    if "," in first:
        return norm(first.split(",")[0])
    return norm(first.split()[-1]) if first.split() else ""


def fetch_json(url: str, tries: int = 3):
    req = urllib.request.Request(url, headers={"User-Agent": f"ralph-scientist-gate (mailto:{MAILTO})"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if i == tries - 1:
                raise
            if e.code == 429:
                # S2's unauthenticated search limiter needs real patience —
                # 2s/4s backoff just burns the remaining tries (seen 2026-07-04).
                ra = e.headers.get("Retry-After", "")
                time.sleep(min(int(ra) if ra.isdigit() else 30 * (i + 1), 120))
            else:
                time.sleep(2 ** (i + 1))
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 ** (i + 1))


def resolve_crossref(title: str, family: str):
    q = urllib.parse.quote(title)
    data = fetch_json(f"https://api.crossref.org/works?query.bibliographic={q}&rows=5&mailto={MAILTO}")
    for item in data.get("message", {}).get("items", []):
        cand_title = (item.get("title") or [""])[0]
        families = [norm(a.get("family", "")) for a in item.get("author", [])]
        if similar(title, cand_title) >= SIM_THRESHOLD and (not family or family in families):
            return {"source": "crossref", "matched_title": cand_title, "doi": item.get("DOI", "")}
    return None


def resolve_s2(title: str, family: str):
    q = urllib.parse.quote(title)
    data = fetch_json(
        f"https://api.semanticscholar.org/graph/v1/paper/search?query={q}&limit=5&fields=title,authors,year,externalIds"
    )
    for item in data.get("data", []):
        families = [norm((a.get("name") or "").split()[-1]) for a in item.get("authors", []) if a.get("name")]
        if similar(title, item.get("title", "")) >= SIM_THRESHOLD and (not family or family in families):
            return {"source": "semanticscholar", "matched_title": item.get("title", ""),
                    "s2id": item.get("paperId", "")}
    return None


def resolve_arxiv(title: str, family: str):
    """arXiv's own export API — keyless and generous. Covers the arXiv-only ML
    literature (PMLR/COLM/preprints) that Crossref misses and that S2's
    unauthenticated search endpoint 429s for long stretches (seen 2026-07-04)."""
    import xml.etree.ElementTree as ET
    q = urllib.parse.quote(f'ti:"{title}"')
    url = f"http://export.arxiv.org/api/query?search_query={q}&max_results=5"
    req = urllib.request.Request(url, headers={"User-Agent": f"ralph-scientist-gate (mailto:{MAILTO})"})
    for i in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                xml_text = r.read().decode("utf-8", errors="replace")
            break
        except Exception:
            if i == 2:
                raise
            time.sleep(2 ** (i + 1))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for entry in ET.fromstring(xml_text).findall("a:entry", ns):
        cand_title = re.sub(r"\s+", " ", (entry.findtext("a:title", "", ns) or "")).strip()
        families = [norm(n.split()[-1]) for n in
                    (au.findtext("a:name", "", ns) or "" for au in entry.findall("a:author", ns)) if n.split()]
        if similar(title, cand_title) >= SIM_THRESHOLD and (not family or family in families):
            arxiv_id = (entry.findtext("a:id", "", ns) or "").rsplit("/", 1)[-1]
            return {"source": "arxiv", "matched_title": cand_title, "arxiv": arxiv_id}
    return None


def main() -> int:
    cite_keys = set()
    for tex in PAPER_DIR.glob("*.tex"):
        for m in re.finditer(r"\\cite[pt]?(?:\[[^\]]*\])?\{([^}]*)\}", tex.read_text(errors="replace")):
            cite_keys.update(k.strip() for k in m.group(1).split(","))

    if not BIB.exists():
        if cite_keys:
            print(f"FAIL: {len(cite_keys)} \\cite key(s) used but paper/refs.bib does not exist")
            return 1
        print("PASS: no refs.bib and no \\cite commands yet (nothing to verify)")
        return 0

    entries = parse_bib(BIB.read_text(errors="replace"))
    CACHE.mkdir(parents=True, exist_ok=True)
    failures = 0

    missing = cite_keys - set(entries)
    for k in sorted(missing):
        print(f"FAIL: \\cite{{{k}}} has no entry in refs.bib")
        failures += 1
    for k in sorted(set(entries) - cite_keys):
        print(f"WARN: bib entry '{k}' is never cited")

    for key, f in entries.items():
        title, author = f.get("title", ""), f.get("author", "")
        if not title or not author:
            print(f"FAIL: bib entry '{key}' missing title or author")
            failures += 1
            continue
        family = first_author_family(author)
        cache_file = CACHE / (hashlib.sha1(f"{norm(title)}|{family}".encode()).hexdigest() + ".json")
        if cache_file.exists():
            cached = json.loads(cache_file.read_text())
            if cached.get("resolved"):
                print(f"PASS (cached): {key} -> {cached['via']['source']}")
                continue
        result, err = None, None
        for resolver in (resolve_crossref, resolve_arxiv, resolve_s2):
            try:
                result = resolver(title, family)
                if result:
                    break
            except Exception as e:
                err = e
        if result:
            cache_file.write_text(json.dumps({"resolved": True, "key": key, "title": title, "via": result}, indent=1))
            print(f"PASS: {key} -> {result['source']} ('{result['matched_title'][:60]}')")
        else:
            if err is not None:
                print(f"FAIL: {key} — could not verify (network error: {err}). Not cached; retried next lap.")
            else:
                cache_file.write_text(json.dumps({"resolved": False, "key": key, "title": title}, indent=1))
                print(f"FAIL: {key} — no matching real paper found for '{title[:70]}' "
                      f"(first author '{family}'). Likely fabricated or mistitled.")
            failures += 1

    if failures:
        print(f"{failures} citation failure(s).")
        return 1
    print(f"PASS: all {len(entries)} bib entries resolve to real papers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
