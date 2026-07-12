#!/usr/bin/env python3
"""Score frozen probe outputs and build the paper's numeric result registry.

This is the cheap tier of the pipeline.  It reads only the probe manifest and
one raw output file per completed probe.  It never reads prompts or invokes the
model.  Incomplete manifests are resumable: missing cells are reported in
metadata and excluded from every aggregate.

Scoring rules
-------------
llama-completion appends a fixed ``> EOF by user`` transport trailer.  We
remove that trailer and surrounding whitespace before scoring.  A response is
code-only compliant when the remaining text is exactly one code of the form
``AA-000``.  Normalized accuracy requires the target code to occur and the
distractor code not to occur; this deliberately gives credit to an otherwise
correct response with extra words.  A distractor capture reverses those two
conditions.  A response is invalid when it contains both expected codes or
neither.  Extra-token responses contain exactly one expected code but are not
code-only compliant.
"""
import json
import math
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data/probes/manifest.json"
RESULTS = ROOT / "results.json"
SCRIPT = "analysis/run_all.py"
CODE_RE = re.compile(r"(?<![A-Z0-9])[A-Z]{2}-[0-9]{3}(?![A-Z0-9])")
EOF_RE = re.compile(r"(?:\r?\n)?\s*> EOF by user[\s\S]*\Z")
Z = 1.96


def clean_output(raw: str) -> str:
    """Remove llama.cpp's transport trailer, not model-generated prose."""
    return EOF_RE.sub("", raw).strip()


def score_record(rec: dict, raw: str) -> dict:
    answer = clean_output(raw)
    target = rec["target_code"]
    distractor = rec["distractor_code"]
    target_present = re.search(
        rf"(?<![A-Z0-9]){re.escape(target)}(?![A-Z0-9])", answer) is not None
    distractor_present = re.search(
        rf"(?<![A-Z0-9]){re.escape(distractor)}(?![A-Z0-9])", answer) is not None
    code_only = CODE_RE.fullmatch(answer) is not None
    return {
        **rec,
        "answer": answer,
        "accurate": target_present and not distractor_present,
        "exact_target": answer == target,
        "code_only": code_only,
        "distractor_capture": distractor_present and not target_present,
        "invalid": target_present == distractor_present,
        "extra_tokens": (target_present != distractor_present) and not code_only,
    }


def pct(successes: int, n: int) -> float:
    return 100.0 * successes / n if n else 0.0


def wilson(successes: int, n: int) -> tuple:
    """Two-sided Wilson score interval using the fixed normal critical value."""
    if not n:
        return 0.0, 0.0
    p = successes / n
    denom = 1.0 + Z * Z / n
    centre = (p + Z * Z / (2.0 * n)) / denom
    radius = (Z / denom) * math.sqrt(
        p * (1.0 - p) / n + Z * Z / (4.0 * n * n))
    return 100.0 * max(0.0, centre - radius), 100.0 * min(1.0, centre + radius)


def main() -> int:
    if not MANIFEST.is_file():
        print("run_all: data/probes/manifest.json is missing", file=sys.stderr)
        return 1
    manifest = json.loads(MANIFEST.read_text())
    meta = manifest.get("meta", {})
    records = manifest.get("probes", {})
    scored = []
    missing = []
    for probe_id in sorted(records):
        rec = records[probe_id]
        output = ROOT / rec["output_file"]
        if rec.get("status") != "done" or not output.is_file():
            missing.append(probe_id)
            continue
        scored.append(score_record(rec, output.read_text()))

    values = {}

    def add(name, value, unit, desc, fmt=None):
        entry = {"value": value, "unit": unit, "desc": desc, "script": SCRIPT}
        if fmt is not None:
            entry["fmt"] = fmt
        values[name] = entry

    def add_accuracy(prefix, rows, desc):
        n = len(rows)
        successes = sum(r["accurate"] for r in rows)
        low, high = wilson(successes, n)
        add(prefix + "Count", n, "count", f"probe count for {desc}")
        add(prefix + "Accuracy", pct(successes, n), "pct", desc, ".1f")
        add(prefix + "AccuracyLow", low, "pct",
            f"Wilson lower confidence bound for {desc}", ".1f")
        add(prefix + "AccuracyHigh", high, "pct",
            f"Wilson upper confidence bound for {desc}", ".1f")

    def add_binary_rate(prefix, rows, field, desc):
        n = len(rows)
        successes = sum(r[field] for r in rows)
        low, high = wilson(successes, n)
        add(prefix + "Count", successes, "count", f"count of {desc}")
        add(prefix + "Rate", pct(successes, n), "pct", desc, ".1f")
        add(prefix + "RateLow", low, "pct",
            f"Wilson lower confidence bound for {desc}", ".1f")
        add(prefix + "RateHigh", high, "pct",
            f"Wilson upper confidence bound for {desc}", ".1f")

    def keyed(rows, fields):
        return {tuple(r[f] for f in fields): r for r in rows}

    def add_paired(prefix, left, right, key_fields, left_label, right_label):
        lm = keyed(left, key_fields)
        rm = keyed(right, key_fields)
        keys = sorted(set(lm) & set(rm))
        wins = sum((not lm[k]["accurate"]) and rm[k]["accurate"] for k in keys)
        losses = sum(lm[k]["accurate"] and (not rm[k]["accurate"]) for k in keys)
        ties = len(keys) - wins - losses
        delta = pct(sum(rm[k]["accurate"] for k in keys), len(keys)) - pct(
            sum(lm[k]["accurate"] for k in keys), len(keys))
        comparison = f"paired {right_label} minus {left_label} comparison"
        add(prefix + "Denominator", len(keys), "count", f"matched pairs in {comparison}")
        add(prefix + "Wins", wins, "count", f"accuracy gains in {comparison}")
        add(prefix + "Losses", losses, "count", f"accuracy losses in {comparison}")
        add(prefix + "Ties", ties, "count", f"accuracy ties in {comparison}")
        add(prefix + "Change", delta, "raw",
            f"accuracy change in percentage points for {comparison}", ".1f")

    add("sampleSize", len(scored), "count", "total completed probes scored")
    add("manifestProbeCount", len(records), "count", "total probes in the manifest")
    add("missingProbeCount", len(missing), "count", "manifest probes without completed raw outputs")
    add("confidenceLevel", 95.0, "pct", "nominal level of every Wilson confidence interval", ".0f")
    add("cpuBudgetMinutes", 45, "count", "full clean-room probe budget in minutes")

    full = [r for r in scored if r["variant"] == "full" and r["style"] == "para"]
    tier_words = {"t2k": "Two", "t4k": "Four", "t8k": "Eight"}
    for tier, word in tier_words.items():
        rows = [r for r in full if r["tier"] == tier]
        if not rows:
            continue
        mean_tokens = sum(r["measured_prompt_tokens"] for r in rows) / len(rows)
        add(f"tier{word}Tokens", mean_tokens, "tokens",
            f"mean tokenizer-measured prompt length in the {tier} full-context tier", ".0f")
        add_accuracy(f"tier{word}", rows,
                     f"normalized full-context accuracy in the {tier} tier")

        # Position estimates share the same family/filler scenarios within a tier.
        by_position = {}
        for position in ("start", "mid", "end"):
            pos_word = {"start": "Start", "mid": "Middle", "end": "End"}[position]
            pos_rows = [r for r in rows if r["position"] == position]
            by_position[position] = pos_rows
            add_accuracy(f"position{word}{pos_word}", pos_rows,
                         f"normalized accuracy with the target at {position} in the {tier} tier")
        add_paired(f"position{word}StartMiddle", by_position["start"],
                   by_position["mid"], ("family", "filler"), "start", "middle")
        add_paired(f"position{word}MiddleEnd", by_position["mid"],
                   by_position["end"], ("family", "filler"), "middle", "end")
        add_paired(f"position{word}StartEnd", by_position["start"],
                   by_position["end"], ("family", "filler"), "start", "end")

        # Filler comparisons match family, position, tier, style, and wording.
        rel = [r for r in rows if r["filler"] == "rel"]
        irr = [r for r in rows if r["filler"] == "irr"]
        add_accuracy(f"quality{word}Relevant", rel,
                     f"normalized accuracy with relevant filler in the {tier} tier")
        add_accuracy(f"quality{word}Irrelevant", irr,
                     f"normalized accuracy with irrelevant filler in the {tier} tier")
        add_paired(f"quality{word}Relevant", irr, rel,
                   ("family", "position"), "irrelevant filler", "relevant filler")

    # Amount estimates use only families present at all three tiers.  Each cell
    # is matched on family, filler, position, style, and question wording.
    tier_maps = {tier: keyed([r for r in full if r["tier"] == tier],
                             ("family", "filler", "position"))
                 for tier in tier_words}
    shared_keys = sorted(set.intersection(*(set(m) for m in tier_maps.values())))
    shared = {tier: [tier_maps[tier][k] for k in shared_keys] for tier in tier_words}
    for tier, word in tier_words.items():
        add_accuracy(f"amountShared{word}", shared[tier],
                     f"normalized accuracy in the {tier} tier for families shared across all tiers")
    add_paired("amountSharedTwoFour", shared["t2k"], shared["t4k"],
               ("family", "filler", "position"), "t2k", "t4k")
    add_paired("amountSharedFourEight", shared["t4k"], shared["t8k"],
               ("family", "filler", "position"), "t4k", "t8k")
    add_paired("amountSharedTwoEight", shared["t2k"], shared["t8k"],
               ("family", "filler", "position"), "t2k", "t8k")

    # The mitigation denominator is the exact intersection of full and pruned
    # t4k scenarios, never the difference between unmatched aggregate rates.
    full_four = [r for r in full if r["tier"] == "t4k"]
    pruned = [r for r in scored if r["tier"] == "t4k" and r["variant"] == "pruned"]
    pair_fields = ("family", "filler", "position", "style")
    fm, pm = keyed(full_four, pair_fields), keyed(pruned, pair_fields)
    prune_keys = sorted(set(fm) & set(pm))
    paired_full = [fm[k] for k in prune_keys]
    paired_pruned = [pm[k] for k in prune_keys]
    add_accuracy("pruningFull", paired_full,
                 "normalized full-context accuracy in matched pruning scenarios")
    add_accuracy("pruningPruned", paired_pruned,
                 "normalized pruned-context accuracy in matched pruning scenarios")
    add_paired("pruning", paired_full, paired_pruned, pair_fields,
               "full context", "keyword-pruned context")

    literal = [r for r in scored if r["style"] == "lit"]
    para_controls = [r for r in full if r["tier"] == "t2k" and
                     r["position"] == "mid" and r["filler"] == "irr"]
    add_accuracy("literalControl", literal, "normalized literal-control accuracy")
    add_accuracy("paraphraseControl", para_controls,
                 "normalized accuracy in the matched paraphrase-control scenarios")
    add_paired("literalControl", para_controls, literal, ("family",),
               "paraphrase wording", "literal wording")
    closed = [r for r in scored if r["variant"] == "closedbook"]
    add_accuracy("closedBook", closed, "normalized closed-book accuracy")

    add_accuracy("overall", scored, "normalized accuracy across all completed probes")
    add_binary_rate("exactTarget", scored, "exact_target",
                    "responses containing exactly the target code and nothing else")
    add_binary_rate("exactOutputCompliance", scored, "code_only",
                    "responses containing exactly one code and nothing else")
    add_binary_rate("distractorCapture", scored, "distractor_capture",
                    "responses containing the distractor code but not the target code")
    add_binary_rate("invalidOutput", scored, "invalid",
                    "responses containing both expected codes or neither expected code")
    add_binary_rate("extraTokenOutput", scored, "extra_tokens",
                    "responses containing one expected code plus extra output")

    result = {
        "meta": {
            "generated_by": SCRIPT,
            "data": "data/probes/ (raw outputs of the frozen model in data/models/)",
            "model_file": meta.get("model_file"),
            "model_sha256": meta.get("model_sha256"),
            "manifest_complete": bool(meta.get("manifest_complete")) and not missing,
            "missing_probe_count": len(missing),
            "scoring": {
                "transport_cleanup": "strip the fixed llama.cpp EOF trailer and surrounding whitespace",
                "exact_output_compliance": "cleaned output is exactly one AA-000 code",
                "normalized_accuracy": "target code present and distractor code absent",
                "distractor_capture": "distractor code present and target code absent",
                "invalid_output": "both expected codes or neither expected code present",
                "extra_token_output": "exactly one expected code present but output is not code-only",
            },
            "missing_probe_ids": missing,
        },
        "values": dict(sorted(values.items())),
    }
    tmp = RESULTS.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    tmp.replace(RESULTS)
    print(f"run_all: scored {len(scored)}/{len(records)} probes; "
          f"wrote {len(values)} values to results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
