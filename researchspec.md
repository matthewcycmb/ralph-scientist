# Autonomous Verifiable Research Loop — One-Page Specification

## Mission

Build an unattended agent system that produces a small, defensible research paper within a fixed time budget. The system must design and run experiments, analyze results, write the paper, review its own work, and preserve a verified submission at every successful stage.

The system optimizes for traceability, scientific honesty, reproducibility, and clear professional writing, not merely for completing a paper.

## Research contract

- **Question:** `[INSERT A NARROW, MEASURABLE RESEARCH QUESTION]`
- **Subject/data:** `[FROZEN MODEL, DATASET, OR SYSTEM UNDER TEST]`
- **Primary outcomes:** `[EXACT METRICS]`
- **Experimental factors:** `[VARIABLES TO CHANGE]`
- **Required comparisons:** Use matched or paired cases wherever a causal-sounding comparison is intended.
- **Scope:** Findings describe only the tested subject, data, conditions, and metrics.
- **Budget:** The complete experiment must finish within `[TIME/COST LIMIT]`.
- **Reproducibility:** Fixed inputs, stable seeds, deterministic scoring, resumable execution, and checksummed artifacts are mandatory.

A partial experiment is legitimate work in progress. It must be marked incomplete and may not be presented as a final result.

## System model

The repository is the system's memory. Every worker starts without conversational memory and reads:

- `SPEC.md`: immutable research constitution.
- `TODO.md`: prioritized shared work queue.
- `VERIFY.log`: latest deterministic failures.
- `EDITORIAL.md`: current thesis and editorial direction.
- Git history: permanent record of completed laps.

Each worker performs exactly one highest-leverage task, updates the shared memory, and exits without committing.

## Roles

1. **Worker:** Designs experiments, runs analysis, or writes the paper. Creative but untrusted.
2. **Verifier:** Runs protected deterministic checks outside the worker.
3. **Reviewer:** Critiques only complete, verified papers; traces claims, citations, and numbers.
4. **Editor:** Decides the paper's honest thesis and reprioritizes work around reviewer objections.
5. **Prose editor:** Improves clarity and professional register without changing claims, numbers, tables, or citations.
6. **Orchestrator:** Controls timeouts, commits, tags, retries, monitoring, and recovery.

No role may silently perform another role's function.

## Iteration lifecycle

```text
Fresh worker
→ one task
→ restore protected files after tampering
→ deterministic gates
→ commit exact verified checkpoint
→ create green fallback tag
→ review if first green paper or review cadence is due
→ promote checkpoint to paper tag if review threshold passes
→ editor and prose pass
→ commit follow-up changes
→ next worker gates those changes
```

The checkpoint must be committed before tagging. A reviewer timeout must never prevent an already verified fallback from being saved.

## Evidence pipeline

```text
Frozen inputs
→ raw experiment artifacts
→ deterministic analysis
→ results.json
→ generated paper values
→ compiled PDF
```

Every reported result must trace through this chain. Fixed model or dataset metadata should come from protected macros or manifests. Analysis code and raw artifacts remain publicly inspectable.

## Acceptance gates

A checkpoint is verified only when all applicable gates pass:

- Frozen inputs match committed checksums.
- Citations resolve to real sources and cited claims are supported.
- Reported numeric literals come from generated result macros.
- Re-running analysis reproduces `results.json` and paper values exactly.
- Results satisfy schema, provenance, bounds, completeness, and sample-size requirements.
- Writing passes professional-style checks.
- The paper compiles, meets the page limit, and has no broken headers or overflowing displays.

Deterministic gates establish integrity and reproducibility. They do not prove scientific correctness; the reviewer must inspect experimental design, scoring code, and claim size.

## Paper standard

The paper must:

- State a narrow question and answer it directly.
- Report denominators and uncertainty for every main estimate.
- Separate supported findings, null results, and unresolved questions.
- Use matched comparisons and avoid causal language for unmatched observations.
- Name the exact frozen inputs and rerun procedure.
- Include honest limitations.
- Use concise professional prose: claim, evidence, necessary qualification.
- Avoid jargon, filler, casual wording, repetitive templates, unnecessary definitions, and display bloat.

Readable does not mean childish. Write for a technically literate reader outside the immediate subfield.

## Ratchet and termination

- Every green checkpoint receives a fallback tag.
- A reviewed paper receives a version tag only if all gates pass and its fixed-rubric score meets or exceeds the threshold.
- The same review may promote only one checkpoint.
- Later failures cannot invalidate earlier verified tags.
- At the deadline, submit the highest reviewed tag; otherwise submit the highest green fallback.
- Preserve failed attempts and reviewer criticism as part of the research record.

## Operations

Provide one launcher that performs preflight checks, starts the loop, launches a local dashboard, starts external telemetry, records process IDs, and verifies service health. The loop must refuse to start from a dirty working tree and must support restart from Git without losing research state.
