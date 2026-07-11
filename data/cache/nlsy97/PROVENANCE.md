# NLSY97 Extract — Provenance

**Source:** NLS Investigator (https://www.nlsinfo.org/investigator), Bureau of Labor
Statistics public-use data, NLSY97 cohort (~8,984 respondents born 1980–84, surveyed
since 1997). Extract pulled during prep (July 2026) because Investigator requires an
interactive web session — the agent never fetches this; it starts from the frozen files
in this directory. Anyone can rebuild the extract free of charge from the same source.

**Documentation used to select variables:**
- Assets & Debts topical guide: nlsinfo.org/content/cohorts/nlsy97/topical-guide/income/assets-debts
- School & Transcript Surveys guide: nlsinfo.org/content/cohorts/nlsy97/topical-guide/education/school-transcript-surveys

## Variable shopping list

| Variable | What it is | Role |
|---|---|---|
| TRANS_CRD_GPA_OVERALL | Credit-weighted overall high school GPA (from real transcripts) | predictor |
| TRANS_CRD_GPA_YR_* | Credit-weighted GPA by academic year (all years) | grade-9 GPA derivation |
| TRANS_PROBFLAG | Transcript data quality flag | quality filter |
| CVC_HH_NET_WORTH_30 | Household net worth at age 30 (constructed) | outcome |
| CV_HH_NET_WORTH_P | Household net worth per parent report, round 1 (1997) | family-wealth control |
| CVC_HH_NET_WORTH_25 / _35 | Net worth at 25 / 35 | robustness |
| KEY_SEX, KEY_RACE_ETHNICITY, KEY_BDATE_Y | Demographics + birth year | controls / cohort check |
| CV_INCOME_GROSS_YR (round 1) | Gross household income 1997 | alternative control |
| CV_HGC_EVER (latest) | Highest grade completed | attainment robustness |
| Sampling weights (round-1 / cumulative custom) | Survey weights | weighted estimates |

Known caveats (state in paper's Limitations): net worth is household-level and topcoded;
transcripts cover 6,232/8,984 (69.4%) with TRANS_PROBFLAG quality issues in a subset;
Assets-30 tax-advantaged-accounts skip error (see assets-debts guide) — created net-worth
variables still defined for all respondents; cohort reached age 30 in ~2010–2014.

## Files (FROZEN 2026-07-02, pulled via NLS Investigator guest session)

Dataset: **NLSY97 1997-2023 (rounds 1-21), released January 23, 2026**. 71 variables ×
8,984 respondents. Extract built by OR-searching question names: TRANS_CRD_GPA*,
TRANS_PROB*, CVC_HH_NET_WORTH*, CV_HH_NET_WORTH*, CVC_HGC*, SAMPLING_WEIGHT*,
CV_INCOME_GROSS_YR* + Investigator's 6 defaults (PUBID, sex, birth m/y, sample type,
race/ethnicity).

- `nlsy97_gpa_networth.csv` — the data (RNUM column headers), unmodified
- `nlsy97_gpa_networth.cdb` — codebook (value labels, topcodes, universes)
- `nlsy97_gpa_networth.NLSY97` — tagset: upload to Investigator to rebuild this exact extract
- `nlsy97_gpa_networth.dat/.dct/.sas/.sps/-value-labels.do` — control files from the same zip
- `nlsy97_gpa_networth.zip` — pristine original download (2.7 MB)
- `variable_map.csv` — RNUM → variable title mapping (generated from the .dct)
- `CHECKSUMS.txt` — SHA256 of all of the above

Verified present: CVC_HH_NET_WORTH_20/25/30/35/40, CV_HH_NET_WORTH_P (parent, 1997),
TRANS_CRD_GPA_OVERALL + by-year + by-subject, TRANS_PROBFLAG, CVC_HGC_EVER, round-1
sampling weights, CV_INCOME_GROSS_YR (all rounds).
