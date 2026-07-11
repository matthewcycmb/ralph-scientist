# Paper Outline

Working rule: draft from this outline into `paper/main.tex`; every empirical quantity
must appear through a macro generated in `paper/values.tex`.

## Abstract

- State the predictive question: whether high-school GPA forecasts household net worth
  around age thirty after accounting for family starting wealth.
- Name the dataset as the frozen NLSY97 public-use extract with transcript GPA and
  age-thirty household net worth.
- Summarize the three analyses using only macro names: `\sampleSize`,
  `\gpaWealthCorr`, `\topBottomMedianGap`, `\parentControlledGpaCoef`, and
  `\parentControlSampleSize`.
- Close with the main caveat: observational household-wealth evidence, not causal
  individual wealth evidence.

## Introduction

- Open with the practical claim people make about grades: grades are often treated as
  early signals of later economic position.
- Define the paper as a small replication-and-extension study: prior work links high
  school GPA to earnings, while this paper tests household net worth as the outcome and
  includes parental net worth as the starting-position control.
- List the research questions in prose:
  - GPA association with age-thirty household net worth.
  - Median net-worth gap between top and bottom GPA quintiles.
  - Whether the GPA association remains after parental net worth is included.
- Preview the empirical posture: simple, transparent, predictive statistics from one
  frozen public-use extract.

## Related Work

- Use `french2015gpa` for the closest grades-to-earnings precedent.
- Use `zagorsky2007smart` to motivate wealth as a distinct outcome from income.
- Use `chetty2014land` for the intergenerational-mobility framing and to separate this
  paper's modest individual-level prediction exercise from broader mobility mapping.
- Keep the section short; the contribution is the outcome/control combination, not a new
  theory of mobility.

## Data

- Describe NLSY97 as a US cohort study with public-use data, high-school transcript
  variables, household net worth around age thirty, and parent-reported household net
  worth near baseline.
- Cite the frozen extract provenance in `data/cache/nlsy97/PROVENANCE.md` without adding
  numeric prose to LaTeX unless a macro exists.
- Explain the GPA variable:
  - Prefer grade-nine transcript GPA from the birth-year academic-year mapping.
  - Fall back to overall transcript GPA when the mapped grade-nine value is missing.
  - Report the grade-nine share with `\gradeNineGpaShare`.
- Explain filters:
  - Keep non-problem transcripts via `TRANS_PROBFLAG`.
  - Treat NLS negative missing-money codes as missing, while preserving real debt values.
  - Require GPA and age-thirty household net worth.
- Report final analytic sample with `\sampleSize`.

## Method

- RQ association: Spearman correlation between GPA and age-thirty household net worth.
- Quintile gap: rank respondents into GPA quintiles, compare median household net worth in
  the top and bottom quintiles.
- Parent-control model: HC3 robust OLS of age-thirty household net worth on GPA and
  parental net worth; report `\parentControlSampleSize`, `\parentControlledGpaCoef`, and
  `\parentControlledGpaPvalue`.
- State explicitly that the analysis is predictive and descriptive, not causal.

## Results

- Table A: core estimates.
  - Rows: analytic sample, Spearman GPA/net-worth correlation, bottom-quintile median,
    top-quintile median, top-minus-bottom median gap.
  - Macros: `\sampleSize`, `\gpaWealthCorr`, `\gpaWealthCorrPvalue`,
    `\bottomQuintMedian`, `\topQuintMedian`, `\topBottomMedianGap`.
- Table B: parental-wealth-control regression summary.
  - Rows: regression sample, GPA coefficient, GPA p-value.
  - Macros: `\parentControlSampleSize`, `\parentControlledGpaCoef`,
    `\parentControlledGpaPvalue`.
- Interpret cautiously:
  - GPA has a positive monotonic association with household net worth.
  - Top-quintile students have higher median household net worth than bottom-quintile
    students.
  - The GPA coefficient remains positive after adding parental net worth, but this does
    not identify a causal effect.

## Limitations

- Household net worth is not individual net worth.
- Net-worth observations are skewed and topcoded.
- Transcript data are a subsample and depend on transcript-quality filters.
- GPA measurement mixes grade-nine GPA and overall GPA fallback.
- Family background is only partially represented by parental net worth.
- Cohort and historical context are specific to US millennials reaching age thirty in
  the early twenty-first century.

## Reproducibility Statement

- State that the frozen NLSY97 extract lives under `data/cache/nlsy97/`.
- State that `make clean && make all` regenerates `results.json`,
  `paper/values.tex`, and the PDF.
- State that gates check citation resolution, numeric provenance, full pipeline rebuild,
  and sanity constraints.
