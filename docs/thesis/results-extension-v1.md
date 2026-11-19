# Extension results: second hold-out panel and Chronos (2026-11-19)

Status: the runs, the second hold-out panel and the decision rules E1-E5 were fixed in
`experiment-protocol.md` (eighth entry, commit `dfe0b2c`) before any forecast was computed for
these countries. The code is at commit `ca43ddc`. Rules are applied as written. Tables:
`results/holdout2_ncal48/`, `results/holdout2_ncal96/`, `results/ext_design13/`,
`results/ext_holdout1/`, `results/extension_accuracy/` (the per-base-model analyses are in the
`ce_<model>` subfolders).

Setup: second hold-out panel of 10 countries (ZM, AM, TZ, UG, KE, IQ, BW, NA, MZ, CI; 198
months of IMF CPI from 2010-01; 89 pooled months at h=3 and 83 at h=6 at warm-up 48, 41 and 35 at
warm-up 96); four base models (naive B, ARIMA, LightGBM, and Chronos zero-shot with the model
`amazon/chronos-bolt-tiny`); nominal level 0.90; block bootstrap with blocks of at least 12
months. The earlier 20 countries were re-run with the same four models from 2010-01 as a
secondary analysis, so their numbers differ from the earlier runs that started in 2000.

Implementation note recorded for transparency: the first attempt to analyse the new panel failed
because the country code NA (Namibia) was read as a missing value by the CSV reader; the reader
was fixed (`read_results`, with a regression test), the forecasts were not affected and were not
recomputed, and only the analysis step was repeated.

## E1: do the main conclusions replicate on new countries?

Calibration error (CE, mean over countries of |coverage - 0.90|) at h=3, warm-up 48 (primary).

| Base model | ACI | DRACP | Rolling | Split | Native |
|---|---|---|---|---|---|
| LightGBM | 0.033 | 0.023 | 0.070 | 0.104 | |
| ARIMA | 0.034 | 0.019 | 0.066 | 0.098 | 0.058 |
| Naive B | 0.049 | 0.037 | 0.090 | 0.122 | |
| Chronos | 0.737| 0.034 | 0.030 | 0.067 | 0.109 | |

Primary contrasts at warm-up 48 (difference of CE in pp, Holm p over the family of four):

| Base model | ACI - rolling, h=3 | ACI - rolling, h=6 | DRACP - ACI, h=3 | DRACP - ACI, h=6 |
|---|---|---|---|---|
| LightGBM | -3.7 (0.008) | -3.5 (0.159) | -1.0 (0.321) | -1.3 (0.337) |
| ARIMA | -3.2 (0.004) | -3.1 (0.030) | -1.5 (0.199) | -1.8 (0.199) |
| Naive B | -4.1 (0.004) | -3.5 (0.039) | -1.2 (0.422) | -1.8 (0.422) |
| Chronos | 0.737| -3.3 (0.036) | -2.5 (0.089) | -0.5 (0.454) | -1.2 (0.443) |

Secondary contrast ACI - split at warm-up 48 (unadjusted p): LightGBM -7.0 and -8.0 pp (0.0005
and 0.0005), ARIMA -6.4 and -5.8 (0.0005, 0.001), Naive B -7.3 and -5.3 (0.001, 0.0045), Chronos
-7.4 and -5.7 (0.0005, 0.0005). ACI against the native intervals of ARIMA is read from the CE
table above: 0.034 against 0.058 at h=3.

Outcomes of the rules on this panel (warm-up 48 primary; warm-up 96 is a sensitivity run and is
not promoted):

- R1 (ACI better calibrated than split): met for all four base models at both horizons.
  At warm-up 96 it is not met: LightGBM (0.048) and Naive B (0.032) at h=3 have unadjusted p below
  0.05, every other cell is above 0.05, and with Holm over the two horizons none is below 0.05
  (0.096 and 0.064).
- R2 (ACI improves on rolling, Holm p below 0.05): met at h=3 for all four base models and at h=6
  for ARIMA (0.030) and Naive B (0.039); not met at h=6 for LightGBM (0.159) and Chronos (0.089).
  At warm-up 96 it is not shown for any base model (Holm p 0.15 to 1.0; 41 and 35 pooled months).
  **This differs from the first hold-out panel and from the design panel, where R2 was "not shown"
  (results-holdout-v1.md); the earlier 20 countries re-run from 2010-01 again show it as not met
  (ACI - rolling, Holm p 0.22 to 1.0, tables in `results/ext_design13/` and `results/ext_holdout1/`).**
  The conclusion about ACI against a rolling window therefore depends on the panel; the data do not
  say why. Panel differences (shorter series, lower-income and more volatile economies, a warm-up
  that takes a larger share of 198 months) are candidate explanations that were not tested.
- R3 (DRACP against ACI): inconclusive. At warm-up 48 DRACP has a lower CE than ACI in every cell
  (by 0.5-1.8 pp) but no difference is significant; equivalence within 2 pp holds only for Chronos
  at h=3 (p 0.0385) and is not shown elsewhere. At warm-up 96 equivalence holds for LightGBM and
  Naive B at h=3 and not elsewhere, and DRACP is better than ACI at h=6 for Naive B (-2.3 pp, Holm
  p 0.002) only. The rule requires the same verdict at both warm-ups, so it is not met.
- E5 (power): minimum detectable differences at warm-up 48 are 1.2-6.6 pp for ACI - rolling (not
  defined for Chronos at h=3) and undefined for every DRACP - ACI contrast; at warm-up 96 they are
  undefined for all contrasts. Contrasts without a defined minimum detectable difference are
  inconclusive whatever their p-value. The ACI - rolling results at warm-up 48 are therefore
  conclusive for LightGBM (3.2 and 6.1 pp), ARIMA (3.2 and 3.5), Naive B (1.2 and 3.5) and
  Chronos at h=6 (6.6), and not conclusive for Chronos at h=3.

## E2: does the conclusion depend on the base model?

On this panel the direction and the size of the contrasts are alike for the four base models
(tables above). On the 20 earlier countries re-run from 2010-01 the same holds, with a weaker
effect: ACI - rolling is -1.3 to -4.7 pp for LightGBM and Chronos in the two panels and none is
significant after the correction (Holm p 0.22-1.0); ACI - split is -3.5 to -9.4 pp with
unadjusted p between 0.002 and 0.045.

## E3 and E4: point accuracy of Chronos, and the question of leakage

Mean absolute error relative to naive B (below 1 is better), second hold-out panel, all months,
warm-up 48:

| Model | h=1 | h=3 | h=6 | h=12 |
|---|---|---|---|---|
| Chronos | 0.737| 0.737 | 0.586 | 0.581 | 0.934 |
| ARIMA | 0.779 | 0.602 | 0.570 | 0.880 |
| LightGBM | 0.817 | 0.619 | 0.593 | 0.943 |

Target months before 2025-01 are flagged `possibly_seen`: Chronos may have met these public series
in pretraining (its cutoff was not looked up; 2025-01 is a conservative assumption). On the target
months from 2025-01 (22 calendar months, 567 country-month cells per horizon, pooled over the 30
countries), the difference in mean absolute error (Chronos minus the other model, in pp of
cumulative growth; negative favours Chronos), with a paired block-bootstrap 95% interval (blocks of
3 months, months resampled jointly across countries; `scripts/thesis/extension_accuracy.py`):

| h | against LightGBM | against ARIMA | against Naive B |
|---|---|---|---|
| 1 | -0.023 [-0.047, -0.007] | -0.037 [-0.053, -0.021] | -0.104 [-0.134, -0.081] |
| 3 | -0.031 [-0.078, +0.036] | -0.086 [-0.139, -0.031] | -0.350 [-0.519, -0.206] |
| 6 | -0.084 [-0.129, -0.025] | -0.097 [-0.204, +0.002] | -0.720 [-0.905, -0.528] |
| 12 | -0.245 [-0.465, -0.019] | -0.024 [-0.122, +0.139] | -0.256 [-0.449, -0.041] |

Relative MAE of Chronos on these clean months is 0.774, 0.699, 0.654 and 0.895 at h=1, 3, 6 and 12
(LightGBM 0.824, 0.725, 0.694, 0.995; ARIMA 0.854, 0.773, 0.700, 0.905). Reading: Chronos is at
least as accurate as LightGBM and ARIMA in this period and clearly more accurate than the naive
baseline; against LightGBM the interval excludes zero at h=1, 6 and 12 and against ARIMA at h=1 and
3. The sample is thin (22 months), the block length is short because of it, the leakage assumption
is not verified, and these are descriptive results, not a ranking of forecasters.

## What this adds to the thesis

- The calibration conclusions do not depend on the base model: ACI with any of the four base models
  is better calibrated than a one-shot calibration and (for ARIMA) than the native intervals, in the
  same direction as before.
- The ACI - rolling result is panel dependent (met on the second hold-out panel at the primary
  warm-up, not shown on the other panels), so the statement "adaptivity beyond a rolling window is
  not established" stays correct as a statement about the evidence taken together, and the new panel
  is an honest counter-example that must be reported next to it.
- DRACP against ACI stays inconclusive, with a small consistent tendency of lower CE for DRACP at
  warm-up 48 that is not significant.
- A foundation model can be used as a base forecaster for conformal intervals without changing the
  conclusions, and it is competitive in point accuracy on the months it cannot have seen.
