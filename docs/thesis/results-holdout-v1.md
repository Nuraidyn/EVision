# Hold-out results, run v1 (2026-11-19)

Status: first and only look at the 7 hold-out countries (BO, PY, UY, GH, GE, KG, AO; full IMF
monthly history, target months 2009-02 to 2026-06). The run, the amendments and the decision
rules R1-R5 were fixed in `experiment-protocol.md` (fourth entry, commit `0ff08d8`; fifth
entry with the rules and the run specification, commit `1480604`) before any forecast was
computed for these countries. Rules are applied as
written; none was changed after seeing the result. Tables: `results/holdout_ncal48/`,
`results/holdout_ncal96/`, `results/diag_instant_h12_holdout/`, `results/confirm13/`.

Setup: base model LightGBM, nominal 0.90, warm-up 48 months (run A, specified as primary) and
96 months (run B, sensitivity), block bootstrap with blocks of at least 12 months resampled
jointly across the 7 units (205 months at h=3, 199 at h=6 for run A).

## Pooled coverage (7 countries)

| Method | h=1 | h=3 | h=6 | h=12 |
|---|---|---|---|---|
| Split | 0.954 | 0.932 | 0.936 | 0.861 |
| Rolling | 0.924 | 0.918 | 0.921 | 0.872 |
| ACI | 0.914 | 0.907 | 0.908 | 0.884 |
| FACI | 0.919 | 0.910 | 0.897 | 0.835 |
| Conformal PID | 0.912 | 0.910 | 0.909 | 0.833 |
| DRACP | 0.917 | 0.904 | 0.894 | 0.865 |

## Decision rules, as pre-specified

| Rule | Outcome | Evidence |
|---|---|---|
| R1 ACI better calibrated than split (Holm p < 0.05 at h=3 and h=6) | **Not met in the primary run (warm-up 48); met at warm-up 96** | CE difference at 48: -3.0 pp (p 0.054) and -2.8 pp (p 0.092); at 96: -4.1 pp (p 0.018) and -5.9 pp (p 0.0025). The direction replicates in both runs. The secondary contrast has no Holm column in the output; the p-values are unadjusted (Holm over the two horizons would give 0.108 for both horizons at 48, and 0.018 at h=3 and 0.005 at h=6 at 96) |
| R2 ACI improves on rolling | **Not shown** | Holm p 0.35 (h=3) and 1.0 (h=6) at 48; 0.59 and 0.99 at 96. At h=6 ACI is 5.3% worse than rolling on the Winkler score (p 0.005) |
| R3 DRACP versus ACI | **Inconclusive** | Equivalent within 2 pp at warm-up 48 (TOST p 0.0005 and 0.047) but not shown at warm-up 96 (0.062 and 0.355); the verdict is not stable |
| R4 delayed feedback explains the h=12 shortfall (ACI +3 pp or more) | **Not met** | ACI 0.884 delayed, 0.908 instant: +2.4 pp. FACI +6.5 pp, DRACP +3.9 pp, rolling +1.3 pp, split 0.0 |
| R5 power | **All four primary contrasts inconclusive** | The minimum detectable difference on the full hold-out sample is undefined (baseline calibration error is too small to be improved by 10 pp); on random 15-month windows the median is 2.6-3.1 pp but 63-68% of windows are undefined |

## What can and cannot be said

- Supported (direction replicated in the exploratory data, the hold-out at both warm-ups):
  adaptive conformal methods (ACI, FACI, PID, DRACP) are better calibrated than a conformal
  calibration performed once and never updated, with the strength of the evidence depending
  on the warm-up.
- Not supported in this design: that adaptivity helps beyond a simple rolling window; that
  DRACP is better than ACI. The equivalence of DRACP and ACI within 2 pp holds at one warm-up
  and fails at the other, so only "inconclusive" is reportable.
- At h=12 every method under-covers (0.83-0.88 pooled). Releasing the outcome immediately
  restores about 0.90-0.91 for ACI and DRACP in the exploratory data (+5 pp) but only +2.4 pp
  for ACI in the hold-out, so delayed feedback is a contributing factor whose size is not
  stable across samples.
- Per-country coverage varies widely (standard deviation across units at h=12, ACI: 0.058;
  split: 0.152).

## Supplementary: original 13 countries after 2025-06

Run `confirm13`: 11 countries have target months from 2025-07 to 2026-10 (Nigeria ends in
2024-12 because of the CPI break; Russia has no usable stretch after 2022-03). With at most 16
months per unit and blocks of 12, the bootstrap is degenerate (confidence limits equal to the
estimate; p-values at the resampling floor). These contrast results are not used. Coverage in
that period is high for every method (for example ACI 0.904, 0.922, 0.940 at h=1, 3, 6),
consistent with calmer inflation, and no conclusion is drawn.

## Limits

- Seven countries; two of them (Ghana, Angola) have high-inflation episodes, so pooled
  coverage can be driven by few units.
- One point forecaster carries the contrasts; ARIMA and the cumulative-growth naive baseline
  are in `sd_coverage.csv` and show similar patterns.
- The hold-out rules produce mostly null results; absence of significance is not evidence of
  equality (see R3).
