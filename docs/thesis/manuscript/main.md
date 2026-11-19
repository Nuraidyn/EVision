# Calibrating Prediction Intervals for Inflation Forecasts in Commodity-Dependent Economies: A Multi-Horizon Panel Benchmark of Conformal Methods, with Kazakhstan as a Case Study

Draft manuscript, 2026-11-19. Source documents: `docs/thesis/` and `scripts/thesis/exp/` on branch `thesis/inflation-calibration` (HEAD `de93501`).

---

## How this text should be reviewed (not part of the paper)

This draft was written only from the project documents and the result tables in `docs/thesis/results/`. No analysis was re-run. Before the text is used, the following should be checked.

**Numbers to re-check against the CSV tables** (all in `docs/thesis/results/<run>/`):

1. The CE contrasts, confidence intervals and p-values in Tables 3, 4 and 5: `calibration_contrasts.csv` and `calibration_tost.csv` in `explore_v1`, `explore_v2_ncal96`, `holdout_ncal48`, `holdout_ncal96`.
2. The pooled coverage in Tables 2 and 6: `interval_summary.csv` (rows with `unit = ALL`, model `lgbm`).
3. The delayed-feedback differences in Table 7: `robust/s3_feedback_diff.csv` (rows `unit = ALL`).
4. S1, S2 and S4 (Tables 8 to 10): `robust/s1_leave_one_out.csv` (rows `SUMMARY`), `robust/s2_other_models.csv`, `robust/s4_compact.csv`.
5. The minimum detectable differences: `power_mde_ce.csv` and `power_mde_ce_windows15.csv`.
6. Winkler contrasts: `winkler_contrasts.csv`.

**Places where the source documents and the CSV tables differ in the last digit.** The text follows the CSV in each case.

- R1 at warm-up 96, h=3: `results-holdout-v1.md` gives -4.2 pp; the CSV gives -0.04150, which is -4.1 pp.
- R1 at warm-up 48, h=6: the holdout document gives p 0.093; the CSV gives 0.0925 (0.092).
- FACI, instant minus delayed feedback, hold-out: the holdout document gives +6.5 pp; the CSV and the robustness document give +6.4 pp (0.0644). The upper limit of the DRACP interval is 6.4 in the CSV (0.0645) and 6.5 in the robustness document.
- The p-values reported for R1 in the source documents are the unadjusted bootstrap p-values (the secondary contrast has no Holm column in the CSV), although rule R1 is written with "Holm p". See Section 6.2.

**Items marked [VERIFY] or [CITATION NEEDED] in this file.**

- [VERIFY] Whether commit `0ff08d8` or `1480604` carries the fourth protocol entry (Sections 5 and Appendix C).
- [VERIFY] The exact command lines of runs `explore_v2_ncal96` and `diag_instant_h12` (Section 9).
- [CITATION NEEDED] Statements about inflation forecast uncertainty in emerging markets (Section 2.4 and Section 1), including the Dallas Fed working paper, [CITATION NEEDED: verify authors and title].
- [CITATION NEEDED] ARIMA/ARMA modelling and the AICc criterion (Section 4.2).
- [VERIFY] The description of DRACP's internals in Section 2.3 (inferred from the package configuration, not from the paper).
- [VERIFY] Bibliographic details in `references.md`.
- Wherever Section 6 reports a width or interval-score advantage of ACI, it holds on the hold-out panel and not in the exploratory data at h=3; keep this qualification if the text is shortened.

**Procedural boundary to keep in view.** Hold-out countries are untouched with respect to countries only. The methods, contrasts and horizons were chosen on the 13 design countries. The author had seen the post-2025-06 months of the 13 countries before the amendments. The stress analysis and S1-S4 are secondary. The run on the post-2025-06 months of the 13 countries is degenerate and is not used.

---

## Abstract

Prediction intervals for inflation are used for decisions in commodity-dependent economies, but it is not known whether adaptive conformal methods that perform well on euro-area and US data keep their nominal coverage there. We build a multi-horizon (1, 3, 6 and 12 months) calibration benchmark of split, rolling-window, adaptive (ACI, FACI), conformal PID and regime-aware (DRACP) intervals at nominal level 0.90, using monthly IMF consumer price indices for 13 design economies and 7 hold-out economies chosen by a fixed rule. The primary outcome is the calibration error (CE), the mean over countries of |coverage - 0.90|. Contrasts are tested with a moving-block bootstrap and Holm correction, equivalence of DRACP and ACI with two one-sided tests and a 2 percentage-point margin, and decision rules R1-R5 were committed before the hold-out run. Adaptive methods were better calibrated than a split calibration performed once in every run, but rule R1 was met only at a 96-month warm-up, which is a sensitivity run, and not at the primary 48-month warm-up (ACI minus split at h=3: -3.0 pp, p=0.054). An advantage of ACI over a rolling window was not shown (Holm p 0.35 and 1.0). DRACP against ACI is inconclusive: equivalence within 2 pp holds at warm-up 48 and not at 96. The power rule R5 leaves all four primary contrasts inconclusive. At the 12-month horizon all methods under-cover (0.83 to 0.88 pooled); releasing outcomes immediately raised ACI coverage by 2.4 pp (95% CI -0.1 to 4.8) on the hold-out panel, below the pre-registered 3 pp threshold. The contribution is a benchmark with null outcomes recorded in advance, a clear result against one-shot calibration, a feedback-delay diagnostic and an open reproducible pipeline. The hold-out countries are untouched only with respect to countries; methods and horizons were chosen on the design countries.

---

## 1 Introduction

Central banks, finance ministries and firms in commodity-dependent economies use inflation forecasts, and a forecast is useful for decisions only together with a statement of its uncertainty. A prediction interval with a nominal level of 90 percent makes a specific claim: in about nine cases out of ten the realised value should fall inside it. Whether this claim holds in practice is the question of calibration, and it can be checked directly against realised data. It is not guaranteed by the forecasting model, because the model's own error distribution is estimated from a past that may not resemble the future.

Commodity-dependent economies are a demanding setting for calibration. Their price levels are exposed to exchange-rate movements and to commodity prices, and their inflation regimes can change within a few years. [CITATION NEEDED: empirical evidence on the volatility and regime changes of inflation in commodity-dependent economies.] A calibration made once on a past window may therefore fail later, and a method that adapts the interval width online is a natural candidate. Conformal prediction (Vovk, Gammerman and Shafer, 2005) gives distribution-free finite-sample coverage under exchangeability, which time series violate. Adaptive conformal methods (Gibbs and Candes, 2021, 2024; Angelopoulos, Candes and Tibshirani, 2023; Bhatnagar et al., 2023) were designed for that case, and a recent regime-aware variant, DRACP (Oancea, 2026), reports gains on euro-area inflation. Whether these results transfer to commodity-dependent economies, and at multi-month horizons, has not been tested to our knowledge. [CITATION NEEDED: no systematic literature search was run; this statement is based on the author's reading only.]

**What is done.** We construct a rolling-origin benchmark for the cumulative h-month log growth of the consumer price index, at horizons 1, 3, 6 and 12 months. Six interval methods (split, rolling, ACI, FACI, conformal PID, DRACP) are placed on top of point forecasts, with a nominal level of 0.90 and with outcome feedback delayed by h months, as it is in real use. The panel has 13 economies used to design the study and 7 hold-out economies that no forecast had been computed for before the pre-registered hold-out run. The primary outcome is calibration error, defined per country as the absolute difference between empirical coverage and 0.90 and averaged over countries. Pooled coverage is reported but not used as the primary outcome, because opposite deviations of different countries can cancel in a pooled average. The decision rules for the hold-out run (R1 to R5) were written in the repository before the run, and the outcomes are reported exactly as the rules classify them.

**Summary of findings, stated plainly.**

1. Adaptive methods were better calibrated than split conformal calibrated once on the first months and never updated. The direction is the same in the exploratory data, in the hold-out panel at both warm-up sizes, for three base forecasters, and after removing any single country. The pre-registered rule R1, however, was met only at the 96-month warm-up, which is a sensitivity run and is not promoted to the primary result. At the primary 48-month warm-up the result for ACI minus split at h=3 was -3.0 pp with p=0.054.
2. An improvement of ACI over a rolling-window conformal method was not shown (R2). Point estimates are negative (about 1 to 3 pp of calibration error in most settings) and their intervals include zero in the primary run.
3. For DRACP against ACI the outcome is inconclusive (R3): equivalence within 2 pp was shown at warm-up 48 and not at warm-up 96. No advantage of DRACP over ACI was detected in this configuration.
4. All four primary contrasts are inconclusive under the power rule R5, because the minimum detectable difference is undefined on the full hold-out sample.
5. At the 12-month horizon every method under-covers. Delayed feedback accounts for part of the shortfall, but the pre-registered threshold (R4) was not met for ACI: +2.4 pp against 3 pp required, with an interval that includes zero.

**What is not claimed.** This work does not show that adaptive methods are better than rolling windows, and it does not show that DRACP fails or does not transfer. Most pre-registered rules returned null or inconclusive outcomes, and a null outcome here is not evidence of equality. The hold-out countries are untouched with respect to countries only (Section 5).

**Contributions.** (1) A calibration benchmark on 20 economies with calibration error, interval score, width and power-aware inference, where the null outcomes were fixed in advance. (2) A clear result against one-shot calibration. (3) A diagnostic of the effect of delayed feedback at the 12-month horizon. (4) An open pipeline with dated hashed data snapshots, tests and a committed protocol, and a platform module that serves calibrated inflation intervals.

The remainder of the paper is organised as follows. Section 2 reviews related work. Section 3 describes the data, and Section 4 the methods. Section 5 states what was fixed before which run. Section 6 gives the results, Section 7 discusses them, Section 8 lists limitations, and Section 9 describes how to reproduce the work.

---

## 2 Related work

### 2.1 Conformal prediction for time series

Conformal prediction (Vovk, Gammerman and Shafer, 2005) turns any point predictor into a prediction set whose coverage is guaranteed in finite samples when the data are exchangeable. In the split variant, residuals on a held-out calibration set define a quantile, and the interval is the point forecast plus or minus that quantile. Time series are not exchangeable, and the guarantee does not hold in general. Barber, Candes, Ramdas and Tibshirani (2023) give a coverage bound beyond exchangeability, using weights that reflect how far the data depart from it. Xu and Xie (2021) propose a conformal interval for dynamic time series built on ensembles. Zaffran et al. (2022) study adaptive conformal predictions for time series and the role of the learning rate. A simple practical response is to compute the quantile only from the most recent residuals, which we call rolling conformal.

### 2.2 Adaptive methods: ACI, FACI, conformal PID and SAOCP

Adaptive conformal inference (ACI; Gibbs and Candes, 2021) treats the miscoverage level as a quantity updated online. After each outcome, the working level moves by a step size times the difference between the target miscoverage and the realised miss indicator, so that the long-run frequency of misses approaches the target level without assumptions on the data. The step size is a tuning choice. FACI (Gibbs and Candes, 2024) aggregates several step sizes to avoid choosing one. Conformal PID control (Angelopoulos, Candes and Tibshirani, 2023) treats the problem as control of a quantile and combines proportional, integral and forecasting components. SAOCP (Bhatnagar et al., 2023) uses strongly adaptive online learning. The present benchmark includes ACI, FACI and conformal PID. SAOCP is implemented in the released `dracp` package and was run in a reproduction check (Section 5.1) but is not part of the panel benchmark.

These guarantees concern long-run miss frequency. They do not guarantee that every country, every horizon and every window is calibrated, and they are not stated for the situation in which the outcome of an h-step forecast is revealed only h months later. How that delay affects the adaptive updates is an empirical question that this paper addresses with a diagnostic (Section 6.5).

### 2.3 Regime-aware calibration: DRACP

DRACP (Dynamic Regime-Aware Conformal Calibration; Oancea, 2026, arXiv:2608.17079) combines regime and scale models with a weighted, time-decayed calibration set and an adaptive correction of the miscoverage level [VERIFY: this description is inferred from the package configuration used here, not from a reading of the paper]. It is evaluated by its authors on economic series, including euro-area inflation. Over 48 series and 20 seeds, the authors report mean coverage of 0.890 for DRACP, 0.884 for ACI, 0.883 for FACI, 0.868 for SAOCP, 0.841 for rolling, 0.825 for conformal PID and 0.781 for split conformal at nominal 0.90 (as recorded in `experiment-protocol.md`). The authors state that the advantage is specific to one-step forecasts. This benchmark uses the released package through its public streaming interface (Section 4.3). Our setting differs from theirs in three respects: the point model is refitted on an expanding window instead of being fitted once, the target is the cumulative h-month log growth instead of the annual rate, and the economies are commodity-dependent.

### 2.4 Inflation forecast uncertainty in emerging markets

The literature on inflation forecasting in emerging and commodity-dependent economies is large, and the project notes refer to a Dallas Fed working paper on emerging-market inflation forecasting [CITATION NEEDED: verify authors and title]. We did not run a systematic literature search, and we make no claim about the state of that literature beyond the following. Intervals for inflation are commonly derived from the forecast model's own error distribution, and we include the native ARIMA and ETS intervals in the engine as a null comparison (they are computed but are not reported in the results documents used for this draft). [CITATION NEEDED: studies of the calibration of inflation prediction intervals in emerging markets.]

### 2.5 Positioning

The paper is a transfer and benchmark study, not a new method. Its aim is to measure, with pre-recorded decision rules, whether the published ranking of conformal methods holds on a different panel, and to report null outcomes as such. The closest work is the DRACP paper (Oancea, 2026). We do not replicate its setup; we reproduce it only partially (Section 5.1).

---

## 3 Data

### 3.1 Sources

All series are monthly. Consumer price indices (all items) come from the IMF (series `M.<country>.PCPI_IX`), obtained through DBnomics for the first snapshot and through the IMF SDMX API (`api.imf.org`) for the second. The exchange rate is the monthly average of domestic currency per US dollar (IMF IFS, `ENDA_XDC_USD_RATE`). The Brent crude price is from the IMF primary commodity price series (`M.W00.POILBRE.USD`); in the direct API it requires the area code `G001`. The exchange rate and Brent enter the feature set of the LightGBM forecaster, and the exchange rate defines the stress measure of the secondary analysis.

### 3.2 Countries

**Design countries (13).** Core long-history group: Brazil (BR), Mexico (MX), Chile (CL), Colombia (CO), Peru (PE), South Africa (ZA), Indonesia (ID). Regional group: Kazakhstan (KZ), Russia (RU), Azerbaijan (AZ), Uzbekistan (UZ). Control group: Nigeria (NG), Mongolia (MN). These countries were used to shape the design (the stress rule, the start date, the contrasts and the horizons). The documents reviewed do not state a written criterion for calling these countries commodity-dependent (see Section 8).

**Hold-out countries (7).** Bolivia (BO), Paraguay (PY), Uruguay (UY), Ghana (GH), Georgia (GE), Kyrgyzstan (KG), Angola (AO). The candidate list (14 names, in a fixed order) and the eligibility rule were written in `scripts/thesis/fetch_holdout.mjs` before any forecast was computed for these countries. The rule required at least 220 months of IMF monthly CPI and of exchange rate per US dollar within 2000-01 to 2026-06, with at most 3 missing CPI months. The first 10 eligible candidates were to be kept. Only 7 candidates met the rule (ZM, AM, TZ, UG, KE and IQ start in 2009 or 2010; PG has no CPI series), so the panel has 7 countries and the rule was not relaxed. Target months of the hold-out panel run from 2009-02 to 2026-06. All months of these countries are labelled `holdout`.

### 3.3 Snapshots

Two dated snapshots with SHA-256 hashes were taken from the IMF (Appendix B).

- `snapshot.json`: CPI, exchange rate and Brent for the 13 design countries from DBnomics (indexed 2025-08-31). SHA-256 `d01b8360c4167f0b3d829f3d7af0438c36fe858c9f2e2745e9b258039cc2d739`.
- `confirmatory.json`: CPI, exchange rate and Brent from 2024-01 onwards, fetched directly from the IMF SDMX API after the protocol was committed. SHA-256 `e2001e5aad677567a7d572a6cf1d22929b18bfe1d3c1ad94bff47b75a3981a74`. CPI runs to 2026-08 (PE, NG), 2026-09 (KZ, RU, AZ, UZ, CO, BR, MX, ZA) or 2026-10 (CL, MN, ID).
- `holdout.json`: CPI and exchange rate of the 7 hold-out countries, SHA-256 `0245eab6c75d6bd7fe800fe5978a7ca5670550dff4b3f23e817177f9c6fae9ac`. Brent for the hold-out run is taken from the main snapshot files.

The overlap of the two snapshots (2024-01 to 2025-05) is identical for the exchange rate, Brent and CPI except for three differences recorded in the protocol: a constant rebasing of the index level for Kazakhstan (ratio 0.477) and Nigeria (ratio 0.131), small revisions for Russia (up to 0.07 percent) and Mongolia (up to 0.05 percent), and a methodology break in the Nigerian series at 2025-01.

### 3.4 Rebasing and the Nigerian methodology break

Because the two snapshots use different index bases, the loader chains them on the CPI level at the last month they have in common (`chain_cpi` in `exp/data.py`). The earlier snapshot wins on overlap, and later months are rescaled by a constant factor, so growth rates are unaffected. An early version of the loader merged the snapshots without rescaling and produced a false 74 percent fall in the Kazakhstani index; this was found and fixed before the run, and a regression test now checks that no country has a monthly log jump above 0.15 at the junction. For Nigeria, the CPI index falls from 113.9 to 110.7 in rebased terms between 2024-12 and 2025-01, which reflects a change in methodology and not a price movement. Months from 2025-01 are therefore not appended and the Nigerian series ends at 2024-12.

Russia has 30 missing CPI months. Its series is cut into stretches of consecutive months and only stretches of at least 60 months are used; in the runs reported here Russia enters as one unit (`RU`) in the 13-unit panel. Series that start later than 2000 (KZ, AZ, NG from 2005; MN from 2006; UZ, PE from 2010) enter once they have 60 months of history.

### 3.5 Exploratory and confirmatory samples

The label of each evaluated row depends on its target month. Target months before 2025-07 are labelled exploratory. Target months from 2025-07 on the 13 design countries are labelled confirmatory in the code. After the amendments (Section 5), the confirmatory months of the 13 countries cannot carry a claim: with at most about 16 months per country, there are two or three independent blocks. The main confirmatory pool became the 7 hold-out countries, all of whose months are labelled `holdout`. The run on the post-2025-06 months of the 13 countries (`confirm13`) is degenerate (Section 6.7) and is not used.

---

## 4 Methods

### 4.1 Target

For country c, origin month t and horizon h in {1, 3, 6, 12}, the target is

y(t, h) = 100 * ln(CPI(t+h) / CPI(t)),

the cumulative h-month log growth of the index, in percent. Working in log differences makes the target invariant to the index base. A target is defined only if CPI(t+h) lies in the same stretch of consecutive months as CPI(t).

### 4.2 Point forecasters

Forecasts are made at one origin per month with an expanding window, using only information dated at or before the origin. Hyperparameters are fixed in advance and not tuned on the test period. Tests check that corrupting all data after the origin does not change a forecast.

- **Naive A:** h times the last observed monthly inflation rate.
- **Naive B:** the last observed cumulative h-month growth (equal to the year-on-year rate at h=12).
- **ETS:** exponential smoothing in the state-space framework (Hyndman et al., 2002) with additive error, no trend and additive seasonality (period 12), fitted to monthly inflation. The h monthly forecasts are summed.
- **ARIMA:** an ARMA(p, q) model with p and q in {0, 1, 2}, a constant and two annual harmonics as regressors, fitted to monthly inflation. The order is chosen by AICc every 12 origins and the parameters are re-estimated at every origin; the h monthly forecasts are summed. [CITATION NEEDED: ARMA/ARIMA modelling and the AICc criterion.]
- **LightGBM** (Ke et al., 2017): a direct forecast, one model per horizon, 200 trees, learning rate 0.05, 8 leaves, subsample 0.8, column sample 0.8, refitted every 3 origins. Features are the current monthly inflation and its lags at 1, 2, 5 and 11 months, rolling means over 3 and 12 months, the exchange-rate and Brent log changes (current and lagged one month), and the sine and cosine of the calendar month. LightGBM is the primary base model in all contrasts reported below.

Forecast origins start no earlier than 2000-01, because the 1990s hyperinflation of Brazil and Mexico made native ARIMA intervals and LightGBM unusable in a check. Each country needs 60 months of training history. A failed ETS or ARIMA fit carries the previous point forecast forward and is counted; in the exploratory run, no fit fell back (0 of 7628 rows per model). The conformal interval methods were run on three base models: LightGBM, ARIMA and naive B. A foundation-model forecaster (Chronos) was listed in the protocol as an optional extension; the engine contains no such module, and no result with it is reported.

### 4.3 Interval methods

All six methods are run through the streaming interface of the released `dracp` package (`fit`, `predict_one`, `update_one`) with a pass-through base model. The first feature column is our own point forecast, and the package uses it unchanged. Nominal level 1 - alpha = 0.90 (alpha = 0.10).

- **Split conformal:** the quantile of absolute residuals on the warm-up window, fixed and never updated.
- **Rolling conformal:** the quantile of the most recent 120 absolute residuals.
- **ACI** (Gibbs and Candes, 2021): the quantile level is updated online with step 0.02 on a rolling window of 120 residuals. After each released outcome, the working miscoverage level moves by 0.02 times (0.10 minus the miss indicator of the interval that was actually issued).
- **FACI** (Gibbs and Candes, 2024): package defaults.
- **Conformal PID** (Angelopoulos, Candes and Tibshirani, 2023): package defaults.
- **DRACP** (Oancea, 2026): the package configuration used in the reproduction script (calibration window 120, target window 24, temporal decay 0.985, adaptive bandwidth from a grid, 3 regimes, FACI control of the level). DRACP trains its regime and scale models on the first half of the warm-up rows and calibrates on the second half; the other methods use all warm-up rows for calibration.

Infinite radii that arise when there are too few scores for the requested level are capped at 10 times the largest absolute calibration score seen so far, and the number of capped intervals is recorded. An independent implementation of ACI (`OwnACI`) is used in a test that compares it with the package at h=1. Native intervals of ARIMA (Gaussian, from psi-weights) and ETS (simulated, 400 paths) are computed as a parametric null comparison.

### 4.4 Delayed feedback

For an h-step forecast made at origin j, the outcome is observed only at month j+h. When predicting at origin k, the update for origin j is therefore applied only if j + h <= k, and the result stored at prediction time is passed back so that the miss indicator is that of the interval actually issued. This is the setting in real use, and it is what the code implements by default. The first rows form the warm-up: rows 0 to n_cal-1 are the initial calibration set, and the first evaluated origin is n_cal + h - 1, so that every warm-up row has been released. The h-1 rows between them receive no interval and no feedback.

A diagnostic option releases each outcome at origin + 1 as if the horizon were 1, even though the real outcome is observable only after h months. It is not a valid forecasting setup. It is used only to isolate the effect of delay (Section 6.5), and its output directory carries a marker file that labels it as a diagnostic.

### 4.5 Evaluation protocol

The evaluation uses a rolling origin with one origin per month. For each unit (a country, or a stretch of Russia), the evaluated rows are the origins from n_cal + h - 1 on. The primary warm-up is n_cal = 48 residuals; a sensitivity run uses n_cal = 96, applied to all methods. Coverage is the share of origin months where the realised target lies in the interval. The interval (Winkler) score (Winkler, 1972; see also Gneiting and Raftery, 2007) of an interval [l, u] for outcome y is

W = (u - l) + (2 / alpha) * max(l - y, 0) + (2 / alpha) * max(y - u, 0),

so that with alpha = 0.10 an outcome outside the interval is penalised by 20 times the distance by which it is missed, in addition to the width. Lower is better. Mean width is reported in percentage points of cumulative growth. Point forecasts are evaluated by mean absolute error and root mean squared error relative to the naive baselines.

### 4.6 Calibration error and why pooled coverage is not enough

For a unit u and a method m, let cov(u, m) be the empirical coverage. The **calibration error** (CE) is |cov(u, m) - 0.90|. A contrast between methods m1 and m2 is

T(m1, m2) = mean over units of [ CE(u, m1) - CE(u, m2) ],

with equal weight for each unit and only (unit, origin) cells present for both methods. A negative T means m1 is better calibrated. The reason for using CE instead of pooled coverage is that pooled coverage lets opposite deviations cancel. In the exploratory data at h=3, split conformal covers 1.000 in Indonesia and 0.822 in Peru. A pooled average of these is close to nominal, although neither country is calibrated. Moreover, when a method over-covers, a lower coverage means better calibration, so a difference in pooled coverage does not tell which method is closer to 0.90. The absolute value in CE is biased upward by sampling noise, particularly for small samples per unit; the bias largely cancels in T because both methods have the same sample in each unit. Percentile bootstrap intervals for T need not be symmetric around the estimate, because CE is a nonlinear function of coverage.

The original contrasts defined in the first protocol draft (difference of pooled coverage) are kept in the report as secondary results.

### 4.7 Contrasts and the decision family

The primary family (after the fourth protocol amendment) has four tests: ACI minus rolling conformal, and DRACP minus ACI, each at h=3 and h=6, with LightGBM as base model, pooled over countries. Holm's procedure (Holm, 1979) controls the family-wise error rate over these four tests. ACI minus split conformal is a secondary, descriptive contrast and is not part of the Holm family. h=1 and h=12 are descriptive. The Winkler contrast is the relative difference of the equal-unit-weight mean Winkler score, reported with unadjusted p-values as descriptive. The standard deviation of coverage across units is reported next to CE.

### 4.8 Block bootstrap

Origins of consecutive months overlap in their h-step errors and are dependent across countries through common shocks. The bootstrap therefore resamples origin calendar months in moving blocks (Kunsch, 1989), with the same month indices for all units (joint resampling), and a block length of max(h, 12) months. The choice of 12 follows from the memory of ACI, roughly 50 months at step 0.02, and from the overlap of errors. The per-unit statistics are recomputed on each replicate. Reported are the estimate, a 95 percent percentile interval and a two-sided centred bootstrap p-value (the share of replicates with |T* - T| at least |T|). The primary contrasts use 2000 replicates, so the smallest attainable p-value is about 0.0005. With a block length of 12 and fewer than about 16 months per unit, the bootstrap is degenerate (Section 6.7).

### 4.9 Equivalence testing (TOST)

A non-significant difference is not evidence of equality. DRACP against ACI is therefore also tested for equivalence with **two one-sided tests** (TOST; Schuirmann, 1987). The equivalence margin is 2 pp of CE. Two null hypotheses are tested, T <= -2 pp and T >= +2 pp, each against the bootstrap distribution shifted to the boundary. Equivalence is declared if the larger of the two p-values is below 0.05; otherwise the verdict is "not shown". The margin of 2 pp is fixed in advance and is not justified beyond that. TOST is reported separately and is not part of the Holm family.

### 4.10 Power and minimum detectable difference

The **minimum detectable difference** (MDE) is the smallest true reduction delta of CE for which the test has a power of at least 0.80 at the level used. The simulation (`exp/power.py`) keeps the observed hit pattern of the baseline method (so that cross-country common shocks and the overlap of errors stay in the data) and constructs the comparison method by thinning or thickening its hits so that its CE is lower by delta in each unit, on the same side of 0.90, with fixed uniform draws shared across delta values. Each simulated dataset is tested with the same centred block bootstrap as the real analysis. The test level is 0.05/4 for every contrast (the first Holm step), which gives a conservative bound. The MDE is reported in percentage points of mean CE. It is undefined if the power at 10 pp is still below 0.80. A contrast with an MDE that is undefined or above 7 pp is reported as inconclusive regardless of its p-value (rule R5). The MDE is also computed on random 15-month windows of the data, with 60 windows, to judge panels of the size of the post-2025-06 months.

### 4.11 FX-stress definition

Stress is secondary. The driver is the monthly exchange rate. For each country and month t, d(t) = ln(FX(t)/FX(t-1)); over the 60 preceding months (t excluded), m is the median and s = max(1.4826 * MAD, 0.005) the robust scale of d; z(t) = (d(t) - m)/s. A month is a shock event if |z(t)| exceeds 3, and the shock window is the event month and the 3 following months, with overlapping windows merged into episodes. For the continuous version used in the main stress analysis, stress at month t is the maximum of |z| over t-3 to t, and coverage is reported by within-country decile of stress at the forecast origin. The parameters were frozen on 2026-11-18, before any forecast was run, and the rule is not tuned.

---

## 5 Pre-registration and procedure

### 5.1 What "pre-registered" means here

The protocol (`experiment-protocol.md`) and the shock definition (`shock-definition.md`) are committed documents in the project repository. Changes are logged in their "Changes" sections with a date and a reason. "Pre-registered" in this paper means that a rule was committed to the repository before the run it governs. It does not mean registration in an external registry: the author is a single person, and all entries are dated 2026-11-18 or 2026-11-19. The order of events is attested by the commit history and not by an independent timestamp.

### 5.2 Sequence

The commit hashes below are taken from the protocol and results documents where they are stated there, and otherwise from `git log` (marked "git log").

1. **Shock rule frozen** (2026-11-18; git log `58871dc`), before any forecast. Validity checks were run afterwards (git log `9c0bdb7`) and are described in Section 5.4.
2. **Protocol draft 1** (git log `810a60c`), written before any forecast or interval had been computed. A committee review scored it 5.5 out of 10 (first change entry), and the claim hierarchy, FACI and conformal PID, reproduction tolerance, block length at least h, reduced primary tests and an MDE threshold were added before any forecast. A second entry added the second snapshot and the Nigerian break and restricted confirmatory analysis to the pooled panel. A partial reproduction of DRACP was recorded (git log `89996d2`) and the topic was fixed (git log `cb6de1b`).
3. **Third entry and the exploratory run v1.** Implementation decisions of the engine (start 2000-01, warm-up 48, window 120, ACI step 0.02, snapshot chaining) were fixed before results existed. The first run was exploratory only (`--start 2000-01 --end 2025-06`), so that no target month from 2025-07 could enter, and was made at code commit `2229076`. Results: `results-exploratory-v1.md` (git log `bf78f53`).
4. **Fourth entry, amendments after the exploratory result and before any hold-out forecast.** Pooled-coverage contrasts were replaced by calibration error as the primary outcome; the reference changed from split to rolling conformal; DRACP against ACI became an equivalence question with a 2 pp margin; a fair DRACP sensitivity with warm-up 96 was added; the 7 hold-out countries became the main confirmatory pool; block length became at least 12; and the stress analysis was kept exploratory. The text of the entry states that the changes are motivated by logical defects of the design and not by significance. The commit that carries this entry is `0ff08d8` by git log message, while `results-holdout-v1.md` cites `1480604` for the fourth and fifth entries [VERIFY which commit carries the fourth entry].
5. **Fifth entry, hold-out run specification and decision rules R1-R5** (commit `1480604`), before any forecast was computed for the 7 hold-out countries. The runs were (A) warm-up 48 (primary), (B) warm-up 96 (sensitivity) and (C) an instant-feedback diagnostic at h=12; the original 13 countries to 2026-09 were listed as a supplementary pooled check. The entry states that none of the rules is changed after the result is seen.
6. **Hold-out run** and its results (`results-holdout-v1.md`; git log `46a2474`). First and only look at the 7 countries.
7. **Sixth entry, robustness analyses S1-S5** (commit `552fa67`), written after the hold-out result and before they were computed. They are secondary, do not replace R1-R5, and no threshold was changed. Their results are in `results-robustness-v1.md` (git log `de93501`).

The exploratory results with the amended contrasts at both warm-ups (`explore_v1` and `explore_v2_ncal96`) were already known when R1-R5 were written, so the rules were set by an author who knew how the design countries behaved.

### 5.3 Procedural boundary

The hold-out countries are untouched with respect to countries only. The set of methods, the form of the contrasts, the horizons, the 2 pp margin and the 3 pp and 7 pp thresholds were chosen on the 13 design countries. The author had also seen the post-2025-06 months of the 13 design countries before the amendments. The hold-out evaluation is therefore a test on new countries and not a fully blind test of the design. The stress analysis and the analyses S1-S4 are secondary. The run on the post-2025-06 months of the 13 countries is degenerate and is not used.

### 5.4 Validity check of the shock rule and why stress is secondary

A committee review scored the frozen FX-based shock rule 5.5 out of 10, objecting that an exchange-rate flag measures currency turbulence and not an inflation shock. Two checks were run on the 13 design countries; they are exploratory because the same countries shaped the design.

The first check, with the discrete label (threshold 3, window of 3 months), compared the share of the top-decile one-step errors of a naive forecast that falls inside shock windows with the share of shock months (Table 1). The lift is below the committee's bar of 2. Nigeria and Uzbekistan have 35 to 41 percent of months in shock windows, which points to an exchange-rate-regime artefact.

**Table 1. Validity check 1 (discrete label)**

| Sample | Label | Shock share | Recall | Lift | Permutation p |
|---|---|---|---|---|---|
| All evaluable months, 13 countries | target | 0.204 | 0.382 | 1.87 | 0.0005 |
| All evaluable months | origin | 0.204 | 0.364 | 1.79 | 0.0005 |
| Since 2015-09 | target | 0.172 | 0.288 | 1.68 | 0.0015 |
| Since 2015-09 | origin | 0.171 | 0.255 | 1.49 | 0.0125 |

The second check, with the continuous stress variable, found a pooled within-country rank correlation with the naive one-step error of 0.075 (permutation p = 0.001) for origin stress over all months, 0.091 for target stress, and 0.050 (p = 0.0495) for origin stress since 2015-09. The relation is not monotone: deciles 2 to 8 are flat, and the share of top-decile errors is 0.134 in decile 9 and 0.235 in decile 10 (base rate 0.10), while decile 1 is also raised (0.142) and is not explained.

Because the association is weak and concentrated in the upper tail, the main contribution does not depend on shocks. Stress is analysed as a continuous variable with the discrete windows as a check, parameters of the rule were not tuned to raise the lift, and the upper decile was not promoted to a primary threshold after the fact. Disclosures recorded with the rule: the threshold of 3 was chosen after looking at episode counts for 2.5, 3 and 3.5; the 60-month lookback for Kazakhstan before mid-2020 includes years of a managed exchange rate, which lowers the scale and produces more flags; and of the six Kazakhstani episodes after 2015-09, only three are linked to a known event. Kazakhstan has fewer than 10 independent episodes after 2015-09 (6 at threshold 3), so it is a case study inside a pooled panel and not a stand-alone inferential unit.

### 5.5 The decision rules R1-R5

The rules (Appendix A) apply to the base model LightGBM, the primary family with Holm correction over four tests, pooled over the 7 hold-out countries, with a block length of 12. Section 6.2 applies them as written.

---

## 6 Results

All results below use LightGBM as base model and nominal level 0.90, unless stated otherwise. A negative CE contrast means the first method is better calibrated. The exploratory results are exploratory and carry no confirmatory claim.

### 6.1 Exploratory results

Run `explore_v1`: 13 units, origins from 2000-01 and target months to 2025-06, warm-up 48. It took 695 seconds. Pooled coverage by method and horizon is in Table 2. Bootstrap 95 percent intervals are wide: for ACI at h=3 they are [0.879, 0.930], and at h=12 [0.797, 0.914].

**Table 2. Pooled coverage, exploratory, 13 units, warm-up 48 (every unit-month weighted equally)**

| Method | h=1 | h=3 | h=6 | h=12 |
|---|---|---|---|---|
| Split conformal | 0.946 | 0.937 | 0.917 | 0.864 |
| Rolling conformal | 0.917 | 0.916 | 0.900 | 0.869 |
| ACI | 0.908 | 0.906 | 0.899 | 0.864 |
| FACI | 0.913 | 0.904 | 0.878 | 0.825 |
| Conformal PID | 0.917 | 0.907 | 0.883 | 0.837 |
| DRACP | 0.915 | 0.909 | 0.892 | 0.863 |

The number of unit-months is 2024, 1972, 1894 and 1738 at h=1, 3, 6 and 12.

The calibration-error contrasts (Table 3) are shown at both warm-ups. At warm-up 48, ACI minus rolling was -2.2 pp at h=3 and -1.5 pp at h=6, with unadjusted p-values of 0.030 and 0.019 but Holm-adjusted p-values of 0.090 and 0.078, so neither survives the correction for the family. ACI minus split (secondary) was -4.6 pp at h=3 (95% CI [-5.0, -1.4], unadjusted p 0.001) and -3.4 pp at h=6 (p 0.0025). DRACP minus ACI was +0.2 pp and -0.2 pp, within noise. Equivalence within 2 pp was shown at warm-up 48 (maximum one-sided p 0.0085 at h=3 and 0.0135 at h=6) and not shown at warm-up 96 (0.128 and 0.146). At warm-up 96, DRACP was wider than ACI: its Winkler score was higher by 33.2 percent at h=3 (95% CI [12.1, 75.9], unadjusted p 0.049) and 19.9 percent at h=6 (95% CI [6.8, 46.2], unadjusted p 0.054). Equivalence in the exploratory data is therefore not stable across warm-up sizes.

**Table 3. Calibration-error contrasts, exploratory (pp of CE; 95% bootstrap CI; Holm p for the primary family)**

| Warm-up | h | Contrast | Family | T (pp) | 95% CI | p | Holm p |
|---|---|---|---|---|---|---|---|
| 48 | 3 | ACI - rolling | primary | -2.2 | [-2.7, 0.05] | 0.030 | 0.090 |
| 48 | 3 | DRACP - ACI | primary | +0.2 | [-1.2, +1.0] | 0.70 | 1.0 |
| 48 | 6 | ACI - rolling | primary | -1.5 | [-2.1, -0.1] | 0.019 | 0.078 |
| 48 | 6 | DRACP - ACI | primary | -0.2 | [-2.0, +1.3] | 0.78 | 1.0 |
| 48 | 3 | ACI - split | secondary | -4.6 | [-5.0, -1.4] | 0.001 | - |
| 48 | 6 | ACI - split | secondary | -3.4 | [-4.7, -0.9] | 0.0025 | - |
| 96 | 3 | ACI - rolling | primary | -1.3 | [-2.0, +0.1] | 0.039 | 0.13 |
| 96 | 3 | DRACP - ACI | primary | +0.1 | [-2.8, +1.9] | 0.95 | 1.0 |
| 96 | 6 | ACI - rolling | primary | -1.5 | [-2.8, -0.0] | 0.033 | 0.13 |
| 96 | 6 | DRACP - ACI | primary | +0.2 | [-2.9, +1.6] | 0.85 | 1.0 |
| 96 | 3 | ACI - split | secondary | -3.9 | [-4.3, -1.0] | 0.0055 | - |
| 96 | 6 | ACI - split | secondary | -2.9 | [-4.2, +0.4] | 0.046 | - |

Other exploratory observations (all exploratory):

- **Protocol-form contrasts (difference of pooled coverage).** ACI minus split was -3.0 pp at h=3 (95% CI [-4.1, -1.9], Holm p 0.004) and -1.8 pp at h=6 ([-3.3, -0.5], Holm p 0.036). The negative sign must not be read as "ACI is worse": split conformal over-covers at short horizons (0.946, 0.937), so a lower ACI coverage is closer to 0.90. DRACP minus ACI was +0.25 pp ([-0.7, +1.2], Holm p 0.67) at h=3 and -0.74 pp ([-2.1, +0.8], Holm p 0.67) at h=6.
- **Width.** DRACP intervals were wider than ACI at h=3 (mean width 4.97 against 4.28) and at h=12 (24.3 against 15.5).
- **Per-country spread.** At h=3 split coverage ranges from 0.822 (Peru) and 0.827 (Kazakhstan) to 1.000 (Indonesia); ACI ranges from 0.886 to 0.934. At h=12 ACI coverage ranges from 0.655 (Peru) and 0.716 (Nigeria) to 1.000 (Uzbekistan).
- **Long horizon.** At h=12 every method under-covers (0.82 to 0.87) and the adaptive methods do not repair it.
- **Point forecasts.** Mean absolute error relative to naive B (pooled) was 0.74 (ARIMA), 0.72 (ETS) and 0.74 (LightGBM) at h=3, 0.75, 0.76 and 0.75 at h=6, and 0.86, 0.93 and 0.91 at h=12. Naive A is worse than naive B at h of 3 or more.
- **Dependence on the base model.** ARIMA and naive B give similar ACI coverage at h=6 (0.895 and 0.908).

### 6.2 Hold-out results and rules R1-R5

The hold-out run covers 7 countries (BO, PY, UY, GH, GE, KG, AO), target months 2009-02 to 2026-06, with 205 months at h=3 and 199 months at h=6 for run A (warm-up 48) and 157 and 151 months for run B (warm-up 96). The number of unit-months in run A is 1163, 1135, 1093 and 1009 at h=1, 3, 6 and 12. Pooled coverage in run A is in Table 4.

**Table 4. Pooled coverage, hold-out, 7 countries, warm-up 48**

| Method | h=1 | h=3 | h=6 | h=12 |
|---|---|---|---|---|
| Split | 0.954 | 0.932 | 0.936 | 0.861 |
| Rolling | 0.924 | 0.918 | 0.921 | 0.872 |
| ACI | 0.914 | 0.907 | 0.908 | 0.884 |
| FACI | 0.919 | 0.910 | 0.897 | 0.835 |
| Conformal PID | 0.912 | 0.910 | 0.909 | 0.833 |
| DRACP | 0.917 | 0.904 | 0.894 | 0.865 |

The CE contrasts of the hold-out panel are in Table 5. The decision rules are applied as registered.

**Table 5. Calibration-error contrasts, hold-out (LightGBM; pp of CE; 95% bootstrap CI)**

| Warm-up | h | Contrast | Family | T (pp) | 95% CI | p | Holm p |
|---|---|---|---|---|---|---|---|
| 48 | 3 | ACI - rolling | primary | -1.6 | [-3.0, +0.5] | 0.087 | 0.35 |
| 48 | 3 | DRACP - ACI | primary | -0.1 | [-1.2, +0.9] | 0.76 | 1.0 |
| 48 | 6 | ACI - rolling | primary | -0.7 | [-2.8, +1.3] | 0.48 | 1.0 |
| 48 | 6 | DRACP - ACI | primary | -0.3 | [-1.4, +1.7] | 0.66 | 1.0 |
| 48 | 3 | ACI - split | secondary | -3.0 | [-5.4, +0.5] | 0.054 | - |
| 48 | 6 | ACI - split | secondary | -2.8 | [-3.9, +1.2] | 0.092 | - |
| 96 | 3 | ACI - rolling | primary | -1.5 | [-2.9, +0.8] | 0.148 | 0.59 |
| 96 | 3 | DRACP - ACI | primary | -0.4 | [-3.3, +1.6] | 0.76 | 0.99 |
| 96 | 6 | ACI - rolling | primary | -1.1 | [-2.5, +1.2] | 0.33 | 0.99 |
| 96 | 6 | DRACP - ACI | primary | -1.1 | [-3.8, +1.9] | 0.46 | 0.99 |
| 96 | 3 | ACI - split | secondary | -4.1 | [-5.7, -0.2] | 0.018 | - |
| 96 | 6 | ACI - split | secondary | -5.9 | [-7.6, -1.6] | 0.0025 | - |

**R1 (ACI better calibrated than split): not met in the primary run (warm-up 48); met at warm-up 96, which is a sensitivity run and is not promoted.** At warm-up 48 the CE difference ACI minus split was -3.0 pp (p 0.054) at h=3 and -2.8 pp (p 0.092) at h=6. At warm-up 96 it was -4.1 pp (p 0.018) and -5.9 pp (p 0.0025). The direction replicates in both runs. The p-values given here for the secondary contrast are the unadjusted bootstrap p-values; the CSV has no Holm column for this contrast, although R1 is written in terms of "Holm p". At warm-up 48 the rule fails even with unadjusted p-values. The pre-registered verdict is "not met" for the primary configuration, and warm-up 96 was not promoted to the primary configuration because R1 holds there.

**R2 (ACI improves on rolling): not shown.** Holm p was 0.35 (h=3) and 1.0 (h=6) at warm-up 48, and 0.59 and 0.99 at 96. On the Winkler score, ACI was 1.0 percent lower than rolling at h=3 (95% CI [-7.1, +4.1]) and 5.3 percent higher at h=6 (95% CI [+1.4, +8.1], unadjusted p 0.005; at warm-up 96, +9.2%, 95% CI [3.4, 15.3], unadjusted p 0.001). These Winkler contrasts are descriptive and unadjusted.

**R3 (DRACP against ACI): inconclusive.** Equivalence within 2 pp was shown at warm-up 48 (TOST p 0.0005 at h=3 and 0.047 at h=6) and not shown at warm-up 96 (0.062 and 0.355). Under the registered wording, "no advantage, equivalent within 2 pp" requires equivalence at both warm-ups, so the verdict is "inconclusive" and the equivalence result is not stable. DRACP minus ACI is not negative with Holm p below 0.05 at either warm-up, so "DRACP better" is also not supported. The wording used here for DRACP is therefore: no advantage over ACI was detected in this configuration; equivalence within 2 pp held at warm-up 48 but not at 96.

**R4 (delayed feedback explains the h=12 shortfall; ACI at least +3 pp): not met.** ACI coverage at h=12 was 0.884 with delayed feedback and 0.908 with instant feedback, a difference of +2.4 pp. The S3 interval for this difference is given in Section 6.5.

**R5 (power): all four primary contrasts are inconclusive.** The minimum detectable difference is undefined on the full hold-out sample at both warm-ups (`power_mde_ce.csv`): the baseline calibration error is too small for a 10 pp improvement to be attainable, so the power at 10 pp is below 0.80. On random 15-month windows of the hold-out data the median MDE is 2.6 to 3.1 pp, but 63 to 68 percent of windows have an undefined MDE (`power_mde_ce_windows15.csv`). The same full-sample MDE is also undefined in the exploratory data at warm-up 48. Under R5, a contrast with an undefined MDE is inconclusive regardless of its p-value, so none of the four primary contrasts supports a conclusion.

**Table R. Summary of outcomes**

| Rule | Outcome | Evidence |
|---|---|---|
| R1 | Not met in the primary run (warm-up 48); met at warm-up 96 (sensitivity, not promoted) | -3.0 pp (p 0.054), -2.8 pp (p 0.092) at 48; -4.1 pp (p 0.018), -5.9 pp (p 0.0025) at 96 |
| R2 | Not shown | Holm p 0.35, 1.0 at 48; 0.59, 0.99 at 96 |
| R3 | Inconclusive | TOST p 0.0005, 0.047 at 48; 0.062, 0.355 at 96 |
| R4 | Not met | +2.4 pp against the 3 pp threshold |
| R5 | All four primary contrasts inconclusive | MDE undefined on the full hold-out sample |

**What the hold-out result supports.** Adaptive methods are better calibrated than a one-shot conformal calibration, with a direction replicated in the exploratory data and in the hold-out data at both warm-up sizes, and with a strength of evidence that depends on the warm-up. It does not support the statements that adaptivity helps beyond a simple rolling window, or that DRACP is better than ACI. Per-country coverage varies widely: at h=12 the standard deviation of coverage across units is 0.058 for ACI and 0.152 for split.

### 6.3 Robustness analyses S1-S4

The analyses S1-S4 were written down after the hold-out result and before they were computed (Section 5.2). They are secondary, use only existing intervals, and qualify R1-R5 without replacing them. Settings: block length max(h, 12); S1 with 500 bootstrap replicates, S2 and S3 with 2000.

**S1, leave one country out** (LightGBM, warm-up 48). Table 8 shows the range of the contrast over removals and the number of removals that flip the sign of the full-sample estimate. The advantage of ACI over a calibration done once does not depend on any single country. The point estimate of ACI against rolling is negative for almost every removal, but its interval includes zero in the primary run, so "not shown" stands. The DRACP minus ACI estimates sit at zero and change sign when one or two countries are removed.

**Table 8. S1: range over removals (pp of CE) and sign flips**

| Contrast, h | Exploratory (13 countries) | Hold-out (7 countries) |
|---|---|---|
| ACI - split, h=3 | -5.1 to -4.2, 0 flips | -4.1 to -2.2, 0 flips |
| ACI - split, h=6 | -4.1 to -2.5, 0 flips | -3.5 to -2.1, 0 flips |
| ACI - rolling, h=3 | -2.5 to -1.8, 0 flips | -2.2 to -1.0, 0 flips |
| ACI - rolling, h=6 | -1.7 to -1.3, 0 flips | -1.3 to +0.1, 1 of 7 flips |
| DRACP - ACI, h=3 | 0.0 to +0.4, 0 flips | -0.4 to -0.1, 0 flips |
| DRACP - ACI, h=6 | -0.5 to +0.1, 2 of 13 flips | -0.7 to +0.1, 1 of 7 flips |

**S2, other base models.** The contrasts were recomputed with ARIMA and naive B as base models of the conformal methods (Table 9; T in pp of CE, unadjusted bootstrap p in brackets). ACI minus split is negative for all three base models in both samples; for naive B at h=6 on the hold-out panel it is -10.6 pp. All DRACP minus ACI equivalence tests at warm-up 48 say "equivalent" within 2 pp, except naive B at h=6 on the hold-out panel (p 0.0515); at warm-up 96 on the hold-out panel most are "not shown". The direction "ACI better than rolling" holds for every base model and both samples, but the unadjusted p-values range from 0.016 to 0.22, and none survives the correction of the pre-registered family.

**Table 9. S2: contrasts by base model (pp of CE, p in brackets)**

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

(The robustness document rounds the LightGBM hold-out DRACP minus ACI value at h=3 to -0.2; the CSV value is -0.149 pp, shown as -0.1 in Table 5.)

**S4, calibration against width** (hold-out, LightGBM, warm-up 48). Each cell of Table 10 gives CE, the ratio of the mean Winkler score to that of rolling conformal, and the ratio of the median interval width to that of rolling conformal; a ratio below 1 is better than rolling. At h=1 and h=3, ACI, DRACP and FACI are better calibrated than rolling with intervals about 9 to 16 percent narrower (width ratios 0.84 to 0.91), and the Winkler ratio is 0.94 to 0.99, so the narrower intervals do not cost interval score. At h=6 and h=12, the Winkler ratio of ACI and DRACP is above 1 (up to 1.25), so the advantage in calibration is paid for with width or misses. These ratios are descriptive. The Winkler contrast with a confidence interval is given in Section 6.2.

**Table 10. S4: CE / Winkler ratio / width ratio (relative to rolling), hold-out**

| Method | h=1 | h=3 | h=6 | h=12 |
|---|---|---|---|---|
| ACI | 0.020 / 0.95 / 0.84 | 0.020 / 0.99 / 0.90 | 0.025 / 1.05 / 0.88 | 0.048 / 1.12 / 1.09 |
| DRACP | 0.021 / 0.97 / 0.89 | 0.019 / 0.97 / 0.91 | 0.022 / 1.04 / 0.91 | 0.047 / 1.25 / 0.97 |
| FACI | 0.024 / 0.95 / 0.85 | 0.023 / 0.94 / 0.90 | 0.013 / 1.00 / 0.90 | 0.070 / 1.07 / 0.92 |
| Conformal PID | 0.024 / 0.98 / 0.95 | 0.028 / 0.97 / 0.95 | 0.021 / 1.00 / 0.94 | 0.079 / 1.05 / 0.99 |
| Rolling | 0.029 / 1 / 1 | 0.036 / 1 / 1 | 0.032 / 1 / 1 | 0.086 / 1 / 1 |
| Split | 0.056 / 1.11 / 1.35 | 0.050 / 1.07 / 1.23 | 0.053 / 1.06 / 1.27 | 0.119 / 1.02 / 1.09 |

S3 is reported in Section 6.5.

### 6.4 Summary of the robustness reading

Adaptive methods are better calibrated than a one-shot calibration for all three base models and without dependence on any single country. The direction "ACI better calibrated than a rolling window by 1 to 3 pp of CE" is seen in most settings but is not established at the registered level. Equivalence of DRACP and ACI within 2 pp holds for most base models at warm-up 48 and not at 96. On the hold-out panel, at short horizons adaptive methods reach similar or better calibration with narrower intervals than a rolling window, and at long horizons they do not. The narrower intervals are not seen in the exploratory data at h=3, where ACI was wider than rolling (mean width 4.28 against 3.95) and its Winkler score was 6.3 percent higher (95% CI [0.3, 19.4], unadjusted p 0.15).

### 6.5 The delayed-feedback diagnostic at h=12

At h=12 every method under-covers (pooled coverage 0.83 to 0.88 on the hold-out panel, 0.82 to 0.87 in the exploratory data). To examine the role of delayed feedback, the diagnostic run releases each outcome at origin + 1 instead of origin + 12. Table 7 gives coverage with instant feedback minus coverage with delayed feedback, with a paired block-bootstrap 95 percent interval over the same (unit, origin) cells.

**Table 7. S3: change in h=12 coverage when feedback is instant (pp; 95% interval)**

| Method | Exploratory (1738 cells) | Hold-out (1009 cells) |
|---|---|---|
| ACI | +4.1 [1.4, 7.8] | +2.4 [-0.1, 4.8] |
| DRACP | +4.3 [1.4, 7.5] | +3.9 [1.6, 6.4] |
| FACI | +8.3 [4.3, 13.6] | +6.4 [2.5, 9.6] |
| Conformal PID | +5.1 | +5.3 |
| Rolling | +1.3 | +1.3 |
| Split | 0 | 0 |

In the hold-out panel, ACI coverage is 0.884 with delayed feedback and 0.908 with instant feedback. R4 as registered (ACI at least +3 pp on the hold-out panel) is not met: the result is +2.4 pp. The interval [-0.1, 4.8] is compatible with no effect and with an effect of about 5 pp. For FACI and DRACP the effect is positive in both samples. Split conformal does not use feedback, so its difference is zero by construction. The statement supported is that feedback delay accounts for part of the shortfall at h=12, with a size that depends on the method and the sample. It is not shown that delay is, or is not, the main cause. The diagnostic is not a valid forecasting setup and is not a primary result.

### 6.6 Stress analysis (secondary, exploratory)

For the exploratory sample at h=3, coverage in the top decile of FX stress at the forecast origin is 0.849 for ACI, 0.869 for DRACP and 0.874 for split, against roughly 0.87 to 0.98 in the other deciles. At h=6 it is 0.864, 0.879 and 0.874 respectively. With about 200 observations per decile, the standard error is roughly 2.5 pp, so the top-decile shortfall of ACI at h=3 is about two standard errors. The deciles in between are not monotone. This analysis is exploratory: the same 13 countries shaped the design, many deciles, methods and horizons were examined, and the underlying association between stress and forecast error is weak (Section 5.4). No stress result is reported for the hold-out panel in the results documents used for this draft, and no confirmatory claim about stress is made.

### 6.7 The confirmatory months of the 13 countries

Run `confirm13` evaluates the 13 design countries on target months from 2025-07. Eleven countries contribute (Nigeria ends in 2024-12 because of the CPI break; Russia has no usable stretch after 2022-03), each with at most 16 months. With blocks of 12 months, the bootstrap is degenerate: confidence limits coincide with the estimate and p-values sit at the resampling floor. These contrast results (including entries that appear highly "significant" in the table) are not used. Pooled coverage in that period is high for every method (ACI 0.904, 0.922 and 0.940 at h=1, 3 and 6, from 167 unit-months), which is consistent with calmer inflation, and no conclusion is drawn.

### 6.8 The platform module

The repository contains a module of the application that serves calibrated inflation intervals for the 13 design economies (`GET /api/v1/inflation/calibrated-forecast`, implemented in `backend/fastapi_service/app/services/inflation_calibration.py`, with a page that shows the measured backtest coverage next to the nominal level). The service reads a CPI snapshot and forms the point forecast as h times an exponentially weighted moving average of past monthly log growth (smoothing parameter 0.2). It issues intervals by ACI on absolute residuals over a rolling calibration window of 120 months with step 0.02, with delayed feedback, and requires at least 30 revealed residuals before issuing an interval. The point forecast, the minimum calibration size (30 against the benchmark's warm-up of 48) and the data differ from the benchmark, which uses LightGBM. The benchmark results therefore bear on the platform only through the interval method, and the platform's own backtest coverage is displayed to users.

---

## 7 Discussion

### 7.1 What is established and what is not

Three statements are supported by the evidence. First, adaptive conformal intervals were better calibrated than a conformal calibration performed once on the first months and never updated. The direction is the same in the exploratory data, in the hold-out panel at both warm-ups, for three base forecasters, and after removing any single country (Table 8). The strength of the evidence depends on the warm-up size, and the registered rule R1 was met only at warm-up 96, which is a sensitivity run. Second, at the 12-month horizon all methods under-cover, and delayed feedback accounts for part of the shortfall, the size depending on the method and sample. Third, on the hold-out panel, at short horizons ACI, DRACP and FACI reach similar or better calibration than a rolling window with narrower intervals, while at 6 and 12 months the advantage costs interval score; the exploratory data do not show narrower intervals at h=3 (Section 6.4).

Three statements are not established. An improvement of ACI over a rolling window was not shown (R2); the point estimates are negative, and the evidence is in the direction of an advantage of about 1 to 3 pp of CE, but it does not reach the registered level. An advantage of DRACP over ACI was not detected, and equivalence within 2 pp was not stable across warm-up sizes (R3). That delayed feedback explains the h=12 shortfall was not met at the registered threshold (R4). None of these results is evidence that the effects are absent. In particular, the wording "DRACP does not transfer" or "ACI and DRACP are equal" is not allowed by the data.

### 7.2 Why null results, power and the ceiling effect

Several reasons may contribute to the null outcomes, and the data do not allow us to apportion them.

**Sample size and dependence.** The hold-out panel has 7 countries and about 200 origin months at h=3. Errors of h-step forecasts overlap, adaptive methods have a long memory (about 50 months at step 0.02), and countries share common shocks. The block bootstrap respects this dependence at the cost of wide intervals; the 95 percent intervals of the primary contrasts are about 2 to 6 pp wide on the CE scale (Table 5).

**Ceiling effect.** The calibration error of the rolling baseline is already small: in the hold-out panel its CE is 0.029 at h=1, 0.036 at h=3 and 0.032 at h=6 (Table 10), and ACI's is about 0.02. There is little room to improve. The power simulation reflects this: its alternative cannot reduce CE below zero, so the improvement it can create is bounded by the baseline CE (about 3 to 4 pp), and 80 percent power at the first Holm step was not reached up to 10 pp on the full hold-out sample. The MDE is therefore undefined for all four primary contrasts (R5). The same is true for the exploratory sample. The MDE on random 15-month windows has a median of 2.6 to 3.1 pp on the hold-out panel, but is undefined in 63 to 68 percent of windows. A contrast without defined power cannot support a claim of absence of an effect, and the pre-registered R5 therefore classifies all four contrasts as inconclusive. We interpret this as a limit of the design (a small and already well-calibrated reference) and not as a finding about the methods.

**A true small or zero difference.** The data are also compatible with ACI and a rolling window being close to each other in this setting, and with DRACP and ACI being close, but this cannot be separated from low power with the present sample.

**Specific to DRACP.** DRACP trains its regime and scale models on half of the warm-up (24 rows at warm-up 48), which is a small sample for these models, and its results depend on the warm-up (equivalence holds at 48 and not at 96, where it is wider than ACI). The DRACP paper reports an advantage that is specific to one-step forecasts, and our reproduction of its one-step setting was partial and qualitative: ACI 0.874 and DRACP 0.871 in coverage over 5 countries, against 0.884 and 0.890 reported by the authors over 48 series (Section 5.2 and the protocol), so the DRACP claim of being closest to nominal was not distinguishable from ACI there either.

### 7.3 Implications for practice

A practitioner who produces inflation intervals for a commodity-dependent economy should not calibrate once and leave the calibration unchanged: one-shot calibration had a higher calibration error than ACI in every CE contrast reported (both samples, both warm-ups, three base models), although the registered rule R1 was met only at the sensitivity warm-up, and its coverage varied the most across countries (the standard deviation of coverage across units at h=12 is 0.152 for split against 0.058 for ACI on the hold-out panel). Updating the calibration, either with a rolling window or with ACI, is a low-cost improvement. Between a rolling window and ACI this study cannot recommend one on statistical grounds. On the hold-out panel ACI had narrower intervals at short horizons without loss of interval score, and cost interval score at 6 and 12 months; on the exploratory data this was not seen at h=3. At the 12-month horizon, all methods under-cover (0.83 to 0.88 pooled on the hold-out panel), and users should treat the nominal level there as an upper bound. A part of the shortfall comes from the delay with which the outcome arrives, and cannot be removed in real use.

### 7.4 The choice of ACI in the platform

The platform uses ACI. The reason is practical and is limited by the evidence: adaptive calibration was better calibrated than a calibration done once, ACI is simple to implement and explain, and with a step of 0.02 and a window of 120 it gave narrower intervals than a rolling window at short horizons on the hold-out panel without a loss of interval score (not on the exploratory data at h=3). It is not claimed that ACI is better than a rolling window; this was not shown. The platform displays measured backtest coverage next to the nominal level so that a user can see the actual calibration.

---

## 8 Limitations

1. **Procedural boundary.** The hold-out countries are untouched with respect to countries only. The methods, the form of the contrasts, the horizons, the margin of 2 pp and the thresholds of 3 pp and 7 pp were chosen on the 13 design countries, and the author had seen the post-2025-06 months of these countries before the amendments. The rules R1 to R5 were written after the exploratory results at both warm-ups were known. The registration is a repository commit history, kept by one author, with all entries on 2026-11-18 or 2026-11-19, and not an external registry.
2. **Power.** The minimum detectable difference is undefined on the full hold-out sample for all four primary contrasts. All null outcomes are therefore inconclusive and are not evidence of equality. The MDE simulation has not been reviewed independently, and it assumes that the observed hit pattern of the baseline describes the true dependence and that dependence beyond the block length is zero.
3. **Small panel.** The hold-out panel has 7 countries; Ghana and Angola have high-inflation episodes, so pooled results can be driven by few units. S1 shows that removing one country changes the sign of ACI against rolling at h=6 on the hold-out panel in one case of seven.
4. **One point-forecaster family dominates the contrasts.** LightGBM is the base model for the primary family. ARIMA and naive B give the same direction in S2, but they were not part of the registered decision rules.
5. **Data revisions and vintages were not checked.** The IMF publishes dated CPI vintages, which allow a real-time revision check, but this was not done. Evaluation uses the revised data of the snapshot date. Small revisions for Russia and Mongolia are noted between the two snapshots, but their effect on intervals was not studied. Nigeria's series ends at 2024-12 because of a methodology break, so that country has no recent months.
6. **No systematic literature search was run.** The statements about novelty and the state of the literature are based on the author's reading only. Several statements are marked [CITATION NEEDED] and the bibliography is limited to a fixed list of works.
7. **The criterion for commodity dependence of the 13 design countries is not documented** in the project files reviewed for this draft. The hold-out candidates were selected from a fixed list by a written data-availability rule, not by a measured commodity-dependence criterion.
8. **Reproduction of DRACP is partial.** Five countries with annual HICP inflation, one seed, and a mean coverage of ACI 0.874, DRACP 0.871 (against 0.884 and 0.890 reported over 48 series with 20 seeds). The criterion of reproducing a published number within 2 pp could not be tested because the published numbers are averages over different series. The DRACP configuration in the benchmark follows the reproduction script and was not tuned.
9. **Calibration error is noisy.** CE is biased upward in small samples, and percentile intervals are not symmetric around the estimate. Choice of the 2 pp equivalence margin and of the 3 pp threshold of R4 is not justified beyond being fixed in advance.
10. **Stress analysis is secondary and exploratory.** The FX-based flag is a weak proxy of inflation shocks (lift below 2), is affected by exchange-rate regimes, and many deciles, methods and horizons were examined. Pegged and managed currencies were not analysed separately.
11. **Items in the protocol that are not reported.** Native ARIMA and ETS intervals, the central-bank target baseline, the exchange-rate-regime split, per-country heterogeneity beyond coverage ranges, and a foundation-model forecaster (Chronos) are mentioned in the protocol; the results documents do not report them, and the engine contains no Chronos module.
12. **The confirmatory months of the 13 countries are degenerate** (at most 16 months per unit) and are not used. The h=12 horizon has few non-overlapping windows (80 non-overlapping cells on the hold-out panel in run A).
13. **The platform is not the benchmark.** The platform uses an EWMA point forecast and a smaller minimum calibration size, so the benchmark results apply to its interval method but not to its point forecast.
14. **Point forecasts matter for interval width but were not optimised.** All hyperparameters were fixed in advance, and the point models are simple; better point forecasts could change absolute calibration and width.

---

## 9 Reproducibility

**Repository layout.**

| Path | Content |
|---|---|
| `docs/thesis/` | `topic.md`, `experiment-protocol.md` (with the "Changes" log), `shock-definition.md`, results documents `results-exploratory-v1.md`, `results-holdout-v1.md`, `results-robustness-v1.md` |
| `docs/thesis/results/<run>/` | CSV result tables per run (`explore_v1`, `explore_v2_ncal96`, `holdout_ncal48`, `holdout_ncal96`, `diag_instant_h12`, `diag_instant_h12_holdout`, `confirm13`); S1-S4 under `robust/` |
| `scripts/thesis/*.mjs` | Data download (IMF through DBnomics and the SDMX API), the shock rule, the validity checks |
| `scripts/thesis/data/` | `snapshot.json`, `confirmatory.json`, `holdout.json` |
| `scripts/thesis/exp/` | The engine: `data.py`, `forecasters.py`, `intervals.py`, `evaluate.py`, `calibration.py`, `power.py`, `robust.py`, `run.py`, and `tests/` |
| `scripts/thesis/repro_dracp.py` | Partial reproduction of the DRACP one-step setting through the public API of `dracp` 0.2.0 |
| `backend/fastapi_service/app/services/inflation_calibration.py` | Platform service |

**Environment.** Python 3.12 virtual environment under `scripts/thesis/.venv` with pandas, numpy, scipy, statsmodels, scikit-learn, LightGBM and the `dracp` package (0.2.0 in the reproduction check). The machine default was Python 3.14 with only numpy, and the package lists Python 3.10 to 3.12.

**Commands** (run from `scripts/thesis`, with the venv interpreter `.venv/Scripts/python.exe`).

- Tests: `-m pytest exp/tests -q`. The test modules cover data and chaining, the absence of look-ahead in forecasters, the timing of delayed and instant feedback, the equivalence of the independent ACI implementation with the package at h=1, calibration-error contrasts, Holm, TOST, the power simulation, the hold-out loader and the robustness analyses.
- Exploratory run v1 (code commit `2229076`): `-m exp.run full --start 2000-01 --end 2025-06 --out explore_v1 --resume`.
- Sensitivity run at warm-up 96 on the design countries: `-m exp.run full --start 2000-01 --end 2025-06 --n-cal 96 --out explore_v2_ncal96` [VERIFY: inferred from the run name and options, not copied from a document].
- Hold-out runs (all with `--holdout --start 2000-01 --end 2026-06`): (A) `--out holdout_ncal48`; (B) `--n-cal 96 --out holdout_ncal96`; (C) `--instant-feedback --horizons 12 --models lgbm --conformal-models lgbm --out diag_instant_h12_holdout`.
- Instant-feedback diagnostic on the design countries: `diag_instant_h12` [VERIFY: command not recorded in the documents; presumably the analogue of (C) without `--holdout`].
- Supplementary run: `--start 2000-01 --out confirm13` (degenerate, not used).
- Calibration-error contrasts: `-m exp.run ce --in results/<run> --out results/<run> --sample exploratory|holdout [--window-mde]`.
- Robustness analyses: `-m exp.run robust --in results/holdout_ncal48 --sample holdout --instant results/diag_instant_h12_holdout`.

**Hashes and commits.** The data hashes are in Appendix B. Commits: shock rule frozen `58871dc`; exploratory code `2229076`; hold-out specification and rules `1480604`; robustness specification `552fa67`; robustness results `de93501`.

Full per-row outputs stay under `scripts/thesis/results/` and are not tracked. The small result tables used in this paper are copied to `docs/thesis/results/`. Run times: the exploratory run v1 took 695 seconds.

---

## References

See `references.md`.

---

## Appendix A. Decision rules R1-R5 (summary of the fifth protocol entry)

The rules apply to base model LightGBM, the primary family with Holm correction over four tests (ACI minus rolling and DRACP minus ACI at h=3 and h=6), pooled over the 7 hold-out countries, block length 12.

- **R1 (replication of the secondary result):** ACI is better calibrated than split if the CE difference ACI - split is negative with Holm p < 0.05 at both h=3 and h=6.
- **R2 (does adaptivity help beyond a rolling window):** "ACI improves on rolling" only if ACI - rolling is negative with Holm p < 0.05 at the horizon; otherwise "not shown".
- **R3 (DRACP against ACI):** "no advantage, equivalent within 2 pp" only if equivalence holds at both warm-up sizes (A and B); "DRACP better" only if DRACP - ACI is negative with Holm p < 0.05 at both warm-ups; otherwise "inconclusive".
- **R4 (delayed feedback explains the h=12 shortfall):** supported if the mean coverage of ACI with instant feedback exceeds the delayed one by at least 3 pp on the hold-out panel.
- **R5 (power):** a contrast whose minimum detectable difference is undefined or above 7 pp is reported as inconclusive regardless of its p value.

No rule was changed after the hold-out result was seen. Any later change would have been logged with a date and a reason and reported as post hoc.

Outcome: R1 not met in the primary run (met at warm-up 96, a sensitivity run, not promoted); R2 not shown; R3 inconclusive; R4 not met (+2.4 pp against 3 pp); R5 all four primary contrasts inconclusive.

## Appendix B. Data snapshots and hashes

| File | Content | SHA-256 |
|---|---|---|
| `scripts/thesis/data/snapshot.json` | IMF CPI, FX per USD and Brent, 13 design countries, via DBnomics (indexed 2025-08-31) | `d01b8360c4167f0b3d829f3d7af0438c36fe858c9f2e2745e9b258039cc2d739` |
| `scripts/thesis/data/confirmatory.json` | CPI, FX and Brent from 2024-01, IMF SDMX API, written by `fetch_confirmatory.mjs` | `e2001e5aad677567a7d572a6cf1d22929b18bfe1d3c1ad94bff47b75a3981a74` |
| `scripts/thesis/data/holdout.json` | CPI and FX of BO, PY, UY, GH, GE, KG, AO, written by `fetch_holdout.mjs` | `0245eab6c75d6bd7fe800fe5978a7ca5670550dff4b3f23e817177f9c6fae9ac` |

Notes. Brent in the direct IMF API needs the area code `G001`. The overlap of the first two snapshots (2024-01 to 2025-05) is identical for FX, Brent and CPI except for the rebasing of the index level of KZ (0.477) and NG (0.131), small revisions for RU (up to 0.07 percent) and MN (up to 0.05 percent), and the Nigerian methodology break at 2025-01 (the index falls from 113.9 to 110.7 in rebased terms; growth between 2024-12 and 2025-01 is excluded). The IMF also publishes dated CPI vintages (`CPI_2026_JAN/FEB/APR/MAY_VINTAGE`), which were not used.

## Appendix C. Change log summary

| Date | Document | Change | Before which result |
|---|---|---|---|
| 2026-11-18 | `shock-definition.md` | Rule A frozen (threshold 3, window 3, 60-month lookback, floor 0.005) | Any forecast |
| 2026-11-19 | `shock-definition.md` | Validity checks logged; label timing defined; stress made secondary; confirmatory evaluation planned | Any forecast |
| 2026-11-19 | `experiment-protocol.md`, entry 1 | After committee review 5.5/10: claim hierarchy, confirmatory limited to h = 1, 3, 6, second snapshot, FACI and PID, DRACP tolerance and fallback, two naive baselines, block length at least h, primary tests at h=3 and 6, MDE threshold | Any forecast |
| 2026-11-19 | entry 2 | Second snapshot checked; confirmatory restricted to the pooled panel; Nigerian break; topic fixed | Any forecast |
| 2026-11-19 | entry 3 | Engine decisions (start 2000-01, 60 months of history, warm-up 48, window 120, step 0.02, LightGBM primary, chaining fix); first run exploratory only | Any full run |
| 2026-11-19 | entry 4 | CE replaces pooled coverage; reference becomes rolling; TOST for DRACP against ACI with 2 pp margin; warm-up 96 sensitivity; 7 hold-out countries; block length at least 12; stress stays exploratory; allowed DRACP wording | Hold-out forecasts (after exploratory v1) |
| 2026-11-19 | entry 5 | Hold-out runs A, B, C specified; R1-R5 fixed | Hold-out run |
| 2026-11-19 | entry 6 | Robustness S1-S5 written down | Their computation (after the hold-out result) |
| 2026-11-19 | `topic.md` | Contribution text revised to match the hold-out result | - |

Commits: `58871dc` (shock rule), `810a60c` (protocol draft), `2229076` (engine and first run), `bf78f53` (exploratory results), `0ff08d8` (amendments; [VERIFY] against the protocol, which cites `1480604`), `1480604` (hold-out support and run rules), `46a2474` (hold-out results), `552fa67` (robustness specification), `c3c3c0f` (topic alignment), `de93501` (robustness results).
