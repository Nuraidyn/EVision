# Post hoc descriptive additions S6 and S7 (2026-11-19)

Status: post hoc. These two additions were requested by a review of the manuscript draft and
were written into `experiment-protocol.md` (seventh entry) before they were computed; they are
not part of the pre-specified family R1-R5 and use only existing interval files. Code:
`scripts/thesis/extra_descriptive.py`. Tables: `results/extra_descriptive/`.

## S6. Kazakhstan alone (design panel, exploratory sample, LightGBM base)

About 137 monthly origins at h=1 (115 at h=12), target months 2014-02 to 2025-06, so the
period after the August 2015 float is mixed with the preceding managed regime. Kazakhstan was one
of the 13 countries used to design the study; the table is descriptive and carries no test.

| Method | Coverage h=1 | h=3 | h=6 | h=12 |
|---|---|---|---|---|
| ACI | 0.898 | 0.902 | 0.906 | 0.826 |
| DRACP | 0.905 | 0.902 | 0.906 | 0.826 |
| FACI | 0.912 | 0.910 | 0.874 | 0.800 |
| Conformal PID | 0.810 | 0.850 | 0.882 | 0.835 |
| Rolling | 0.825 | 0.865 | 0.882 | 0.826 |
| Split | 0.730 | 0.827 | 0.803 | 0.713 |

Reading: for Kazakhstan the adaptive methods ACI, DRACP and FACI stay close to 0.90 up to h=6,
while the rolling window, conformal PID and the one-shot split calibration under-cover at short
horizons (rolling 0.825 at h=1; split 0.730). With about 137 correlated origins the standard
error of a coverage figure is roughly 3 pp, so only the larger gaps (split, and rolling and PID
at h=1) are clearly outside noise. At h=12 every method under-covers (0.71-0.84). The result is
consistent with a series that changed regime in 2015, where a calibration that cannot adapt
fast enough falls behind; the data do not isolate that mechanism.

## S7. Native (parametric) intervals against conformal calibration

Mean over countries of |coverage - 0.90| (calibration error, CE).

| Sample | Interval | h=1 | h=3 | h=6 | h=12 |
|---|---|---|---|---|---|
| Exploratory (13) | ARIMA native | 0.047 | 0.066 | 0.089 | 0.137 |
| Exploratory (13) | ARIMA with ACI | 0.010 | 0.015 | 0.026 | 0.079 |
| Exploratory (13) | ETS native | 0.044 | 0.051 | 0.064 | 0.116 |
| Hold-out (7) | ARIMA native | 0.053 | 0.058 | 0.062 | 0.073 |
| Hold-out (7) | ARIMA with ACI | 0.014 | 0.013 | 0.024 | 0.040 |
| Hold-out (7) | ETS native | 0.056 | 0.035 | 0.048 | 0.053 |

Contrast ACI - native, ARIMA base, in percentage points of CE (95% block-bootstrap interval,
unadjusted p; block length max(h, 12)):

| Sample | h | Difference | 95% interval | p |
|---|---|---|---|---|
| Exploratory | 1 | -3.7 | [-4.6, -0.6] | 0.004 |
| Exploratory | 3 | -5.1 | [-6.2, -1.0] | 0.003 |
| Exploratory | 6 | -6.4 | [-7.7, -1.3] | 0.002 |
| Exploratory | 12 | -5.8 | [-7.8, -1.9] | 0.003 |
| Hold-out | 1 | -3.9 | [-4.5, -1.3] | below 0.001 |
| Hold-out | 3 | -4.5 | [-4.8, -0.6] | 0.010 |
| Hold-out | 6 | -3.8 | [-4.4, +1.2] | 0.082 |
| Hold-out | 12 | -3.3 | [-4.9, +1.3] | 0.100 |

Reading: conformal calibration with ACI gives a lower calibration error than the native
intervals of the same ARIMA model at every horizon in both samples, by about 3-6 pp. On the
hold-out panel the interval excludes zero at h=1 and h=3 and includes it at h=6 and h=12. The
mean coverage of the native ARIMA intervals looks acceptable on the hold-out panel (0.943,
0.930, 0.919, 0.885) because over-coverage in some countries offsets under-coverage in others;
the calibration error shows the dispersion. This contrast is secondary, post hoc, and has no
multiplicity correction.
