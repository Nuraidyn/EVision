# Robustness analyses S1-S4 (2026-11-19)

The analyses were written in `experiment-protocol.md` (sixth entry, commit `552fa67`) after the
hold-out result and before they were computed. They are secondary: they qualify, and do not
replace, the pre-registered rules R1-R5 (`results-holdout-v1.md`). No new data was read; they
use the existing intervals of runs `explore_v1`, `explore_v2_ncal96`, `holdout_ncal48`,
`holdout_ncal96` and the two instant-feedback diagnostics. Tables: `results/<run>/robust/`.
Calibration error (CE) is the mean over countries of |coverage - 0.90|; a negative contrast
means the first method is better calibrated. Settings: block length max(h, 12), S1 with 500
bootstrap replicates, S2 and S3 with 2000.

## S1. Leave one country out (base model LightGBM, warm-up 48)

Range of the contrast across the removals, and the number of removals that flip the sign of the
full-sample estimate.

| Contrast, h | Exploratory (13 countries) | Hold-out (7 countries) |
|---|---|---|
| ACI - split, h=3 | -5.1 to -4.2 pp, 0 flips | -4.1 to -2.2 pp, 0 flips |
| ACI - split, h=6 | -4.1 to -2.5 pp, 0 flips | -3.5 to -2.1 pp, 0 flips |
| ACI - rolling, h=3 | -2.5 to -1.8 pp, 0 flips | -2.2 to -1.0 pp, 0 flips |
| ACI - rolling, h=6 | -1.7 to -1.3 pp, 0 flips | -1.3 to +0.1 pp, 1 of 7 flips |
| DRACP - ACI, h=3 | 0.0 to +0.4 pp, 0 flips | -0.4 to -0.1 pp, 0 flips |
| DRACP - ACI, h=6 | -0.5 to +0.1 pp, 2 of 13 flips | -0.7 to +0.1 pp, 1 of 7 flips |

The advantage of ACI over a calibration done once does not depend on any single country. The
point estimate of ACI against rolling is negative for almost every removal but its confidence
interval includes zero in the primary run, so "not shown" stands. The DRACP - ACI estimates
sit at zero and flip sign with the removal of one or two countries.

## S2. Other base models (T in pp of CE, bootstrap p in brackets)

| Sample | Contrast, h | LightGBM | ARIMA | Naive B |
|---|---|---|---|---|
| Exploratory | ACI - rolling, 3 | -2.2 (0.030) | -1.7 (0.059) | -1.9 (0.053) |
| Exploratory | ACI - rolling, 6 | -1.5 (0.020) | -3.3 (0.016) | -1.9 (0.067) |
| Exploratory | DRACP - ACI, 3 | +0.2 (0.70) | +0.0 (0.98) | +0.1 (0.82) |
| Exploratory | DRACP - ACI, 6 | -0.2 (0.78) | -0.4 (0.54) | +0.4 (0.54) |
| Hold-out | ACI - rolling, 3 | -1.6 (0.088) | -3.0 (0.030) | -0.9 (0.22) |
| Hold-out | ACI - rolling, 6 | -0.7 (0.48) | -1.6 (0.21) | -3.2 (0.053) |
| Hold-out | DRACP - ACI, 3 | -0.2 (0.76) | -0.2 (0.80) | +0.2 (0.71) |
| Hold-out | DRACP - ACI, 6 | -0.3 (0.66) | +0.2 (0.79) | +0.3 (0.75) |

ACI - split is negative for all three base models in both samples (for Naive B at h=6 on the
hold-out panel: -10.6 pp). All DRACP - ACI equivalence tests at warm-up 48 say "equivalent"
within 2 pp, except Naive B at h=6 on the hold-out panel (p 0.0515). At warm-up 96 on the
hold-out panel most of them are "not shown". The direction ACI better than rolling holds for
every base model and both samples, but the p-values range from 0.016 to 0.22 and none
survives the correction of the pre-registered family.

## S3. Delayed feedback at h=12 (coverage with instant minus with delayed feedback, 95% interval)

| Method | Exploratory (1738 cells) | Hold-out (1009 cells) |
|---|---|---|
| ACI | +4.1 pp [1.4, 7.8] | +2.4 pp [-0.1, 4.8] |
| DRACP | +4.3 pp [1.4, 7.5] | +3.9 pp [1.6, 6.5] |
| FACI | +8.3 pp [4.3, 13.6] | +6.4 pp [2.5, 9.6] |
| Conformal PID | +5.1 pp | +5.3 pp |
| Rolling | +1.3 pp | +1.3 pp |
| Split | 0 | 0 |

R4 as registered (ACI at least +3 pp on the hold-out panel) is not met: +2.4 pp. The interval
[-0.1, 4.8] is compatible with no effect and with an effect of about 5 pp; for FACI and DRACP
the effect is clearly positive on both samples. The statement supported is "feedback delay
accounts for part of the shortfall at h=12, with a size that depends on the method and the
sample", not that it is or is not the cause.

## S4. Calibration against width (hold-out panel, LightGBM, warm-up 48)

Each cell: CE / Winkler ratio / interval width ratio, both ratios relative to rolling
conformal (below 1 is better than rolling).

| Method | h=1 | h=3 | h=6 | h=12 |
|---|---|---|---|---|
| ACI | 0.020 / 0.95 / 0.84 | 0.020 / 0.99 / 0.90 | 0.025 / 1.05 / 0.88 | 0.048 / 1.12 / 1.09 |
| DRACP | 0.021 / 0.97 / 0.89 | 0.019 / 0.97 / 0.91 | 0.022 / 1.04 / 0.91 | 0.047 / 1.25 / 0.97 |
| FACI | 0.024 / 0.95 / 0.85 | 0.023 / 0.94 / 0.90 | 0.013 / 1.00 / 0.90 | 0.070 / 1.07 / 0.92 |
| Conformal PID | 0.024 / 0.98 / 0.95 | 0.028 / 0.97 / 0.95 | 0.021 / 1.00 / 0.94 | 0.079 / 1.05 / 0.99 |
| Rolling | 0.029 / 1 / 1 | 0.036 / 1 / 1 | 0.032 / 1 / 1 | 0.086 / 1 / 1 |
| Split | 0.056 / 1.11 / 1.35 | 0.050 / 1.07 / 1.23 | 0.053 / 1.06 / 1.27 | 0.119 / 1.02 / 1.09 |

At horizons 1 and 3 ACI, DRACP and FACI are better calibrated than rolling with intervals
about 9-16% narrower, and the Winkler ratio is 0.94-0.99, so the narrower intervals do not cost
interval score. At h=6 and h=12 the Winkler ratio of ACI and DRACP is above 1 (up to 1.25), so
the advantage in calibration is paid for with width. These ratios are descriptive; the earlier
Winkler contrast with a confidence interval (`results/holdout_ncal48/winkler_contrasts.csv`)
shows ACI against rolling at h=3 as -1.0% [-7.1, +4.1] and at h=6 as +5.3% (p 0.005).

## Reading

1. Robust: adaptive conformal methods are better calibrated than a calibration performed
   once, for all three base models and without dependence on any one country.
2. Direction without proof: ACI is better calibrated than a rolling window by 1-3 pp of CE in
   most settings, but this is not established at the registered significance level.
3. No evidence of an advantage of DRACP over ACI; equivalence within 2 pp holds for most base
   models at warm-up 48 and not at 96.
4. At short horizons adaptive methods reach similar or better calibration with narrower
   intervals than a rolling window; at long horizons they do not.
5. Feedback delay accounts for part of the h=12 under-coverage; the amount is method- and
   sample-dependent.
