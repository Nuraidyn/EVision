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

### 2026-11-19 (fourth entry: amendments after the exploratory run v1, before any confirmatory run)

Source: `results-exploratory-v1.md`, the calibration-error analysis (`exp.run ce`), and a
committee review (5.5/10, about 6.5 with these fixes). All changes below are motivated by
logical defects found in the design, not by significance, and are fixed before the data they
will be applied to is analysed. The original pooled-coverage contrasts stay in the report as
secondary results.

1. **Calibration error replaces pooled coverage as the primary outcome.** For each unit
   CE = |coverage - 0.90| and a contrast is the equal-weight mean over units of the difference
   of CE. Reason: pooled coverage lets opposite country deviations cancel (split conformal
   covers 1.000 in Indonesia and 0.822 in Peru at h=3). Exploratory v1: ACI - split,
   h=3: -4.6 pp (95% CI [-5.0, -1.4], Holm p 0.002); h=6: -3.4 pp (Holm p 0.0045);
   DRACP - ACI: +0.2 and -0.2 pp, not distinguishable from zero.
2. **Reference method.** Split conformal calibrated once on the first 48 months and never
   updated is a weak reference. The primary contrasts become ACI - rolling conformal and
   DRACP - ACI, at h=3 and h=6. ACI - split is kept as a secondary, descriptive result.
3. **DRACP versus ACI is an equivalence question.** The minimum detectable improvement over
   ACI cannot be reached (ACI's mean CE is already about 1.5 pp; MDE undefined), so a null
   result is not evidence of equality. The test is two one-sided tests with an equivalence
   margin of 2 pp in CE; "no advantage" is claimed only if equivalence is shown, otherwise the
   result is reported as inconclusive. Winkler score and the standard deviation of coverage
   across units are reported next to CE.
4. **Fair DRACP sensitivity.** In v1 DRACP trains its regime and scale models on half of a
   48-month warm-up (24 rows). It is re-run with a warm-up of 96 months for all methods
   (`n_cal=96`) on the exploratory data; the conclusion about DRACP is drawn only if it is
   stable across the two warm-up sizes.
5. **Hold-out countries are the main confirmatory pool.** Fifteen months per country after
   2025-06 give two or three independent blocks, so the confirmatory months of the original
   13 countries cannot carry a claim. Seven further commodity-dependent economies that were
   not used for any design decision form a hold-out panel with their full history: BO, PY,
   UY, GH, GE, KG, AO (`scripts/thesis/data/holdout.json`, SHA-256
   `0245eab6c75d6bd7fe800fe5978a7ca5670550dff4b3f23e817177f9c6fae9ac`). The candidate list
   (14 names, fixed order) and the eligibility rule (at least 220 months of IMF monthly CPI
   and FX per USD within 2000-01..2026-06, at most 3 missing CPI months) were written in
   `fetch_holdout.mjs` before any forecast was computed; the first 10 eligible were to be
   kept, and only 7 candidates met the rule (ZM, AM, TZ, UG, KE, IQ start in 2009-2010, PG has
   no CPI), so the panel has 7 countries and the rule was not relaxed. No forecast has been
   computed for these countries before this entry. All their months count as hold-out
   (`sample = holdout`). The confirmatory months of the original 13 countries are reported
   as a supplementary check, pooled only.
6. **Dependence and horizon.** Contrasts use a moving-block bootstrap with block length at
   least 12 months (ACI has a memory of roughly 50 months at step 0.02). The failure at h=12
   is examined with a diagnostic run in which feedback arrives immediately; it is labelled a
   diagnostic and not a primary result. The MDE for confirmatory claims is computed on random
   15-month windows of the exploratory data and on the hold-out panel, and a contrast with an
   MDE above 7 pp is reported as inconclusive.
7. **Stress analysis stays exploratory.** It is presented with clustering by episode and
   with the number of deciles, methods and horizons that were looked at.
8. **Reading of the exploratory DRACP result.** Allowed wording: "in this configuration no
   advantage over ACI was detected"; not allowed: "DRACP does not transfer" or "ACI and DRACP
   are equal".

### 2026-11-19 (fifth entry: hold-out run specification and decision rules, before the run)

Exploratory results with the amended contrasts (block length 12, `results/explore_v1` and
`explore_v2_ncal96`, tables in `results/`): no primary contrast survives Holm at either
warm-up (ACI - rolling at h=3: -2.2 pp, Holm p 0.09; at h=6: -1.5 pp, Holm p 0.078);
ACI - split stays clear (-4.6 / -3.4 pp at warm-up 48, -3.9 / -2.9 pp at 96); DRACP - ACI is
equivalent within 2 pp at warm-up 48 (max one-sided p 0.0085 and 0.0135) but not at 96
(0.128 and 0.146), so the equivalence verdict is not stable and DRACP is wider than ACI at
warm-up 96 (Winkler +33% at h=3); at h=12 the adaptive methods cover 0.82-0.86 with delayed
feedback and 0.91 when the outcome is revealed immediately (diagnostic).

The hold-out run is specified here, before any forecast is computed for the 7 hold-out
countries. Runs (from `scripts/thesis`, all with `--holdout --start 2000-01 --end 2026-06`):
(A) `--out holdout_ncal48`; (B) `--n-cal 96 --out holdout_ncal96`; (C) the instant-feedback
diagnostic `--instant-feedback --horizons 12 --models lgbm --conformal-models lgbm
--out diag_instant_h12_holdout`. Supplementary: the original 13 countries to 2026-09
(`--start 2000-01 --out confirm13`), reported pooled over the confirmatory months only.

Decision rules (applied to base model lgbm, primary family Holm over 4 tests, pooled over the
7 countries, block length 12):

- R1 (replication of the secondary result): ACI better calibrated than split, if the CE
  difference ACI - split is negative with Holm p < 0.05 at both h=3 and h=6.
- R2 (does adaptivity help beyond a rolling window): "ACI improves on rolling" only if
  ACI - rolling is negative with Holm p < 0.05 at the horizon; otherwise "not shown".
- R3 (DRACP versus ACI): "no advantage, equivalent within 2 pp" only if equivalence holds at
  both warm-up sizes (A and B); "DRACP better" only if DRACP - ACI is negative with Holm
  p < 0.05 at both warm-ups; otherwise "inconclusive".
- R4 (delayed feedback explains the h=12 shortfall): supported if the mean coverage of ACI
  with instant feedback exceeds the delayed one by at least 3 pp on the hold-out panel.
- R5 (power): a contrast whose minimum detectable difference is undefined or above 7 pp is
  reported as inconclusive regardless of its p value.

None of these rules is changed after the hold-out result has been seen; any later change goes
into this section with a date and a reason and is reported as post hoc.

### 2026-11-19 (sixth entry: robustness analyses written down after the hold-out result, before they are computed)

The hold-out result (`results-holdout-v1.md`) was mostly null and a committee review asked
for analyses that explain it. They are listed here before they are computed. They are
secondary: they do not replace R1-R5, no threshold is changed, warm-up 48 stays the primary
configuration and warm-up 96 stays a sensitivity run (it is not promoted because R1 holds
there). They use outputs that already exist, so no new data is read and no new method is
added. Every result is reported on both the exploratory data and the hold-out panel.

- S1, leave-one-country-out: the CE contrasts ACI - split, ACI - rolling and DRACP - ACI at
  h=3 and h=6 (warm-ups 48 and 96) recomputed with each unit removed in turn; the report gives
  the range of the point estimate and how many removals change the sign.
- S2, other base models: the same contrasts for ARIMA and naive B as base models of the
  conformal methods (LightGBM was the base model of the primary family).
- S3, delayed feedback: the difference between the coverage with instant feedback and with
  delayed feedback at h=12 for ACI, DRACP and FACI, with a paired block-bootstrap interval,
  on both samples. R4 keeps its pre-specified threshold and verdict; the interval only
  qualifies the wording.
- S4, width and efficiency: per method and horizon, the ratio of the mean Winkler score and
  of the median interval width to rolling conformal, per unit and pooled, next to the CE.
- S5, wording: effects are reported as the range of differences compatible with the data
  (the confidence interval), not as present or absent; the 2 pp equivalence margin and the
  3 pp threshold of R4 are unchanged and are not justified beyond being fixed beforehand.

### 2026-11-19 (seventh entry: two post hoc descriptive additions after the manuscript review)

A review of the manuscript draft pointed out that the native (parametric) intervals of ARIMA
and ETS were computed but not reported, and that the title mentions Kazakhstan while no
Kazakhstan result is shown. Two additions are made, both labelled post hoc and both computed
from existing outputs only:

- S6, Kazakhstan (design panel, exploratory sample only): coverage, calibration error and
  number of origins per method and horizon for Kazakhstan alone. Descriptive; no inference,
  because the series has about 137 monthly origins after the 2015 float and Kazakhstan was one
  of the 13 countries used to design the study.
- S7, native intervals: calibration error of the native intervals of ARIMA and ETS against ACI
  with ARIMA as the base model, per horizon, on the exploratory and the hold-out panels. For
  ARIMA a block-bootstrap interval of the difference ACI - native (same bootstrap settings as
  the primary contrasts, unadjusted p-values, secondary family); for ETS (no conformal
  version was run) the calibration error is reported without a contrast.

These results do not change R1-R5 and are not part of the pre-specified family.

### 2026-11-19 (eighth entry: AI extension, specified before any computation)

The thesis adds two components that were not in the original design. Both are specified here
before any forecast, request or evaluation is computed. They do not change R1-R5 or any earlier
result.

**E. Foundation-model forecaster (Chronos) and a second hold-out panel.**

- Forecaster `chronos`: a pretrained Chronos model used zero-shot (no fine-tuning, no
  covariates), the smallest Chronos-Bolt model that can be installed (fallback: chronos-t5-small);
  the exact model identifier is written into the code and the results before the run. It forecasts
  the monthly inflation series (100 times the log change of the CPI) h steps ahead from all history
  up to the origin (truncated to the model's maximum context) and the h median forecasts are
  summed, as for ETS and ARIMA. No native interval is produced (the cumulative sum of quantiles is
  not a quantile); the conformal methods are applied on top of its point forecast, like for the
  other base models.
- Second hold-out panel (`data/holdout2.json`, SHA-256
  `72bcfee645ef3c5f89a67763278a3ee8ee2a74523e38a26739b16726c8947c75`): ZM, AM, TZ, UG, KE, IQ,
  BW, NA, MZ, CI, the first 10 of a candidate list fixed in `fetch_holdout2.mjs` before any
  forecast (rule: at least 170 months of IMF monthly CPI and FX within 2010-01..2026-06, at most 3
  missing CPI months; CM, DZ, EG, MW, RW, ET were also eligible but beyond the first 10). No
  forecast of any kind has been computed for these countries before this entry. All their target
  months are labelled `holdout2`. The panel is shorter than the first hold-out (198 months from
  2010-01), so the first evaluated origins fall after the 60-month training minimum and the warm-up.
- Runs, all with `--start 2010-01`: (E-A) base models lgbm, arima, naive_b and chronos on the second
  hold-out panel at warm-up 48 (primary) and 96 (sensitivity); (E-B) the same four base models on
  the 20 earlier countries, as a secondary analysis, with the Chronos rows flagged as described
  below.
- Decision rules, applied separately for each base model, with the CE contrast family of the
  protocol (ACI - rolling and DRACP - ACI at h=3 and h=6, Holm over 4; ACI - split and ACI - native
  secondary):
  - E1, replication of the main conclusions on new countries: a statement of R1, R2 or R3 is
    "replicated" for a base model only if it is met by the same rule as in the fifth entry and in
    the same direction; otherwise it is reported as not replicated or inconclusive. Results at
    warm-up 96 are a sensitivity analysis and are not promoted.
  - E2, whether the conclusions depend on the base model: reported as the table of the contrasts
    for lgbm, arima, naive_b and chronos side by side, without a threshold.
  - E3, point accuracy of Chronos: mean absolute error relative to naive B per horizon with a
    block-bootstrap 95% interval, next to arima, ets and lgbm; descriptive.
  - E4, leakage: Chronos may have seen public CPI series during pretraining. Target months before
    2025-01 are flagged `possibly_seen`; only target months from 2025-01 are treated as clean.
    Claims about the accuracy of Chronos are drawn from the clean months pooled over all 30
    countries, and the thinness of that sample is stated. Calibration contrasts for Chronos are
    reported on all months with the flag.
  - E5, power: a contrast whose minimum detectable difference is undefined or above 7 pp is
    reported as inconclusive.

**L. LLM explanation layer (engineering chapter with its own evaluation).**

- Component: an explainer that receives a user question about a country and a horizon, calls the
  platform endpoint `GET /api/v1/inflation/calibrated-forecast` as a tool and answers in English,
  Russian or Kazakh. The language model is accessed through the project's existing OpenRouter
  client; the model identifier is written into the code and the results before the run.
- Evaluation set, fixed here: 13 countries x 4 horizons x 3 question types (what is the forecast
  and its interval; how reliable is the interval; what should the user not conclude from it) x 3
  languages = 468 prompts, each answered in two conditions: (a) with the tool result in the
  context, (b) without it (an ungrounded baseline).
- Metrics, computed by program and not by a judge model: numerical faithfulness (share of answers
  in which every number that refers to the forecast, the lower and upper limit, the nominal level,
  the empirical coverage or the number of evaluated points equals the API value within rounding);
  omission rate (share of answers that do not state the interval and the level); coverage
  overstatement (share of answers that present the interval as guaranteed, or omit the empirical
  coverage when it is more than 5 pp below nominal); a manual review of 30 answers per language for
  fluency and terminology. Rates are reported with Wilson 95% intervals; there is no pass
  threshold, and no result of this component enters the main claims of the thesis.

Boundary note, to be repeated in the write-up: the hold-out countries are untouched with
respect to countries only; the set of methods, the form of the contrasts and the horizons were
chosen on the exploratory countries, and the author had seen the post-2025-06 months of the
original 13 countries before the amendments.
