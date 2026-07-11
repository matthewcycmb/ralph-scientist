#!/usr/bin/env python3
"""Gate: results.json exists, follows the contract, and passes sanity bounds.

Reproducible is not the same as correct — this gate catches the shallow bugs
that produce absurd-but-reproducible numbers. Contract: analysis/RESULTS_SCHEMA.md.
"""
import json
import math
import re
import sys
from pathlib import Path

RESULTS = Path("results.json")
UNIT_BOUNDS = {
    "pct": (0.0, 100.0),
    "corr": (-1.0, 1.0),
    "pvalue": (0.0, 1.0),
}
MIN_SAMPLE = 100  # sampleSize = total scored probes; SPEC's grid is ~200 (was 500 for NLSY respondents)


def fail(msg):
    print(f"FAIL: {msg}")
    return 1


def main() -> int:
    if not RESULTS.exists():
        return fail("results.json does not exist yet (run `make results`)")
    try:
        data = json.loads(RESULTS.read_text())
    except json.JSONDecodeError as e:
        return fail(f"results.json is not valid JSON: {e}")

    values = data.get("values")
    if not isinstance(values, dict) or not values:
        return fail("results.json must contain a non-empty 'values' object")
    meta = data.get("meta", {})
    if not meta.get("generated_by"):
        return fail("results.json 'meta.generated_by' missing (which script wrote this?)")

    errors = 0
    if "sampleSize" not in values:
        print("FAIL: reserved key 'sampleSize' missing — every analysis must report its n")
        errors += 1

    for name, entry in values.items():
        if not re.fullmatch(r"[a-zA-Z]+", name):
            print(f"FAIL: key '{name}' must be letters only (it becomes a LaTeX macro name)")
            errors += 1
            continue
        if not isinstance(entry, dict) or "value" not in entry:
            print(f"FAIL: '{name}' must be an object with a 'value' field")
            errors += 1
            continue
        v = entry["value"]
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v):
            print(f"FAIL: '{name}'.value must be a finite number (got {v!r})")
            errors += 1
            continue
        if not entry.get("desc") or not entry.get("script"):
            print(f"FAIL: '{name}' missing 'desc' or 'script' (provenance is mandatory)")
            errors += 1
        unit = entry.get("unit", "raw")
        if unit in UNIT_BOUNDS:
            lo, hi = UNIT_BOUNDS[unit]
            if not (lo <= v <= hi):
                print(f"FAIL: '{name}' unit '{unit}' out of bounds: {v} not in [{lo}, {hi}]")
                errors += 1
        if name == "sampleSize" and v < MIN_SAMPLE:
            print(f"FAIL: sampleSize {v} < {MIN_SAMPLE} — check filters/joins for a bug")
            errors += 1

    if errors:
        print(f"{errors} sanity failure(s) in results.json")
        return 1
    print(f"PASS: results.json sane ({len(values)} values, n={values['sampleSize']['value']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
