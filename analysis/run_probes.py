#!/usr/bin/env python3
"""Tier-1 probe runner: seeded prompt generation + frozen-model inference.

Design contract (SPEC.md):
- MATCHED FAMILIES: each scenario family (target clause, distractor clause,
  filler, question) is generated WITHOUT position in its seed; the same family
  is rendered with the target clause at start / middle / end. Only the target
  moves, so position comparisons are paired.
- Distractor depth is chosen per family independently of target position. Its
  final sentence index stays fixed across the three renders, so only the
  target clause moves in a paired position comparison.
- Filler quality (relevant vs irrelevant) is balanced inside every tier.
- Tier sizes are TOKENIZER-VERIFIED: prompts are sized with llama-tokenize and
  the measured counts land in the manifest; nominal labels never reach the
  paper.
- RESUMABLE: every probe has a stable id, one output file per probe, existing
  outputs are skipped, progress prints as done/total. Output files are written
  atomically (tmp + rename) so a killed run never leaves partial outputs.
- Seeds come from zlib.crc32 of stable strings only (never Python hash()).

Usage:
  run_probes.py [--dry-run] [--limit-seconds N] [--only PREFIX]

--dry-run generates all prompts and the manifest, prints the budget estimate,
and runs no inference. --limit-seconds stops STARTING new probes after N
seconds (a partial grid resumes on the next invocation).
"""
import argparse
import hashlib
import json
import random
import re
import subprocess
import sys
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "data/models/qwen2.5-0.5b-instruct-q8_0.gguf"
CHECKSUMS = ROOT / "data/models/CHECKSUMS.txt"
PROBE_DIR = ROOT / "data/probes"
PROMPT_DIR = PROBE_DIR / "prompts"
OUT_DIR = PROBE_DIR / "out"
MANIFEST = PROBE_DIR / "manifest.json"
GRID_VERSION = "v5-fixed-competitor-position-metal"
PROBE_VERSION = "v5"

LLAMA_ARGS = ["--temp", "0", "--seed", "42", "-c", "9216", "-n", "16",
              "--no-display-prompt", "--simple-io"]

# Grid: nested families per tier (families shared across tiers so the amount
# axis reuses the same scenarios). Costs measured 2026-07-07 on this laptop.
TIERS = [
    ("t2k", 2000, 6, 14),   # (label, nominal tokens, n families, est s/probe)
    ("t4k", 4000, 5, 25),
    ("t8k", 8000, 2, 76),
]
POSITIONS = {"start": 0.05, "mid": 0.50, "end": 0.95}
FILLERS = ["rel", "irr"]
PRUNED_TIER = "t4k"          # cheap mitigation variant, small tiers only
PRUNE_MIN_OVERLAP = 2
PRUNE_FLOOR = 8              # if the rule keeps < 8 sentences, keep top-8
CONTROL_EST_SECONDS = 3      # short pruned prompt with one clause removed
SELECTOR_EST_SECONDS = 3     # short query-entity selector prompt
CLOSED_BOOK_FAMILIES = 6
SIZE_TOLERANCE = 0.05        # measured prompt within +-5% of nominal

COMPANIES = [
    "Meridian", "Halvern", "Ostrander", "Quillon", "Tessary", "Bramwick",
    "Ferrodyne", "Lucastra", "November", "Grelling", "Ashcombe", "Peltram",
    "Vandrell", "Corvess", "Malbourne", "Rydegate", "Sollertis", "Winmark",
    "Ederline", "Farrowby", "Kestrane", "Ambrell", "Thornqvist", "Delverton",
]

STOPWORDS = {
    "the", "a", "an", "of", "to", "is", "was", "are", "with", "for", "in",
    "on", "at", "by", "its", "it", "and", "or", "that", "this", "be", "as",
    "what", "which", "must", "from", "under", "into", "their", "has", "have",
}

IRRELEVANT_TEMPLATES = [
    "The {adj} river near {place} floods every spring when the snow melts.",
    "Local bakers in {place} still prepare {adj} rye loaves in wood ovens.",
    "A {adj} footpath climbs from {place} toward the old granite quarry.",
    "Astronomers observed a {adj} meteor shower above {place} last winter.",
    "The {place} museum restored a {adj} tapestry loom from the 1800s.",
    "Migrating cranes rest in the {adj} wetlands south of {place}.",
    "The {place} orchestra rehearsed a {adj} symphony in the town hall.",
    "Cyclists favor the {adj} coastal road between {place} and the ferry.",
    "A {adj} lighthouse still guides fishing boats past {place} at night.",
    "Botanists catalogued a {adj} fern species in the hills near {place}.",
]
IRR_PLACES = ["Dunmore", "Larkfell", "Seabrook", "Tarnholm", "Windmere",
              "Applecross", "Norvale", "Eastport", "Millbrae", "Cloverfield"]
IRR_ADJS = ["quiet", "narrow", "restored", "ancient", "steep", "shaded",
            "gravel", "misty", "wide", "remote"]

RELEVANT_TEMPLATES = [
    "{co} filed its quarterly procurement summary under reference {code}.",
    "The service annex for {co} lists billing schedule {code}.",
    "An internal audit note for {co} cites compliance tag {code}.",
    "Warehouse deliveries for {co} are logged against docket {code}.",
    "The onboarding packet for {co} references training module {code}.",
    "Legal archived the {co} correspondence file under label {code}.",
    "Invoices from {co} clear through payment channel {code}.",
    "The {co} maintenance addendum specifies inspection cycle {code}.",
    "Quality reviews for {co} shipments follow checklist {code}.",
    "The {co} data-sharing rider carries registry entry {code}.",
]

SYSTEM_MSG = ("You are a careful assistant. Answer with the requested code "
              "only, nothing else.")


def rng_for(tag: str) -> random.Random:
    return random.Random(zlib.crc32(tag.encode("utf-8")))


def make_code(rng: random.Random) -> str:
    letters = "".join(rng.choice("BCDFGHJKLMNPQRSTVWXZ") for _ in range(2))
    return f"{letters}-{rng.randrange(100, 999)}"


def model_sha256() -> str:
    for line in CHECKSUMS.read_text().splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[-1].endswith(MODEL.name):
            return parts[0]
    raise SystemExit(f"run_probes: {MODEL.name} not found in {CHECKSUMS}")


class Family:
    """One scenario family. Nothing here depends on target position."""

    def __init__(self, idx: int):
        rng = rng_for(f"family-{idx}")
        self.idx = idx
        picks = rng.sample(COMPANIES, 2)
        self.company, self.d_company = picks
        self.target_code = make_code(rng)
        self.distractor_code = make_code(rng)
        while self.distractor_code == self.target_code:
            self.distractor_code = make_code(rng)
        # Distractor depth: independent of target position, fixed per family.
        self.distractor_depth = rng.choice([0.25, 0.75])
        # Paraphrase design (NoLiMa-style): the QUESTION shares its surface
        # phrasing with the DISTRACTOR clause; the target clause states the
        # answer in different words, so literal matching favors the wrong code.
        self.question = (f"What is the renewal code required to extend the "
                         f"contract with {self.company}?")
        self.needle_para = (f"{self.company}'s master supply agreement "
                            f"carries the renewal identifier "
                            f"{self.target_code}.")
        self.distractor_para = (f"The renewal code required to extend the "
                                f"contract with {self.d_company} is "
                                f"{self.distractor_code}.")
        # Literal control: needle phrased exactly like the question, the
        # look-alike clause phrased obliquely.
        self.needle_lit = (f"The renewal code required to extend the "
                           f"contract with {self.company} is "
                           f"{self.target_code}.")
        self.distractor_lit = (f"{self.d_company}'s master supply agreement "
                               f"carries the renewal identifier "
                               f"{self.distractor_code}.")

    def clauses(self, style: str):
        if style == "lit":
            return self.needle_lit, self.distractor_lit
        return self.needle_para, self.distractor_para


def filler_sentences(family: Family, tier: str, kind: str, count: int):
    """Deterministic filler; seed excludes position by construction."""
    rng = rng_for(f"filler-{family.idx}-{tier}-{kind}")
    used = {family.company, family.d_company}
    out = []
    for i in range(count):
        if kind == "irr":
            t = IRRELEVANT_TEMPLATES[i % len(IRRELEVANT_TEMPLATES)]
            out.append(t.format(place=rng.choice(IRR_PLACES),
                                adj=rng.choice(IRR_ADJS)))
        else:
            co = rng.choice([c for c in COMPANIES if c not in used])
            t = RELEVANT_TEMPLATES[i % len(RELEVANT_TEMPLATES)]
            out.append(t.format(co=co, code=make_code(rng)))
    return out


def assemble(filler: list, needle: str, distractor: str,
             target_depth: float, distractor_depth: float) -> list:
    """Place both clauses into final-document slots without index shifts.

    Computing slots before filling the document prevents insertion order from
    moving the distractor when the target appears earlier. The distractor's
    final index is consequently identical in every position render of a
    family, while the filler retains its original order.
    """
    n = len(filler) + 2
    d_at = min(int(round(distractor_depth * n)), n - 1)
    t_at = min(int(round(target_depth * n)), n - 1)
    if t_at == d_at:
        t_at = t_at + 1 if t_at + 1 < n else t_at - 1
    filler_iter = iter(filler)
    doc = []
    for index in range(n):
        if index == d_at:
            doc.append(distractor)
        elif index == t_at:
            doc.append(needle)
        else:
            doc.append(next(filler_iter))
    if next(filler_iter, None) is not None:
        raise AssertionError("assemble did not consume the filler exactly")
    return doc


def build_prompt(doc_sentences, question: str) -> str:
    parts = [f"<|im_start|>system\n{SYSTEM_MSG}<|im_end|>\n<|im_start|>user\n"]
    if doc_sentences:
        parts.append("Document:\n" + " ".join(doc_sentences) + "\n\n")
    parts.append(f"Question: {question}\nAnswer with the code only.<|im_end|>"
                 f"\n<|im_start|>assistant\n")
    return "".join(parts)


def content_words(text: str):
    return {w for w in re.findall(r"[a-z]+", text.lower())
            if w not in STOPWORDS}


def prune(doc_sentences, question: str):
    """Keyword-overlap pruning: keep sentences sharing >= 2 content words
    with the question; if fewer than PRUNE_FLOOR survive, keep the top-8 by
    overlap (ties broken by original order). Original order is preserved."""
    qw = content_words(question)
    scored = [(len(qw & content_words(s)), i, s)
              for i, s in enumerate(doc_sentences)]
    kept = [(i, s) for ov, i, s in scored if ov >= PRUNE_MIN_OVERLAP]
    if len(kept) < PRUNE_FLOOR:
        best = sorted(scored, key=lambda t: (-t[0], t[1]))[:PRUNE_FLOOR]
        kept = sorted((i, s) for _, i, s in best)
    return [s for _, s in kept]


def extract_query_entity(question: str) -> str | None:
    """Extract the one-word company in the generator's exact question form.

    This deliberately narrow parser is part of the benchmark diagnostic. It
    rejects aliases, pronouns, and unseen question forms instead of pretending
    to provide general named-entity resolution.
    """
    match = re.fullmatch(
        r"What is the renewal code required to extend the contract with "
        r"([A-Z][A-Za-z]+)\?",
        question,
    )
    return match.group(1) if match else None


def exact_entity_sentences(doc_sentences, question: str):
    """Return a unique exact-name sentence, or ``None`` when unresolved."""
    entity = extract_query_entity(question)
    if entity is None:
        return None
    pattern = re.compile(rf"(?<![A-Za-z]){re.escape(entity)}(?![A-Za-z])")
    selected = [sentence for sentence in doc_sentences if pattern.search(sentence)]
    return selected if len(selected) == 1 else None


def query_entity_select(doc_sentences, question: str):
    """Apply the benchmark-specific exact-name rule, else keyword fallback."""
    selected = exact_entity_sentences(doc_sentences, question)
    return selected if selected is not None else prune(doc_sentences, question)


def deterministic_code_extract(doc_sentences, question: str) -> str | None:
    """Extract a unique code without a language model after exact-name selection.

    Returning ``None`` for ambiguity makes explicit how much of the synthetic
    task is solved by its exact-name and one-code-per-sentence construction.
    """
    selected = exact_entity_sentences(doc_sentences, question)
    if selected is None:
        return None
    codes = re.findall(r"\b[A-Z]{2}-[0-9]{3}\b", selected[0])
    return codes[0] if len(codes) == 1 else None


_TOKENIZE_CALLS = 0


def count_tokens(prompt_file: Path) -> int:
    global _TOKENIZE_CALLS
    _TOKENIZE_CALLS += 1
    res = subprocess.run(
        ["llama-tokenize", "-m", str(MODEL), "-f", str(prompt_file),
         "--show-count", "--log-disable"],
        capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit(f"llama-tokenize failed: {res.stderr[-400:]}")
    m = re.search(r"Total number of tokens:\s*(\d+)", res.stdout + res.stderr)
    if m:
        return int(m.group(1))
    # Fallback: one token per output line of the form "  123 -> '...'".
    return len(re.findall(r"^\s*\d+\s*->", res.stdout, re.M))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_atomic(path: Path, text: str):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    tmp.replace(path)


class Grid:
    """Generates every prompt, sizes tiers with the real tokenizer, and
    yields probe records in cheapest-first order."""

    def __init__(self):
        self.families = {i: Family(i) for i in
                         range(max(nf for _, _, nf, _ in TIERS))}
        self.probes = {}          # id -> record
        self._ratio = {}          # (tier, kind) -> chars per token estimate
        self._docs = {}           # scenario key -> sentence list
        # Caches from the previous manifest: deterministic generation means a
        # matching prompt sha can reuse its measured token count, and sizing
        # counts can skip the tokenizer loop entirely on resume.
        self._old_measown = {}    # prompt_sha256 -> measured tokens
        self._sizing_cache = {}   # sizing key -> filler sentence count
        old = load_manifest()
        if old:
            for rec in old.get("probes", {}).values():
                if rec.get("measured_prompt_tokens"):
                    self._old_measown[rec["prompt_sha256"]] = \
                        rec["measured_prompt_tokens"]
            self._sizing_cache = dict(old.get("meta", {})
                                      .get("sizing_counts", {}))

    def _sized_filler(self, fam, tier_label, nominal, kind, probe_id):
        """Iteratively size filler so the mid-position render measures within
        SIZE_TOLERANCE of nominal tokens. Estimates seed the loop; the real
        tokenizer decides. Returns (filler, measured_mid_tokens)."""
        cached = self._sizing_cache.get(probe_id)
        if cached:
            return filler_sentences(fam, tier_label, kind, cached), None
        ratio = self._ratio.get((tier_label, kind), 4.0)
        needle, distractor = fam.clauses("para")
        overhead = len(build_prompt([], fam.question))
        count = max(10, int((nominal * ratio - overhead) /
                            (ratio * 18)))  # ~18 tokens/sentence to start
        tmp = PROMPT_DIR / f"_sizing-{probe_id}.txt"
        measured = 0
        for _ in range(6):
            filler = filler_sentences(fam, tier_label, kind, count)
            doc = assemble(filler, needle, distractor,
                           POSITIONS["mid"], fam.distractor_depth)
            write_atomic(tmp, build_prompt(doc, fam.question))
            measured = count_tokens(tmp)
            self._ratio[(tier_label, kind)] = (
                tmp.stat().st_size / max(measured, 1))
            if abs(measured - nominal) <= SIZE_TOLERANCE * nominal:
                break
            count = max(10, int(round(count * nominal / max(measured, 1))))
        tmp.unlink(missing_ok=True)
        self._sizing_cache[probe_id] = count
        return filler_sentences(fam, tier_label, kind, count), measured

    def _add(self, pid, prompt, est_s, **fields):
        pf = PROMPT_DIR / f"{pid}.txt"
        if not pf.exists() or pf.read_text() != prompt:
            write_atomic(pf, prompt)
        rec = dict(id=pid, prompt_file=str(pf.relative_to(ROOT)),
                   output_file=str((OUT_DIR / f"{pid}.txt")
                                   .relative_to(ROOT)),
                   prompt_sha256=sha256_text(prompt),
                   est_seconds=est_s, **fields)
        self.probes[pid] = rec

    def generate(self):
        PROMPT_DIR.mkdir(parents=True, exist_ok=True)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        for tier_label, nominal, n_fam, est_s in TIERS:
            for fi in range(n_fam):
                fam = self.families[fi]
                for kind in FILLERS:
                    key = f"{tier_label}-f{fi}-{kind}"
                    filler, _ = self._sized_filler(
                        fam, tier_label, nominal, kind, key)
                    for pos, depth in POSITIONS.items():
                        needle, distractor = fam.clauses("para")
                        doc = assemble(filler, needle, distractor, depth,
                                       fam.distractor_depth)
                        pid = (f"{tier_label}-f{fi}-{pos}-{kind}-full-"
                               f"{PROBE_VERSION}")
                        prompt = build_prompt(doc, fam.question)
                        self._docs[pid] = doc
                        self._add(pid, prompt, est_s, family=fi,
                                  tier=tier_label, nominal_tokens=nominal,
                                  style="para", filler=kind, position=pos,
                                  variant="full",
                                  target_sentence_index=doc.index(needle),
                                  distractor_sentence_index=doc.index(distractor),
                                  target_code=fam.target_code,
                                  distractor_code=fam.distractor_code)
                        if tier_label == PRUNED_TIER:
                            pdoc = prune(doc, fam.question)
                            target_retained = needle in pdoc
                            distractor_retained = distractor in pdoc
                            ppid = (f"{tier_label}-f{fi}-{pos}-{kind}-pruned-"
                                    f"{PROBE_VERSION}")
                            self._add(ppid, build_prompt(pdoc, fam.question),
                                      6, family=fi, tier=tier_label,
                                      nominal_tokens=nominal, style="para",
                                      filler=kind, position=pos,
                                      variant="pruned",
                                      target_retained=target_retained,
                                      distractor_retained=distractor_retained,
                                      target_code=fam.target_code,
                                      distractor_code=fam.distractor_code)
                            # Paired diagnostic: the lexical filter retains
                            # both clauses in this frozen grid. Remove only
                            # its retained look-alike clause, leaving the
                            # answer and every other selected sentence fixed.
                            if not target_retained or not distractor_retained:
                                raise RuntimeError(
                                    f"{ppid}: pruning-control contract failed")
                            cdoc = [s for s in pdoc if s != distractor]
                            cpid = (f"{tier_label}-f{fi}-{pos}-{kind}-"
                                    f"prunednodecoy-{PROBE_VERSION}")
                            self._add(
                                cpid, build_prompt(cdoc, fam.question),
                                CONTROL_EST_SECONDS, family=fi,
                                tier=tier_label, nominal_tokens=nominal,
                                style="para", filler=kind, position=pos,
                                variant="prunednodecoy",
                                target_retained=needle in cdoc,
                                distractor_retained=distractor in cdoc,
                                target_code=fam.target_code,
                                distractor_code=fam.distractor_code)
                            # Deployable comparison: extract the company named
                            # in the visible question and retain sentences that
                            # mention it. Unlike the decoy-removal diagnostic,
                            # this selector never reads the hidden answer label.
                            edoc = query_entity_select(doc, fam.question)
                            epid = (f"{tier_label}-f{fi}-{pos}-{kind}-"
                                    f"entitypruned-{PROBE_VERSION}")
                            self._add(
                                epid, build_prompt(edoc, fam.question),
                                SELECTOR_EST_SECONDS, family=fi,
                                tier=tier_label, nominal_tokens=nominal,
                                style="para", filler=kind, position=pos,
                                variant="entitypruned",
                                target_retained=needle in edoc,
                                distractor_retained=distractor in edoc,
                                selected_sentence_count=len(edoc),
                                target_code=fam.target_code,
                                distractor_code=fam.distractor_code)
        # Literal control: smallest tier, hardest position, irrelevant
        # filler. Reuses the paraphrase cell's sizing key, so the filler is
        # IDENTICAL to the matching paraphrase scenario; the two probes
        # differ only in how the needle and distractor clauses are phrased.
        tier_label, nominal, n_fam, est_s = TIERS[0]
        for fi in range(n_fam):
            fam = self.families[fi]
            filler, _ = self._sized_filler(fam, tier_label, nominal, "irr",
                                           f"{tier_label}-f{fi}-irr")
            needle, distractor = fam.clauses("lit")
            doc = assemble(filler, needle, distractor, POSITIONS["mid"],
                           fam.distractor_depth)
            self._add(f"{tier_label}-f{fi}-mid-irr-lit-{PROBE_VERSION}",
                      build_prompt(doc, fam.question), est_s, family=fi,
                      tier=tier_label, nominal_tokens=nominal, style="lit",
                      filler="irr", position="mid", variant="full",
                      target_sentence_index=doc.index(needle),
                      distractor_sentence_index=doc.index(distractor),
                      target_code=fam.target_code,
                      distractor_code=fam.distractor_code)
        # Closed-book baseline: question only, no document.
        for fi in range(CLOSED_BOOK_FAMILIES):
            fam = self.families[fi]
            self._add(f"cb-f{fi}", build_prompt([], fam.question), 3,
                      family=fi, tier="cb", nominal_tokens=0, style="para",
                      filler="none", position="none", variant="closedbook",
                      target_code=fam.target_code,
                      distractor_code=fam.distractor_code)

        # A position pair is valid only if the competitor occupies the same
        # final-document slot in all three versions of a scenario.
        for tier_label, _, n_fam, _ in TIERS:
            for fi in range(n_fam):
                for kind in FILLERS:
                    ids = [f"{tier_label}-f{fi}-{pos}-{kind}-full-"
                           f"{PROBE_VERSION}" for pos in POSITIONS]
                    distractor_indices = {
                        self.probes[pid]["distractor_sentence_index"]
                        for pid in ids
                    }
                    if len(distractor_indices) != 1:
                        raise AssertionError(
                            f"competitor moved across position renders: {ids}")

    def measure_all(self):
        for rec in self.probes.values():
            if rec.get("measured_prompt_tokens"):
                continue
            cached = self._old_measown.get(rec["prompt_sha256"])
            rec["measured_prompt_tokens"] = cached or count_tokens(
                ROOT / rec["prompt_file"])

    def order(self):
        return sorted(self.probes.values(), key=lambda r: (r["est_seconds"],
                                                           r["id"]))


def load_manifest():
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text())
    return None


def save_manifest(grid: Grid):
    done = {pid: (ROOT / rec["output_file"]).exists()
            for pid, rec in grid.probes.items()}
    for pid, rec in grid.probes.items():
        rec["status"] = "done" if done[pid] else "pending"
    manifest = {
        "meta": {
            "generated_by": "analysis/run_probes.py",
            "model_file": str(MODEL.relative_to(ROOT)),
            "model_sha256": model_sha256(),
            "llama_command": "llama-completion -m <model> -f <prompt> "
                             + " ".join(LLAMA_ARGS),
            "grid_version": GRID_VERSION,
            "position_control": (
                "target clause moves among fixed final-document slots; "
                "competitor final sentence index is invariant within each "
                "tier-family-filler triplet"
            ),
            "total_probes": len(grid.probes),
            "done_probes": sum(done.values()),
            "manifest_complete": all(done.values()),
            "sizing_counts": dict(sorted(grid._sizing_cache.items())),
        },
        "probes": {pid: grid.probes[pid] for pid in sorted(grid.probes)},
    }
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    write_atomic(MANIFEST, json.dumps(manifest, indent=1, sort_keys=True))
    return manifest


def run_probe(rec) -> float:
    t0 = time.time()
    res = subprocess.run(
        ["llama-completion", "-m", str(MODEL), "-f",
         str(ROOT / rec["prompt_file"])] + LLAMA_ARGS,
        capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"{rec['id']}: llama-completion failed: "
                           f"{res.stderr[-400:]}")
    out = ROOT / rec["output_file"]
    tmp = out.with_suffix(".tmp")
    tmp.write_text(res.stdout)
    tmp.replace(out)
    return time.time() - t0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit-seconds", type=float, default=None)
    ap.add_argument("--only", default=None)
    args = ap.parse_args()

    t_start = time.time()
    grid = Grid()
    print("run_probes: generating and sizing prompts "
          "(tokenizer-verified)...", flush=True)
    grid.generate()
    grid.measure_all()
    manifest = save_manifest(grid)
    total = manifest["meta"]["total_probes"]
    done0 = manifest["meta"]["done_probes"]
    est_remaining = sum(r["est_seconds"] for r in grid.probes.values()
                        if not (ROOT / r["output_file"]).exists())
    print(f"run_probes: {total} probes in grid, {done0} done, "
          f"~{est_remaining/60:.1f} min inference remaining "
          f"({_TOKENIZE_CALLS} tokenize calls, "
          f"{time.time()-t_start:.0f}s generation)", flush=True)
    if args.dry_run:
        return 0

    done = done0
    for rec in grid.order():
        if args.only and not rec["id"].startswith(args.only):
            continue
        if (ROOT / rec["output_file"]).exists():
            continue
        if (args.limit_seconds is not None
                and time.time() - t_start > args.limit_seconds):
            print(f"run_probes: time limit reached with {done}/{total} done; "
                  f"rerun to resume", flush=True)
            save_manifest(grid)
            return 0
        secs = run_probe(rec)
        done += 1
        print(f"  [{done}/{total}] {rec['id']} "
              f"({rec['measured_prompt_tokens']} tok, {secs:.1f}s)",
              flush=True)
        save_manifest(grid)
    save_manifest(grid)
    print(f"run_probes: complete, {done}/{total} outputs present", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
