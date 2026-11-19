# Exploratory results, run v1 (2026-11-19)

Status: exploratory. Nothing here is a confirmatory claim. The run used only data up to
2025-06, so no confirmatory target month (>= 2025-07) entered it. The design (protocol, stress
rule, start date) was fixed before the run and logged in `experiment-protocol.md`.

Reproduce (from `scripts/thesis`, code at commit `2229076`):

    .venv/Scripts/python.exe -m exp.run full --start 2000-01 --end 2025-06 --out explore_v1 --resume

Run time 695 s. 13 units (Russia as one stretch), horizons 1, 3, 6, 12, nominal level 0.90,
bootstrap 1000 (blocks of max(h, 6) months, months resampled jointly across units). Small
result tables are copied to `results/explore_v1/`; the full per-row outputs stay under
`scripts/thesis/results/` (not tracked). No ETS/ARIMA fit fell back to a carried-forward
forecast (0 of 7628 rows per model).

## Pooled coverage (LightGBM point forecaster; every unit-month weighted equally)

| Method | h=1 | h=3 | h=6 | h=12 |
|---|---|---|---|---|
| Split conformal | 0.946 | 0.937 | 0.917 | 0.864 |
| Rolling conformal | 0.917 | 0.916 | 0.900 | 0.869 |
| ACI | 0.908 | 0.906 | 0.899 | 0.864 |
| FACI | 0.913 | 0.904 | 0.878 | 0.825 |
| Conformal PID | 0.917 | 0.907 | 0.883 | 0.837 |
| DRACP | 0.915 | 0.909 | 0.892 | 0.863 |

Bootstrap 95% intervals are wide: for ACI at h=3 [0.879, 0.930], at h=12 [0.797, 0.914].

## Primary contrasts as defined in the protocol (difference of pooled coverage)

| h | Contrast | Difference | 95% CI | Holm p |
|---|---|---|---|---|
| 3 | ACI - split | -3.0 pp | [-4.1, -1.9] | 0.004 |
| 3 | DRACP - ACI | +0.25 pp | [-0.7, +1.2] | 0.67 |
| 6 | ACI - split | -1.8 pp | [-3.3, -0.5] | 0.036 |
| 6 | DRACP - ACI | -0.74 pp | [-2.1, +0.8] | 0.67 |

Minimum detectable difference (simulation, first Holm step): 1.8-2.6 pp, below the 7 pp
threshold of the protocol.

## What the numbers say

1. **DRACP shows no advantage over ACI in this setting.** The difference is within noise at
   both horizons, and DRACP intervals are wider at h=3 (4.97 vs 4.28) and at h=12 (24.3 vs
   15.5). The conditional claim "DRACP transfers to commodity-dependent economies" is not
   supported and is not made.
2. **The sign of the ACI-split contrast must not be read as "ACI is worse".** Split conformal
   over-covers at short horizons (0.946, 0.937), so a lower ACI coverage means ACI is closer
   to 0.90. Pooled coverage can also hide opposite deviations of different countries (below).
   The protocol contrast measures the difference of coverage, not of calibration error.
3. **Per-country spread.** At h=3 split coverage ranges from 0.822 (Peru) and 0.827
   (Kazakhstan) to 1.000 (Indonesia); ACI ranges from 0.886 to 0.934. At h=12 ACI coverage
   ranges from 0.655 (Peru) and 0.716 (Nigeria) to 1.000 (Uzbekistan).
4. **Long horizon.** At h=12 every method under-covers (0.82-0.87); the adaptive methods do
   not repair it. This agrees with the limitation stated in the DRACP paper, that its
   advantage is specific to one-step forecasts, and with feedback arriving only 12 months
   after an origin.
5. **Stress.** At h=3 coverage in the top decile of FX stress at the forecast origin is
   0.849 (ACI), 0.869 (DRACP), 0.874 (split), against roughly 0.87-0.98 in the other deciles; at
   h=6 it is 0.864, 0.879 and 0.874. About 200 observations per decile, so a standard
   error of roughly 2.5 pp: the top-decile shortfall is about two standard errors and is
   exploratory. The deciles in between are not monotone.
6. **Point forecasts.** Mean absolute error relative to the cumulative-growth naive baseline
   (naive B): ARIMA 0.74-0.75, ETS 0.72-0.76 and LightGBM 0.74-0.75 at h=3 and 6; 0.86, 0.93
   and 0.91 at h=12. Naive A (h times last monthly inflation) is worse than naive B at h >= 3.

## Limits

- Exploratory: the same data shaped earlier design decisions (stress validity checks,
  start date), so none of this is confirmatory.
- Pooled coverage weights unit-months equally; cross-country dependence is handled only by
  joint resampling of months.
- Interval width is a mean of widths in percentage points of cumulative growth; heavy
  tails and the cap on infinite radii (10 times the largest residual) can affect it, so
  widths are indicative.
- The minimum detectable difference comes from a simulation that has not been reviewed
  independently, and it refers to the pooled-coverage contrast; for the calibration-error
  contrasts that replaced it as primary (see the protocol, fourth entry) the minimum
  detectable difference is undefined on the full exploratory sample (`results/explore_v1/power_mde_ce.csv`).
- One point forecaster (LightGBM) carries the contrasts; ARIMA and naive B give similar
  coverage at h=6 (ACI 0.895 and 0.908).
