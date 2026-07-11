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
ALLOWED_UNITS = {"pct", "corr", "pvalue", "count", "tokens", "seconds", "raw", "usd"}
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
    generated_by = Path(str(meta.get("generated_by", "")))
    if generated_by.is_absolute() or generated_by.suffix != ".py" or not generated_by.is_file():
        return fail("results.json 'meta.generated_by' must name an existing repository Python script")

    errors = 0
    if "data/probes" in str(meta.get("data", "")):
        if meta.get("manifest_complete") is not True:
            print("FAIL: primary experiment manifest is not complete")
            errors += 1
        if meta.get("missing_probe_count") != 0:
            print("FAIL: primary experiment must report meta.missing_probe_count = 0 before acceptance")
            errors += 1
        model_file = meta.get("model_file")
        model_sha = meta.get("model_sha256")
        if not isinstance(model_file, str) or not Path(model_file).is_file():
            print("FAIL: primary experiment meta.model_file must name the existing frozen model")
            errors += 1
        else:
            checksum_file = Path("data/models/CHECKSUMS.txt")
            declared = {}
            if checksum_file.is_file():
                for line in checksum_file.read_text().splitlines():
                    parts = line.split()
                    if len(parts) >= 2:
                        declared[parts[-1]] = parts[0]
            expected_sha = declared.get(Path(model_file).name)
            if not expected_sha or model_sha != expected_sha:
                print("FAIL: primary experiment meta.model_sha256 does not match the committed model manifest")
                errors += 1
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
        if not isinstance(entry.get("desc"), str) or not entry.get("desc"):
            print(f"FAIL: '{name}' missing non-empty 'desc' (provenance is mandatory)")
            errors += 1
        script = entry.get("script")
        if not isinstance(script, str) or not script:
            print(f"FAIL: '{name}' missing 'desc' or 'script' (provenance is mandatory)")
            errors += 1
        else:
            script_path = Path(script)
            if script_path.is_absolute() or script_path.suffix != ".py" or not script_path.is_file():
                print(f"FAIL: '{name}'.script must name an existing repository Python script (got {script!r})")
                errors += 1
        unit = entry.get("unit", "raw")
        if unit not in ALLOWED_UNITS:
            print(f"FAIL: '{name}' has unknown unit {unit!r}; allowed: {sorted(ALLOWED_UNITS)}")
            errors += 1
            continue
        if unit in UNIT_BOUNDS:
            lo, hi = UNIT_BOUNDS[unit]
            if not (lo <= v <= hi):
                print(f"FAIL: '{name}' unit '{unit}' out of bounds: {v} not in [{lo}, {hi}]")
                errors += 1
        if unit == "count" and (not isinstance(v, int) or v < 0):
            print(f"FAIL: '{name}' unit 'count' requires a non-negative integer (got {v!r})")
            errors += 1
        if unit in {"tokens", "seconds"} and v < 0:
            print(f"FAIL: '{name}' unit '{unit}' cannot be negative (got {v!r})")
            errors += 1
        if name == "sampleSize":
            if unit != "count":
                print("FAIL: sampleSize must use unit 'count'")
                errors += 1
            if v < MIN_SAMPLE:
                print(f"FAIL: sampleSize {v} < {MIN_SAMPLE} — check filters/joins for a bug")
                errors += 1
        fmt = entry.get("fmt")
        if fmt is not None:
            if not isinstance(fmt, str):
                print(f"FAIL: '{name}'.fmt must be a Python format string")
                errors += 1
            else:
                try:
                    format(v, fmt)
                except (ValueError, TypeError) as exc:
                    print(f"FAIL: '{name}'.fmt is invalid for its value: {exc}")
                    errors += 1

    if errors:
        print(f"{errors} sanity failure(s) in results.json")
        return 1
    print(f"PASS: results.json sane ({len(values)} values, n={values['sampleSize']['value']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
