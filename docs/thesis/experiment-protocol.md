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
    Status 2026-11-19: the IMF SDMX API (`api.imf.org`) serves the new months directly;
    `scripts/thesis/fetch_confirmatory.mjs` wrote `data/confirmatory.json` (SHA-256
    `e2001e5aad677567a7d572a6cf1d22929b18bfe1d3c1ad94bff47b75a3981a74`) with CPI, FX per USD
    and Brent from 2024-01. CPI runs to 2026-08 (PE, NG), 2026-09 (KZ, RU, AZ, UZ, CO, BR,
    MX, ZA) or 2026-10 (CL, MN, ID), so 14-16 months after 2025-06 per country. Overlap with
    the first snapshot (2024-01..2025-05) is identical for FX, Brent and CPI except: (a) a
    constant rebasing of the index level for KZ (ratio 0.477) and NG (ratio 0.131), which does
    not affect growth rates and is handled by working in log differences and chaining at the
    overlap; (b) small revisions for RU (up to 0.07%) and MN (up to 0.05%); (c) a
    methodology break in the Nigerian series at 2025-01 (the index falls from 113.9 to 110.7
    in rebased terms), so the growth between 2024-12 and 2025-01 is excluded for NG. The IMF
    also publishes dated CPI vintages (`CPI_2026_JAN/FEB/APR/MAY_VINTAGE`), which allow a
    revision check in real time. Brent needs the area code `G001` in the direct API.
  - Only h = 1, 3, 6 are confirmatory. h = 12 stays exploratory: its targets would give about
    4-5 non-overlapping windows per country. The protocol will list, per country and horizon,
    the number of non-overlapping target months, and a pair is treated as confirmatory only
    with at least 20. With 14-16 months per country this threshold is not met for any single
    country, so the confirmatory analysis is pooled over the panel only, and no confirmatory
    claim is made for an individual country.
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

## Reproduction status of DRACP (2026-11-19)

Done with `scripts/thesis/repro_dracp.py`, which calls the released `dracp` 0.2.0 through its
public API and executes none of the authors' pipeline scripts. Setting copied from the
authors' configs: annual HICP inflation, DE/FR/IT/ES/RO, 50/25/25 chronological split, base
model fitted once, calibration updated online, nominal 0.90, one seed.

Mean coverage over the 5 countries: ACI 0.874, DRACP 0.871, FACI 0.864, SAOCP 0.831,
rolling 0.800, conformal PID 0.779, split 0.719. The paper reports 0.884, 0.890, 0.883,
0.868, 0.841, 0.825 and 0.781 over 48 series with 20 seeds.

Reading: the ordering is qualitatively the same (split clearly worst, adaptive methods near
0.87), but the claim that DRACP is closest to nominal is not distinguishable from ACI here
(about 84 test months per country, standard error about 3 percentage points per country,
countries correlated). The criterion of reproducing a published number within 2 percentage
points cannot be tested on this subset because the published numbers are averages over
different series. Reproduction is therefore recorded as partial and qualitative. A stricter
check needs the paper's per-class table for the 28 inflation series, or all 28 series run
here, and the criterion must be restated before the confirmatory run. Until then the
conditional claim "DRACP transfers" is not made.

Difference to our design: the authors fit the model once and update only the calibration;
we refit on an expanding window, and the target is the cumulative h-month log growth, not
the annual rate. Our experiment is therefore a transfer, not a replication of their setup.

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

### 2026-11-19 (second entry, still before any forecast)

Second snapshot taken and checked (see the Data section); confirmatory analysis restricted
to the pooled panel because no country reaches 20 non-overlapping target months; Nigeria's
2025-01 methodology break recorded; topic fixed in `topic.md`.

### 2026-11-19 (third entry, engine built, still before any full run)

Decisions taken while implementing `scripts/thesis/exp/`, fixed here before results exist:

- Forecast origins start no earlier than 2000-01 for every country (the 1990s hyperinflation
  of Brazil and Mexico made native ARIMA intervals and LightGBM unusable in a check); each
  country also needs 60 months of training history, so series that start later (KZ, AZ, NG
  2005; MN 2006; UZ, PE 2010) enter once they have it. Russia is split into stretches of
  consecutive months and only stretches of at least 60 months are used.
- Fitting: each origin month is one row and models use data up to that month only. ETS and
  ARIMA are fitted to monthly inflation and the h forecasts are summed (ARMA(p,q), p,q <= 2,
  plus two annual harmonics, chosen by AICc every 12 origins; ETS with additive seasonality).
  Failed fits carry the previous point forecast forward and are counted in `n_fallback`.
- Calibration: warm-up of 48 residuals, rolling window 120, ACI step 0.02, nominal 0.90;
  all six interval methods run through the `dracp` classes with a pass-through base model so
  that the point forecast is ours; infinite radii are capped at 10 times the largest residual.
  The primary model for the contrasts and for the power simulation is LightGBM. The
  minimum detectable difference uses the first Holm step (0.05/4) for every contrast, which
  is conservative.
- Inference: pooled statistics weight every (unit, origin month) cell equally; the bootstrap
  resamples origin months in blocks of max(h, 6) jointly across units.
- Data: the two snapshots are chained on the CPI level at their last common month because
  their index bases differ (an early version merged them without rescaling, which created a
  false 74% fall for Kazakhstan; the loader now chains and a regression test checks that no
  country has a monthly log jump above 0.15). Nigeria's series ends at 2024-12 because of the
  methodology break.
- First full run: exploratory only, `--start 2000-01 --end 2025-06`, so no confirmatory
  target month can enter. The confirmatory run waits for the power result and for a committee
  review of the exploratory output.
