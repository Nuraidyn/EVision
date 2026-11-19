# Experiment protocol (draft 1, 2026-11-19)

Status: draft written before any forecast or interval has been computed. Changes after the
first experiment run must be logged in the "Changes" section with a date and a reason.
Shock and stress definitions are in `shock-definition.md`; this document does not change
them.

## Question

Do prediction intervals for monthly inflation in commodity-dependent economies keep their
nominal coverage across horizons, and do adaptive conformal methods that were shown to work
on euro-area and US data (arXiv 2608.17079, DRACP) transfer to this setting?

Claim hierarchy (set after a committee review of draft 1):

1. Primary claim: a calibration benchmark. Empirical coverage and width of split conformal,
   rolling conformal, ACI, FACI, conformal PID and the models' native intervals at h = 1, 3, 6
   on a panel of commodity-dependent economies, reported together with the minimum
   detectable difference given the panel size and dependence.
2. Conditional claim: "DRACP transfers to this setting" is stated only if the authors'
   package is reproduced within tolerance (see below) and the minimum detectable difference
   at h = 3 or 6 is at most 7 percentage points. Otherwise it is not claimed.

## Data

- Target: `y(t, h) = 100 * ln(CPI_{t+h} / CPI_t)`, horizons h in {1, 3, 6, 12} months.
- CPI: IMF monthly all-items index (`scripts/thesis/data/snapshot.json`, SHA-256 in
  `shock-definition.md`). Exogenous inputs: exchange rate per USD, Brent.
- Countries (13): core long-history group BR, MX, CL, CO, PE, ZA, ID; regional KZ, RU, AZ,
  UZ; control NG, MN. Russia has 30 missing months and is run only on its consecutive
  stretches, or dropped from pooled results if that is not possible.
- Splits:
  - Exploratory: all months up to 2025-05 in the snapshot. Anything computed here is
    labelled exploratory.
  - Confirmatory: target months after the snapshot (2025-07 onwards), downloaded only after
    this protocol is committed, from the same source (IMF CPI) so the methodology does not
    change at the boundary. DBnomics was last indexed 2025-08-31, so the new months must be
    taken from the IMF directly; this is not yet verified. A second snapshot is stored with its
    SHA-256, and a jump test on the index flags base-year breaks automatically. At most about
    16 months are available and fewer for countries with a publication lag.
  - Only h = 1, 3, 6 are confirmatory. h = 12 stays exploratory: its targets would give about
    4-5 non-overlapping windows per country. The protocol will list, per country and horizon,
    the number of non-overlapping target months, and a pair is treated as confirmatory only
    with at least 20.
  - Pretraining leakage: Chronos may have seen IMF CPI series up to its training cutoff, so
    its exploratory results carry a leakage flag and only the confirmatory set is treated as
    a clean test for it.

## Point forecasters

Core: two naive baselines, ETS, ARIMA (automatic order selection by AICc), LightGBM (direct
forecast, one model per horizon, lagged inflation, FX change, Brent change). Extension:
Chronos zero-shot, run only if the environment allows it; its absence does not change the
core.

- Naive A: h times the last monthly inflation rate. Naive B: the last observed cumulative
  h-month growth (the YoY-like base, equal to YoY at h = 12).
- Seasonality: monthly dummies are allowed in ARIMA and ETS (seasonal period 12) and are
  fixed in advance; the same seasonal setting is used for every country.
- Central-bank inflation target as an additional baseline at h = 6 and 12 for countries that
  have an explicit target. Targets and their effective dates are collected and recorded
  before the run. Exploratory only.

All models are refitted on an expanding window; hyperparameters are fixed in advance
(no tuning on the test period).

## Interval methods

- Reference: split conformal, rolling-window conformal, ACI, FACI, conformal PID (the
  baselines used in the DRACP paper), and DRACP using the authors' released package. The
  package exists (PyPI `dracp` and the GitHub repository, MIT licence; checked 2026-11-19;
  its classifiers list Python 3.10-3.12).
- Sanity check before any new result is trusted: our ACI implementation must match the
  authors' reference ACI on one shared series to numerical tolerance, and the authors'
  code must reproduce a published coverage number on their data within 2 percentage
  points. If it does not, the decision (fall back to an implementation from the paper, with
  deviations logged, or drop DRACP) is written here before the run, and the conditional
  claim is not made.
- Parametric model intervals (ETS and ARIMA native intervals) as a null comparison.
- Nominal level 0.90. Calibration window and learning rates are fixed in advance and not
  tuned on the test period.

## Evaluation

Rolling origin, one origin per month. Metrics:

- Point: MAE and RMSE relative to naive.
- Intervals: empirical coverage, mean width, interval (Winkler) score.
- Inference: moving-block bootstrap with block length at least h (errors of h-step forecasts
  overlap), resampling calendar months jointly across countries (so common global shocks are
  not treated as independent); pooled and per country results are both reported. No country-level conclusion where a country has fewer
  than 10 independent episodes for the question asked.

## Primary contrasts (fixed in advance)

1. Coverage of ACI minus coverage of split conformal, per horizon, pooled over the panel.
2. Coverage of DRACP minus coverage of ACI, per horizon, pooled over the panel.

Primary tests are restricted to h = 3 and h = 6: four tests (2 contrasts x 2 horizons) with
Holm correction. h = 1 and h = 12 are descriptive. The minimum detectable difference (MDE)
in coverage is simulated on the exploratory data before the confirmatory run, with the
actual dependence (overlapping errors, shared calendar months). If the MDE is above 10
percentage points the contrast is reported as inconclusive and not as evidence of no
effect; the conditional claim requires an MDE of at most 7 percentage points for at least
one of the two horizons.

## Secondary analyses (exploratory, not part of the primary claim)

- Coverage by decile of FX stress at the forecast origin (continuous), with the discrete
  shock windows as a check.
- Per-country heterogeneity, and the exchange-rate regime split (floating, managed, pegged).
- Foundation-model forecasts against classical and ML ones.

## Environment

The machine has Python 3.14 with only numpy. The DRACP package lists support for Python
3.10-3.12, so a Python 3.12 virtual environment under `scripts/thesis/.venv` is used
(`py install 3.12`), with pandas, statsmodels, scikit-learn, LightGBM and the DRACP package;
PyTorch and Chronos are optional and heavy. Nothing is installed without approval.

## Known risks

- Weak association between stress and error (see `shock-definition.md`): the thesis does not
  depend on it.
- Power: the number of independent episodes per country is small; pooled inference carries
  the claims.
- Novelty is a transfer and replication result in a new setting, not a new method.
- Revisions and base-year breaks in the CPI series are not yet checked.

## Changes

### 2026-11-19 (before any forecast was run)

Committee review of draft 1: 5.5/10. Changes made: the claim hierarchy; confirmatory set
limited to h = 1, 3, 6; second snapshot from the same source with a hash and a break test;
FACI and conformal PID added; reproduction tolerance and a fallback for DRACP; two explicit
naive baselines, a seasonality rule and the central-bank target as an exploratory baseline;
block length at least h; primary tests reduced to h = 3 and 6; MDE simulation before the
confirmatory run, with a numeric threshold for the conditional claim.
