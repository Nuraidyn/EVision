# Comparing Methods for Building Reliable Prediction Intervals for Machine-Learning Inflation Forecasts in Commodity-Dependent Economies

Draft manuscript, 2026-11-19. Source documents: `docs/thesis/` and `scripts/thesis/exp/` on branch `thesis/inflation-calibration`. Notes for the reviewer are in `REVIEW_NOTES.md`.

---

## Abstract

Prediction intervals for inflation are used for decisions in commodity-dependent economies, but it is not known whether adaptive conformal methods that perform well on euro-area and US data keep their nominal coverage there. We build a multi-horizon (1, 3, 6 and 12 months) calibration benchmark of split, rolling-window, adaptive (ACI, FACI), conformal PID and regime-aware (DRACP) intervals at nominal level 0.90, using monthly IMF consumer price indices for 13 design economies and 7 hold-out economies selected by a fixed data-availability rule, and, in an extension, a second hold-out panel of 10 economies selected by another fixed rule. The primary outcome is the calibration error (CE), the mean over countries of |coverage - 0.90|. Contrasts are tested with a moving-block bootstrap and Holm correction, equivalence of DRACP and ACI with two one-sided tests (TOST) and a 2 percentage-point margin, and decision rules R1-R5 were pre-specified in a version-controlled protocol before the hold-out run (a self-attested commit history; the rules were written after the exploratory results were known). Adaptive methods (ACI, FACI, conformal PID, DRACP) were better calibrated than a calibration performed once and than the native intervals of the forecasting model, and the direction is consistent in both samples. The registered rule R1 (ACI against split) was met only at a 96-month warm-up, a sensitivity run that is not promoted, and not at the primary 48-month warm-up (ACI minus split at h=3: -3.0 pp, p=0.054; at h=6: -2.8 pp, p=0.092; Holm-adjusted 0.108 at both horizons). On the design panel and on the first hold-out panel an advantage of ACI over a rolling window was not shown (Holm p 0.35 and 1.0 on the first hold-out panel; MDE undefined, inconclusive), and no efficiency advantage in interval width or interval score is established. DRACP against ACI is inconclusive: equivalence within 2 pp holds at warm-up 48 and not at 96, and because the 2 pp margin is about the size of ACI's own calibration error, this verdict is weak by construction. The power rule R5 leaves all four primary contrasts inconclusive. At the 12-month horizon, pooled coverage is below nominal for every method (0.83 to 0.88 on the hold-out panel); releasing outcomes immediately raised ACI coverage by 2.4 pp (95% CI -0.1 to 4.8) on the hold-out panel, below the pre-specified 3 pp threshold. In a secondary, post hoc analysis without multiplicity correction, ACI with an ARIMA base model had a lower calibration error than the native ARIMA intervals at every horizon in both samples (-3.3 to -6.4 pp); on the hold-out panel the interval for the difference includes zero at h=6 and h=12. An extension, specified before any forecast was computed for its countries, added a second hold-out panel of 10 economies and a zero-shot foundation model (Chronos) as a fourth base forecaster. On the second panel ACI improved on a rolling window under the registered rule at warm-up 48 at h=3 for LightGBM, ARIMA and naive B (Holm 0.008, 0.004, 0.004) and at h=6 for ARIMA and naive B (0.030, 0.039); for Chronos at h=3 the Holm p is 0.036 but the minimum detectable difference (MDE) is undefined, so under E5 that cell is inconclusive and is not counted as met, and Chronos and LightGBM at h=6 are not met (0.088, 0.159); the earlier 20 countries re-run from 2010-01 show it as not significant (Holm p 0.22 to 1.0), with the MDE undefined in every cell, so inconclusive under E5. The conclusion about ACI against a rolling window therefore depends on the panel; the reason is not known, candidate explanations were not tested, the panels are not pooled into one claim, and warm-up 96 on the new panel (41 and 35 pooled months, undefined minimum detectable difference) shows nothing. On that panel ACI was better calibrated than split for all four base models at warm-up 48, and DRACP had a lower CE than ACI in every cell by 0.5 to 1.8 pp with no difference reaching Holm p below 0.05 (R3 stays inconclusive). On target months from 2025-01, a period that Chronos cannot be assumed to have seen in pretraining (the cutoff was not verified), its mean absolute error was lower than that of naive B and, descriptively, at least as low as that of LightGBM and ARIMA. A language-model explanation layer is implemented and tested with a deterministic fake client; its evaluation has not been run on a real model and no result is reported. The contributions are a benchmark with null outcomes specified in advance, a comparison of adaptive calibration with one-shot calibration and with native intervals, a feedback-delay diagnostic, a panel-dependence finding that is reported rather than resolved, and an open reproducible pipeline. The hold-out countries are untouched only with respect to countries; methods, contrasts and horizons were chosen on the design countries.

---

## 1 Introduction

Central banks, finance ministries and firms in commodity-dependent economies use inflation forecasts, and a forecast is useful for decisions only together with a statement of its uncertainty. A prediction interval with a nominal level of 90 percent makes a specific claim: in about nine cases out of ten the realised value should fall inside it. Whether this claim holds in practice is the question of calibration, and it can be checked directly against realised data. It is not guaranteed by the forecasting model, because the model's own error distribution is estimated from a past that may not resemble the future.

Commodity-dependent economies are a demanding setting for calibration. Their price levels are exposed to exchange-rate movements and to commodity prices, and their inflation regimes can change within a few years. [CITATION NEEDED: empirical evidence on the volatility and regime changes of inflation in commodity-dependent economies.] A calibration made once on a past window may therefore fail later, and a method that adapts the interval width online is a natural candidate. Conformal prediction (Vovk, Gammerman and Shafer, 2005) gives distribution-free finite-sample coverage under exchangeability, which time series violate. Adaptive conformal methods (Gibbs and Candes, 2021, 2024; Angelopoulos, Candes and Tibshirani, 2023; Bhatnagar et al., 2023) were designed for that case, and a recent regime-aware variant, DRACP (Oancea, 2026), reports gains on euro-area inflation. Whether these results transfer to commodity-dependent economies, and at multi-month horizons, has not been tested to our knowledge. [CITATION NEEDED: no systematic literature search was run; this statement is based on the author's reading only.]

**What is done.** We construct a rolling-origin benchmark for the cumulative h-month log growth of the consumer price index, at horizons 1, 3, 6 and 12 months. Six interval methods (split, rolling, ACI, FACI, conformal PID, DRACP) are placed on top of point forecasts, with a nominal level of 0.90 and with outcome feedback delayed by h months, as it is in real use. The panel has 13 economies used to design the study and 7 hold-out economies for which no forecast had been computed before the pre-specified hold-out run. The primary outcome is calibration error, defined per country as the absolute difference between empirical coverage and 0.90 and averaged over countries. Pooled coverage is reported but not used as the primary outcome, because opposite deviations of different countries can cancel in a pooled average. The decision rules for the hold-out run (R1 to R5) were written in the repository before the run, and the outcomes are reported exactly as the rules classify them. "Pre-specified" here refers to a self-attested commit history, not to an external registry, and the rules were written after the exploratory results were known (Section 5). An extension, specified in the eighth protocol entry before any forecast was computed for its countries, adds a second hold-out panel of 10 economies, a zero-shot foundation-model forecaster (Chronos) as a fourth base model, and the rules E1-E5 (Sections 5.6 and 6.11 to 6.13).

**Summary of findings, stated plainly.**

1. Adaptive methods (ACI, FACI, conformal PID, DRACP) were better calibrated than split conformal calibrated once on the first months and never updated, and better calibrated than the native intervals of the forecasting model (secondary, post hoc; Section 6.9). The direction is the same in the exploratory data, in the hold-out panel at both warm-up sizes, for three base forecasters, and after removing any single country. The registered rule R1, however, was met only at the 96-month warm-up, which is a sensitivity run and is not promoted to the primary result. At the primary 48-month warm-up the result for ACI minus split was -3.0 pp with p=0.054 at h=3 and -2.8 pp with p=0.092 at h=6 (Holm-adjusted 0.108 at both horizons); the confidence intervals at warm-up 48, [-5.4, +0.5] and [-3.9, +1.2], include zero.
2. An improvement of ACI over a rolling-window conformal method was not shown (R2) on the design panel and on the first hold-out panel (MDE undefined, inconclusive). Point estimates are negative (about 1 to 3 pp of calibration error in most settings) and their intervals include zero in the primary run. On the second hold-out panel of the extension the same rule was met at warm-up 48 (at h=3 for LightGBM, ARIMA and naive B (Holm 0.008, 0.004, 0.004) and at h=6 for ARIMA and naive B (0.030, 0.039); for Chronos at h=3 the Holm p is 0.036 but the MDE is undefined, so under E5 it is inconclusive and not counted as met; Chronos at h=6 and LightGBM at h=6 are not met (0.088, 0.159)), and the earlier 20 countries re-run from 2010-01 show it as not significant, with the MDE undefined in every cell, so inconclusive under E5. The conclusion therefore depends on the panel; the reason is not known and was not tested, and the panels are not averaged into one claim (Sections 6.11 and 7.2). No efficiency advantage in interval width or interval score is established (Section 6.4).
3. For DRACP against ACI the outcome is inconclusive (R3): equivalence within 2 pp was shown at warm-up 48 and not at warm-up 96. No advantage of DRACP over ACI was detected in this configuration. Because the 2 pp margin is about the size of ACI's own calibration error, this equivalence verdict is weak by construction (Section 7.2).
4. All four primary contrasts are inconclusive under the power rule R5, because the minimum detectable difference is undefined on the full hold-out sample.
5. At the 12-month horizon, pooled coverage is below nominal for every method. Delayed feedback accounts for part of the shortfall, but the pre-specified threshold (R4) was not met for ACI: +2.4 pp against 3 pp required, with an interval that includes zero.
6. On the second hold-out panel (warm-up 48) R1 was met for all four base models, so the advantage over a calibration performed once replicated on new countries at the primary warm-up; at warm-up 96 it was not met, on 41 and 35 pooled months. DRACP had a lower CE than ACI in every cell by 0.5 to 1.8 pp, none of the differences reached Holm p below 0.05, and R3 stays inconclusive (equivalence within 2 pp held only for Chronos at h=3).
7. Chronos used zero-shot as a base forecaster did not change the calibration conclusions. On target months from 2025-01 its mean absolute error was lower than naive B at every horizon, and no paired interval against LightGBM or ARIMA favours them over Chronos; this is descriptive, rests on 22 calendar months, and depends on an assumed, unverified pretraining cutoff (Section 6.12). The language-model explainer has not been evaluated (Section 6.13).

**What is not claimed.** This work does not show that adaptive methods are better than rolling windows, it does not show that they are not (the answer depends on the panel), and it does not show that DRACP fails or does not transfer. Most pre-specified rules returned null or inconclusive outcomes, and a null outcome here is not evidence of equality. The hold-out countries are untouched with respect to countries only (Section 5).

**Contributions.** (1) A calibration benchmark on 20 economies with calibration error, interval score, width and power-aware inference, where the null outcomes were specified in advance. (2) Evidence that adaptive methods are better calibrated than a calibration performed once and than the native intervals of the forecasting model, with a direction consistent in both samples; the registered rule R1 was met only at the sensitivity warm-up. (3) A secondary, post hoc comparison with native ARIMA and ETS intervals, with no multiplicity correction: ACI with ARIMA had a lower CE than the native ARIMA intervals at every horizon in both samples, and on the hold-out panel the interval for the difference includes zero at h=6 and h=12 (Section 6.9). (4) A diagnostic of the effect of delayed feedback at the 12-month horizon. (5) An extension on a second hold-out panel of 10 economies with four base models including a zero-shot foundation model, specified before any forecast was computed for these countries; it replicates the advantage over one-shot calibration at the primary warm-up, and it shows that the conclusion about ACI against a rolling window depends on the panel (met on the second panel for part of the cells, not shown or inconclusive on the others), a result that is reported next to the earlier ones and not resolved (Sections 6.11 and 7.2). (6) A descriptive comparison of the point accuracy of Chronos with LightGBM, ARIMA and naive B on target months it cannot be assumed to have seen. (7) An open pipeline with dated hashed data snapshots, tests and a committed protocol. A platform module that serves inflation intervals is an engineering application of the interval method with a simpler point forecast and is not a scientific contribution (Section 6.10).

The remainder of the paper is organised as follows. Section 2 reviews related work. Section 3 describes the data, and Section 4 the methods. Section 5 states what was fixed before which run, including the extension. Section 6 gives the results, the extension in Sections 6.11 to 6.13, Section 7 discusses them, Section 8 lists limitations, and Section 9 describes how to reproduce the work.

---

## 2 Related work

### 2.1 Conformal prediction for time series

Conformal prediction (Vovk, Gammerman and Shafer, 2005) turns any point predictor into a prediction set whose coverage is guaranteed in finite samples when the data are exchangeable. In the split variant, residuals on a held-out calibration set define a quantile, and the interval is the point forecast plus or minus that quantile. Time series are not exchangeable, and the guarantee does not hold in general. Barber, Candes, Ramdas and Tibshirani (2023) give a coverage bound beyond exchangeability, using weights that reflect how far the data depart from it. Xu and Xie (2021) propose a conformal interval for dynamic time series built on ensembles. Zaffran et al. (2022) study adaptive conformal predictions for time series and the role of the learning rate. A simple practical response is to compute the quantile only from the most recent residuals, which we call rolling conformal.

### 2.2 Adaptive methods: ACI, FACI, conformal PID and SAOCP

Adaptive conformal inference (ACI; Gibbs and Candes, 2021) treats the miscoverage level as a quantity updated online. After each outcome, the working level moves by a step size times the difference between the target miscoverage and the realised miss indicator, so that the long-run frequency of misses approaches the target level without assumptions on the data. The step size is a tuning choice. FACI (Gibbs and Candes, 2024) aggregates several step sizes to avoid choosing one. Conformal PID control (Angelopoulos, Candes and Tibshirani, 2023) treats the problem as control of a quantile and combines proportional, integral and forecasting components. SAOCP (Bhatnagar et al., 2023) uses strongly adaptive online learning. The present benchmark includes ACI, FACI and conformal PID. SAOCP is implemented in the released `dracp` package and was run in a reproduction check (Section 5.2) but is not part of the panel benchmark.

These guarantees concern long-run miss frequency. They do not guarantee that every country, every horizon and every window is calibrated, and they are not stated for the situation in which the outcome of an h-step forecast is revealed only h months later. How that delay affects the adaptive updates is an empirical question that this paper addresses with a diagnostic (Section 6.5).

### 2.3 Regime-aware calibration: DRACP

The following description is as described by the authors of DRACP (Dynamic Regime-Aware Conformal Calibration; Oancea, 2026, arXiv:2608.17079, version 2, Sections 3 and 5 to 7 of the HTML version). DRACP keeps the split-conformal radius but replaces the equal weights on past errors by a weighted quantile. The weight of a past error is a product of four factors: a temporal decay; a density-ratio correction for covariate shift; a Gaussian kernel whose effective sample size is floored; and a regime-similarity term from a Gaussian mixture model. An online controller adjusts the significance level from the realised coverage, aggregating adaptive-conformal experts over several learning rates. The authors evaluate the method on 48 macroeconomic and financial series (28 HICP inflation series of the euro area and EU member states, 13 US macroeconomic and energy series and 7 daily financial series) against split, rolling, ACI, FACI, SAOCP and conformal PID. The evaluation is mainly one-step-ahead, with an additional multi-horizon evaluation at h=3, 6 and 12 with direct forecasts and delayed feedback. The authors state that the advantage is specific to one-step-ahead forecasting and depends on the point forecaster. [VERIFY: the description above was read from the authors' paper by the project author and relayed for this draft; check the wording and the section numbers against the paper before submission. The configuration values used here (Section 4.3) come from the released package and the reproduction script, not from the paper.]

Over 48 series and 20 seeds, the authors report mean coverage of 0.890 for DRACP, 0.884 for ACI, 0.883 for FACI, 0.868 for SAOCP, 0.841 for rolling, 0.825 for conformal PID and 0.781 for split conformal at nominal 0.90 (as recorded in `experiment-protocol.md`). This benchmark uses the released package through its public streaming interface (Section 4.3). Our setting differs from theirs in three respects: the point model is refitted on an expanding window instead of being fitted once, the target is the cumulative h-month log growth instead of the annual rate, and the economies are commodity-dependent. The present study is a transfer study of a published method to a different panel; it draws no conclusion about the method beyond the limitation that its authors state.

### 2.4 Inflation forecast uncertainty in emerging markets

The literature on inflation forecasting in emerging and commodity-dependent economies is large, and the project notes refer to a Dallas Fed working paper on emerging-market inflation forecasting [CITATION NEEDED: verify authors and title]. We did not run a systematic literature search, and we make no claim about the state of that literature beyond the following. Intervals for inflation are commonly derived from the forecast model's own error distribution, and we compare conformal calibration with the native ARIMA and ETS intervals of the engine in a secondary, post hoc analysis (Section 6.9). [CITATION NEEDED: studies of the calibration of inflation prediction intervals in emerging markets.]

### 2.5 Pretrained time-series models

Chronos (Ansari et al., 2024) is a family of pretrained time-series forecasting models that can be applied to a new series without fitting, which is called zero-shot use. We use the smallest Chronos-Bolt model as a point forecaster and put conformal intervals on top of it (Section 4.2). We did not review the literature on foundation models for forecasting and make no claim about it beyond this use. [CITATION NEEDED: studies of foundation-model forecasts for inflation and of their interval calibration; the Chronos entry in `references.md` is marked [VERIFY].]

### 2.6 Positioning

The paper is a transfer and benchmark study, not a new method. Its aim is to measure, with decision rules recorded in advance, whether the published ranking of conformal methods holds on a different panel, and to report null outcomes as such. The closest work is the DRACP paper (Oancea, 2026). We do not replicate its setup; we reproduce it only partially (Section 5.2 and Section 8).

---

## 3 Data

### 3.1 Sources

All series are monthly. Consumer price indices (all items) come from the IMF (series `M.<country>.PCPI_IX`), obtained through DBnomics for the first snapshot and through the IMF SDMX API (`api.imf.org`) for the second. The exchange rate is the monthly average of domestic currency per US dollar (IMF IFS, `ENDA_XDC_USD_RATE`). The Brent crude price is from the IMF primary commodity price series (`M.W00.POILBRE.USD`); in the direct API it requires the area code `G001`. The exchange rate and Brent enter the feature set of the LightGBM forecaster, and the exchange rate defines the stress measure of the secondary analysis.

### 3.2 Countries

**Design countries (13).** Core long-history group: Brazil (BR), Mexico (MX), Chile (CL), Colombia (CO), Peru (PE), South Africa (ZA), Indonesia (ID). Regional group: Kazakhstan (KZ), Russia (RU), Azerbaijan (AZ), Uzbekistan (UZ). Control group: Nigeria (NG), Mongolia (MN). These countries were used to shape the design (the stress rule, the start date, the contrasts and the horizons). No measurable criterion (for example an export-share rule) was applied to call these countries commodity-dependent (Sections 7.5 and 8).

**Hold-out countries (7).** Bolivia (BO), Paraguay (PY), Uruguay (UY), Ghana (GH), Georgia (GE), Kyrgyzstan (KG), Angola (AO). The candidate list (14 names, in a fixed order) and the eligibility rule were written in `scripts/thesis/fetch_holdout.mjs` before any forecast was computed for these countries. The rule required at least 220 months of IMF monthly CPI and of exchange rate per US dollar within 2000-01 to 2026-06, with at most 3 missing CPI months. The first 10 eligible candidates were to be kept. Only 7 candidates met the rule (ZM, AM, TZ, UG, KE and IQ start in 2009 or 2010; PG has no CPI series), so the panel has 7 countries and the rule was not relaxed. Target months of the hold-out panel run from 2009-02 to 2026-06. All months of these countries are labelled `holdout`.

**Second hold-out panel (10), extension.** Zambia (ZM), Armenia (AM), Tanzania (TZ), Uganda (UG), Kenya (KE), Iraq (IQ), Botswana (BW), Namibia (NA), Mozambique (MZ), Cote d'Ivoire (CI). The candidate list and the eligibility rule were written in `scripts/thesis/fetch_holdout2.mjs` before any forecast of any kind was computed for these countries (eighth protocol entry, Section 5.6). The rule required at least 170 months of IMF monthly CPI and of exchange rate per US dollar within 2010-01 to 2026-06, with at most 3 missing CPI months; the first 10 eligible candidates were kept. Six more candidates (CM, DZ, EG, MW, RW, ET) were eligible but came after the first 10 and were not used. Each series has 198 months from 2010-01. Several of these countries (ZM, AM, TZ, UG, KE, IQ) were candidates of the first hold-out rule and did not qualify under its 220-month requirement; no country is in two panels. All target months are labelled `holdout2`. The panel is shorter than the first one, so after the 60-month training minimum and a warm-up of 48 there are 89 pooled calendar months at h=3 and 83 at h=6, and after a warm-up of 96 there are 41 and 35. The same caveat on "commodity-dependent" applies as for the other panels (Section 7.5).

### 3.3 Snapshots

Dated snapshots with SHA-256 hashes were taken from the IMF: two for the design countries and one file for each hold-out panel (Appendix B).

- `snapshot.json`: CPI, exchange rate and Brent for the 13 design countries from DBnomics (indexed 2025-08-31). SHA-256 `d01b8360c4167f0b3d829f3d7af0438c36fe858c9f2e2745e9b258039cc2d739`.
- `confirmatory.json`: CPI, exchange rate and Brent from 2024-01 onwards, fetched directly from the IMF SDMX API after the protocol was committed. SHA-256 `e2001e5aad677567a7d572a6cf1d22929b18bfe1d3c1ad94bff47b75a3981a74`. CPI runs to 2026-08 (PE, NG), 2026-09 (KZ, RU, AZ, UZ, CO, BR, MX, ZA) or 2026-10 (CL, MN, ID).
- `holdout.json`: CPI and exchange rate of the 7 hold-out countries, SHA-256 `0245eab6c75d6bd7fe800fe5978a7ca5670550dff4b3f23e817177f9c6fae9ac`. Brent for the hold-out run is taken from the main snapshot files.
- `holdout2.json`: CPI and exchange rate of the 10 countries of the second hold-out panel, written by `fetch_holdout2.mjs`, SHA-256 `72bcfee645ef3c5f89a67763278a3ee8ee2a74523e38a26739b16726c8947c75`.

The overlap of the two snapshots (2024-01 to 2025-05) is identical for the exchange rate, Brent and CPI except for three differences recorded in the protocol: a constant rebasing of the index level for Kazakhstan (ratio 0.477) and Nigeria (ratio 0.131), small revisions for Russia (up to 0.07 percent) and Mongolia (up to 0.05 percent), and a methodology break in the Nigerian series at 2025-01.

### 3.4 Rebasing and the Nigerian methodology break

Because the two snapshots use different index bases, the loader chains them on the CPI level at the last month they have in common (`chain_cpi` in `exp/data.py`). The earlier snapshot wins on overlap, and later months are rescaled by a constant factor, so growth rates are unaffected. An early version of the loader merged the snapshots without rescaling and produced a false 74 percent fall in the Kazakhstani index; this was found and fixed before the run, and a regression test now checks that no country has a monthly log jump above 0.15 at the junction. For Nigeria, the CPI index falls from 113.9 to 110.7 in rebased terms between 2024-12 and 2025-01, which reflects a change in methodology and not a price movement. Months from 2025-01 are therefore not appended and the Nigerian series ends at 2024-12.

Russia has 30 missing CPI months. Its series is cut into stretches of consecutive months and only stretches of at least 60 months are used; in the runs reported here Russia enters as one unit (`RU`) in the 13-unit panel. Series that start later than 2000 (KZ, AZ, NG from 2005; MN from 2006; UZ, PE from 2010) enter once they have 60 months of history.

### 3.5 Exploratory and confirmatory samples

The label of each evaluated row depends on its target month. Target months before 2025-07 are labelled exploratory. Target months from 2025-07 on the 13 design countries are labelled confirmatory in the code. After the amendments (Section 5), the confirmatory months of the 13 countries cannot carry a claim: with at most about 16 months per country, there are two or three independent blocks. The main confirmatory pool became the 7 hold-out countries, all of whose months are labelled `holdout`; the extension adds the 10 countries of the second hold-out panel, labelled `holdout2`. The run on the post-2025-06 months of the 13 countries (`confirm13`) is degenerate (blocks of 12 months on at most 16 months; Section 6.7) and is not used for any claim.

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
- **LightGBM** (Ke et al., 2017): a direct forecast, one model per horizon, 200 trees, learning rate 0.05, 8 leaves, subsample 0.8, column sample 0.8, refitted every 3 origins. Features are the current monthly inflation and its lags at 1, 2, 5 and 11 months, rolling means over 3 and 12 months, the exchange-rate and Brent log changes (current and lagged one month), and the sine and cosine of the calendar month. LightGBM is the primary base model in all contrasts of Sections 6.1 to 6.10.
- **Chronos** (extension): a pretrained model used zero-shot, with no fine-tuning and no covariates, in the smallest Chronos-Bolt version that installs, `amazon/chronos-bolt-tiny` (the protocol named `chronos-t5-small` as the fallback; the model identifier is fixed in `exp/forecasters.py`). It forecasts the monthly inflation series (100 times the log change of the CPI) h steps ahead from all history up to the origin, truncated to a context of 2048 observations, and the h median forecasts are summed, as for ETS and ARIMA. It has no native interval, because the sum of quantiles is not a quantile; conformal methods are applied on its point forecast, as for the other base models. **Leakage flag.** Chronos may have met public CPI series during pretraining. Rows with a target month before 2025-01 carry the flag `possibly_seen`. The pretraining cutoff of the model was not looked up and not verified; 2025-01 is a conservative assumption. Only target months from 2025-01 are treated as clean.

Forecast origins start no earlier than 2000-01, because the 1990s hyperinflation of Brazil and Mexico made native ARIMA intervals and LightGBM unusable in a check. Each country needs 60 months of training history. A failed ETS or ARIMA fit carries the previous point forecast forward and is counted; in the exploratory run, no fit fell back (0 of 7628 rows per model). The conformal interval methods were run on three base models in the main runs (LightGBM, ARIMA and naive B) and on four in the extension (those three and Chronos). The extension runs start at 2010-01 (Section 5.6); ARIMA and naive B were not re-run on the design and first hold-out countries in the extension, only LightGBM and Chronos.

### 4.3 Interval methods

All six methods are run through the streaming interface of the released `dracp` package (`fit`, `predict_one`, `update_one`) with a pass-through base model. The first feature column is our own point forecast, and the package uses it unchanged. Nominal level 1 - alpha = 0.90 (alpha = 0.10).

- **Split conformal:** the quantile of absolute residuals on the warm-up window, fixed and never updated.
- **Rolling conformal:** the quantile of the most recent 120 absolute residuals.
- **ACI** (Gibbs and Candes, 2021): the quantile level is updated online with step 0.02 on a rolling window of 120 residuals. After each released outcome, the working miscoverage level moves by 0.02 times (0.10 minus the miss indicator of the interval that was actually issued).
- **FACI** (Gibbs and Candes, 2024): package defaults.
- **Conformal PID** (Angelopoulos, Candes and Tibshirani, 2023): package defaults.
- **DRACP** (Oancea, 2026): the package configuration used in the reproduction script (calibration window 120, target window 24, temporal decay 0.985, adaptive bandwidth from a grid, 3 regimes, FACI control of the level). DRACP trains its regime and scale models on the first half of the warm-up rows and calibrates on the second half; the other methods use all warm-up rows for calibration.

Infinite radii that arise when there are too few scores for the requested level are capped at 10 times the largest absolute calibration score seen so far, and the number of capped intervals is recorded. An independent implementation of ACI (`OwnACI`) is used in a test that compares it with the package at h=1. Native intervals of ARIMA (Gaussian, from psi-weights) and ETS (simulated, 400 paths) are computed as a parametric comparison and are reported in Section 6.9 as a post hoc secondary analysis.

### 4.4 Delayed feedback

For an h-step forecast made at origin j, the outcome is observed only at month j+h. When predicting at origin k, the update for origin j is therefore applied only if j + h <= k, and the result stored at prediction time is passed back so that the miss indicator is that of the interval actually issued. This is the setting in real use, and it is what the code implements by default. The first rows form the warm-up: rows 0 to n_cal-1 are the initial calibration set, and the first evaluated origin is n_cal + h - 1, so that every warm-up row has been released. The h-1 rows between them receive no interval and no feedback.

A diagnostic option releases each outcome at origin + 1 as if the horizon were 1, even though the real outcome is observable only after h months. It is not a valid forecasting setup. It is used only to isolate the effect of delay (Section 6.5), and its output directory carries a marker file that labels it as a diagnostic.

### 4.5 Evaluation protocol

The evaluation uses a rolling origin with one origin per month. For each unit (a country, or a stretch of Russia), the evaluated rows are the origins from n_cal + h - 1 on. The primary warm-up is n_cal = 48 residuals; a sensitivity run uses n_cal = 96, applied to all methods. Coverage is the share of origin months where the realised target lies in the interval. The interval (Winkler) score (Winkler, 1972; see also Gneiting and Raftery, 2007) of an interval [l, u] for outcome y is

W = (u - l) + (2 / alpha) * max(l - y, 0) + (2 / alpha) * max(y - u, 0),

so that with alpha = 0.10 an outcome outside the interval is penalised by 20 times the distance by which it is missed, in addition to the width. Lower is better. Mean width is reported in percentage points of cumulative growth. Point forecasts are evaluated by mean absolute error and root mean squared error relative to the naive baselines.

The post-2025-06 target months of the 13 design countries (run `confirm13`) are not evaluated in any reported contrast: with blocks of 12 months on at most 16 months per unit the bootstrap is degenerate, and the run is not used for any claim (Section 6.7).

### 4.6 Calibration error and why pooled coverage is not enough

For a unit u and a method m, let cov(u, m) be the empirical coverage. The **calibration error** (CE) is |cov(u, m) - 0.90|. A contrast between methods m1 and m2 is

T(m1, m2) = mean over units of [ CE(u, m1) - CE(u, m2) ],

with equal weight for each unit and only (unit, origin) cells present for both methods. A negative T means m1 is better calibrated. The reason for using CE instead of pooled coverage is that pooled coverage lets opposite deviations cancel. In the exploratory data at h=3, split conformal covers 1.000 in Indonesia and 0.822 in Peru. A pooled average of these is close to nominal, although neither country is calibrated. Moreover, when a method over-covers, a lower coverage means better calibration, so a difference in pooled coverage does not tell which method is closer to 0.90. The absolute value in CE is biased upward by sampling noise, particularly for small samples per unit; the bias largely cancels in T because both methods have the same sample in each unit. Percentile bootstrap intervals for T need not be symmetric around the estimate, because CE is a nonlinear function of coverage.

The original contrasts defined in the first protocol draft (difference of pooled coverage) are kept in the report as secondary results.

### 4.7 Contrasts and the decision family

The primary family (after the fourth protocol amendment) has four tests: ACI minus rolling conformal, and DRACP minus ACI, each at h=3 and h=6, with LightGBM as base model, pooled over countries. Holm's procedure (Holm, 1979) controls the family-wise error rate over these four tests. ACI minus split conformal is a secondary, descriptive contrast and is not part of the Holm family. h=1 and h=12 are descriptive. The Winkler contrast is the relative difference of the equal-unit-weight mean Winkler score, reported with unadjusted p-values as descriptive. The standard deviation of coverage across units is reported next to CE.

### 4.8 Block bootstrap

Origins of consecutive months overlap in their h-step errors and are dependent across countries through common shocks. The bootstrap therefore resamples origin calendar months in moving blocks (Kunsch, 1989), with the same month indices for all units (joint resampling), and a block length of max(h, 12) months. The choice of 12 follows from the memory of ACI, roughly 50 months at step 0.02, and from the overlap of errors. The per-unit statistics are recomputed on each replicate. Reported are the estimate, a 95 percent percentile interval and a two-sided centred bootstrap p-value (the share of replicates with |T* - T| at least |T|). The primary contrasts use 2000 replicates, so the smallest attainable p-value is about 0.0005. With a block length of 12 and fewer than about 16 months per unit, the bootstrap is degenerate (Section 6.7); the run `confirm13` is of this kind and is not used for any claim.

### 4.9 Equivalence testing (TOST)

A non-significant difference is not evidence of equality. DRACP against ACI is therefore also tested for equivalence with **two one-sided tests** (TOST; Schuirmann, 1987). The equivalence margin is 2 pp of CE. Two null hypotheses are tested, T <= -2 pp and T >= +2 pp, each against the bootstrap distribution shifted to the boundary. Equivalence is declared if the larger of the two p-values is below 0.05; otherwise the verdict is "not shown". The margin of 2 pp is fixed in advance and is not justified beyond that. TOST is reported separately and is not part of the Holm family.

### 4.10 Power and minimum detectable difference

The **minimum detectable difference** (MDE) is the smallest true reduction delta of CE for which the test has a power of at least 0.80 at the level used. The simulation (`exp/power.py`) keeps the observed hit pattern of the baseline method (so that cross-country common shocks and the overlap of errors stay in the data) and constructs the comparison method by thinning or thickening its hits so that its CE is lower by delta in each unit, on the same side of 0.90, with fixed uniform draws shared across delta values. Each simulated dataset is tested with the same centred block bootstrap as the real analysis. The test level is 0.05/4 for every contrast (the first Holm step), which gives a conservative bound. The MDE is reported in percentage points of mean CE. It is undefined if the power at 10 pp is still below 0.80. A contrast with an MDE that is undefined or above 7 pp is reported as inconclusive regardless of its p-value (rule R5). The MDE is also computed on random 15-month windows of the data, with 60 windows, to judge panels of the size of the post-2025-06 months.

### 4.11 FX-stress definition

Stress is secondary. The driver is the monthly exchange rate. For each country and month t, d(t) = ln(FX(t)/FX(t-1)); over the 60 preceding months (t excluded), m is the median and s = max(1.4826 * MAD, 0.005) the robust scale of d; z(t) = (d(t) - m)/s. A month is a shock event if |z(t)| exceeds 3, and the shock window is the event month and the 3 following months, with overlapping windows merged into episodes. For the continuous version used in the main stress analysis, stress at month t is the maximum of |z| over t-3 to t, and coverage is reported by within-country decile of stress at the forecast origin. The rule document is dated 2026-11-18 and states that the parameters were frozen before any forecast was run; the first commit that contains it is `58871dc`, dated 2026-11-19. The rule is not tuned.

---

## 5 Pre-specification and procedure

### 5.1 What "pre-specified" means here

The protocol (`experiment-protocol.md`) and the shock definition (`shock-definition.md`) are committed documents in the project repository. Changes are logged in their "Changes" sections with a date and a reason. "Pre-specified" in this paper means that a rule was committed to the repository before the run it governs. It does not mean registration in an external registry, and the order of events is not independently timestamped: the author is a single person, all entries are dated 2026-11-18 or 2026-11-19, and the order is attested only by a commit history kept by the same person. The decision rules R1-R5 were written after the exploratory results at both warm-ups were known (Section 5.2, item 4), so they were set by an author who knew how the design countries behaved.

### 5.2 Sequence

The commit hashes below are taken from the protocol and results documents where they are stated there, and otherwise from `git log` (marked "git log").

1. **Shock rule frozen.** The document `shock-definition.md` is dated 2026-11-18; the first commit that contains it is `58871dc` (git log), and no forecast had been computed. Validity checks were run afterwards (git log `9c0bdb7`) and are described in Section 5.4.
2. **Protocol draft 1** (git log `810a60c`), written before any forecast or interval had been computed. A committee review scored it 5.5 out of 10 (first change entry), and the claim hierarchy, FACI and conformal PID, reproduction tolerance, block length at least h, reduced primary tests and an MDE threshold were added before any forecast. A second entry added the second snapshot and the Nigerian break and restricted confirmatory analysis to the pooled panel. A partial reproduction of DRACP was recorded (git log `89996d2`) and the topic was fixed (git log `cb6de1b`).
3. **Third entry and the exploratory run v1.** Implementation decisions of the engine (start 2000-01, warm-up 48, window 120, ACI step 0.02, snapshot chaining) were fixed before results existed. The first run was exploratory only (`--start 2000-01 --end 2025-06`), so that no target month from 2025-07 could enter, and was made at code commit `2229076`. Results: `results-exploratory-v1.md` (git log `bf78f53`).
4. **Fourth entry, commit `0ff08d8`: amendments after the exploratory result and before any hold-out forecast.** Pooled-coverage contrasts were replaced by calibration error as the primary outcome; the reference changed from split to rolling conformal; DRACP against ACI became an equivalence question with a 2 pp margin; a fair DRACP sensitivity with warm-up 96 was added; the 7 hold-out countries became the main confirmatory pool; block length became at least 12; and the stress analysis was kept exploratory. The text of the entry states that the changes are motivated by logical defects of the design and not by significance. These amendments were made after the exploratory results were known.
5. **Fifth entry, commit `1480604`: hold-out run specification and decision rules R1-R5**, before any forecast was computed for the 7 hold-out countries. The runs were (A) warm-up 48 (primary), (B) warm-up 96 (sensitivity) and (C) an instant-feedback diagnostic at h=12; the original 13 countries to 2026-09 were listed as a supplementary pooled check. The entry states that none of the rules is changed after the result is seen.
6. **Hold-out run** and its results (`results-holdout-v1.md`; git log `46a2474`). First and only look at the 7 countries.
7. **Sixth entry, commit `552fa67`: robustness analyses S1-S5**, written after the hold-out result and before they were computed. They are secondary, do not replace R1-R5, and no threshold was changed. Their results are in `results-robustness-v1.md` (git log `de93501`).
8. **Seventh entry, commit `30d488c` (post hoc): additions S6 (Kazakhstan alone) and S7 (native intervals)**, requested by a review of the manuscript draft, recorded before they were computed and computed from existing outputs only. They are post hoc, descriptive or secondary, and are not part of the pre-specified family. Their results are in `results-addenda-v1.md`.
9. **Eighth entry, commit `dfe0b2c`: the extension (Section 5.6).** It specifies the second hold-out panel, the Chronos forecaster, the rules E1-E5 and the evaluation of a language-model explainer, and states that no forecast of any kind had been computed for the countries of the new panel. The explainer code is at `29532e7` (git log), the Chronos code, the leakage flag and the loading of the second panel at `ca43ddc`, and the results at `accd674` (`results-extension-v1.md`). The specification was written after R1-R5 had been applied and after the R2 outcome on the first hold-out panel and the robustness results were known; it does not change R1-R5 or any earlier result.

The exploratory results with the amended contrasts at both warm-ups (`explore_v1` and `explore_v2_ncal96`) were already known when R1-R5 were written.

### 5.3 Procedural boundary

The hold-out countries are untouched with respect to countries only. They are independent of the design sample by country, but they share calendar months with it (the global shocks of 2020 to 2022 fall in both samples). The set of methods, the form of the contrasts, the horizons, the 2 pp margin and the 3 pp and 7 pp thresholds were chosen on the 13 design countries. The author had also seen the post-2025-06 months of the 13 design countries before the amendments. The hold-out evaluation is therefore a test on new countries and not a fully blind test of the design. The stress analysis, S1-S4, and the post hoc additions S6 and S7 are secondary. The run on the post-2025-06 months of the 13 countries is degenerate and is not used. The second hold-out panel is independent of both earlier samples by country, but it too shares calendar months with them (2010 to 2026), and its rules E1-E5 were written by an author who knew every earlier result, including the R2 outcome on the first hold-out panel. It is a replication on new countries and not a blind test.

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

### 5.6 The extension: second hold-out panel, Chronos and the rules E1-E5

The eighth protocol entry (commit `dfe0b2c`, dated 2026-11-19) specifies the extension before any forecast, request or evaluation of it was computed. It does not change R1-R5. The extension was specified before any forecast of any kind was computed for the 10 countries of the second hold-out panel (Section 3.2).

**Runs.** All extension runs start at 2010-01. (E-A) Base models LightGBM, ARIMA, naive B and Chronos on the second hold-out panel at warm-up 48 (primary) and warm-up 96 (sensitivity, not promoted). (E-B) The four base models were run on the 13 design countries and the 7 first hold-out countries, as a secondary analysis; calibration contrasts were analysed only for LightGBM and Chronos, which narrows the E-B analysis of the protocol (a deviation; see the end of this section); because these runs start in 2010 and not in 2000, their numbers differ from those of Sections 6.1 and 6.2 and are not comparable with them cell by cell.

**Rules.** They are applied separately for each base model, with the CE family of the protocol (ACI minus rolling and DRACP minus ACI at h=3 and h=6, Holm over four tests; ACI minus split and ACI minus native secondary).

- **E1, replication on new countries.** A statement of R1, R2 or R3 is "replicated" for a base model only if the same rule as in the fifth entry is met in the same direction; otherwise it is reported as not replicated or inconclusive. Results at warm-up 96 are a sensitivity analysis and are not promoted.
- **E2, dependence on the base model.** The contrasts for the four base models are reported side by side, without a threshold.
- **E3, point accuracy of Chronos.** Mean absolute error relative to naive B per horizon, next to ARIMA, ETS and LightGBM, with a block-bootstrap 95% interval; descriptive.
- **E4, leakage.** Claims about the accuracy of Chronos are drawn only from the target months from 2025-01, pooled over all 30 countries, and the thinness of that sample is stated. Calibration contrasts for Chronos are reported on all months with the flag.
- **E5, power.** A contrast whose minimum detectable difference is undefined or above 7 pp is inconclusive.

**Multiplicity.** The Holm correction is applied within each base model (four tests). It is not applied across the four base models, and the four base models are evaluated on the same countries and months, so their results are not independent replications. No statement in this paper rests on pooling the four.

**Implementation note.** The first attempt to analyse the new panel failed because the country code NA (Namibia) was read as a missing value by the CSV reader. The reader was fixed with a regression test; the forecasts were not affected and were not recomputed, and only the analysis step was repeated.

**Deviations from the protocol.** (1) The four base models were run on the earlier 20 countries (re-run from 2010-01); calibration contrasts were analysed only for LightGBM and Chronos, which narrows the E-B analysis of the protocol. (2) The protocol asks for relative MAE (E3) with bootstrap intervals next to ARIMA, ETS and LightGBM; Table 18 (all months) has no intervals and no ETS, because ETS was not part of the extension runs. The clean-month analysis in Table 19 has intervals against LightGBM, ARIMA and naive B.

**The language-model explainer.** The eighth entry also fixes the evaluation of an explanation layer (Section 6.13); no result of that component enters the main claims.

---

## 6 Results

All results below use LightGBM as base model and nominal level 0.90, unless stated otherwise. A negative CE contrast means the first method is better calibrated. The exploratory results carry no confirmatory claim. The word "significant" is not used for any result outside the pre-specified family; unadjusted p-values are given as descriptive. Sections 6.1 to 6.10 concern the design panel and the first hold-out panel; Sections 6.11 to 6.13 report the extension (a second hold-out panel, four base models, Chronos) and are kept apart because the panel, the base models and the start date differ.

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

The calibration-error contrasts (Table 3) are shown at both warm-ups. At warm-up 48, ACI minus rolling was -2.2 pp at h=3 and -1.5 pp at h=6, with unadjusted p-values of 0.030 and 0.020 but Holm-adjusted p-values of 0.090 and 0.078, so neither survives the correction for the family. ACI minus split (secondary) was -4.6 pp at h=3 (95% CI [-5.0, -1.4], unadjusted p 0.001) and -3.4 pp at h=6 (p 0.0025). DRACP minus ACI was +0.2 pp and -0.2 pp, within noise. Equivalence within 2 pp was shown at warm-up 48 (maximum one-sided p 0.0085 at h=3 and 0.0135 at h=6) and not shown at warm-up 96 (0.128 and 0.146). At warm-up 96, in the exploratory data, DRACP was wider than ACI: its Winkler score was higher by 33.2 percent at h=3 (95% CI [12.1, 75.9], unadjusted p 0.049) and 19.9 percent at h=6 (95% CI [6.8, 46.2], unadjusted p 0.054). Equivalence in the exploratory data is therefore not stable across warm-up sizes.

**Table 3. Calibration-error contrasts, exploratory (pp of CE; 95% bootstrap CI; Holm p for the primary family)**

| Warm-up | h | Contrast | Family | T (pp) | 95% CI | p | Holm p |
|---|---|---|---|---|---|---|---|
| 48 | 3 | ACI - rolling | primary | -2.2 | [-2.7, 0.05] | 0.030 | 0.090 |
| 48 | 3 | DRACP - ACI | primary | +0.2 | [-1.2, +1.0] | 0.70 | 1.0 |
| 48 | 6 | ACI - rolling | primary | -1.5 | [-2.1, -0.1] | 0.020 | 0.078 |
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
- **Mean width.** The pooled mean width of DRACP intervals was larger than that of ACI at h=3 (4.97 against 4.28) and at h=12 (24.3 against 15.5).
- **Per-country spread.** At h=3 split coverage ranges from 0.822 (Peru) and 0.827 (Kazakhstan) to 1.000 (Indonesia); ACI ranges from 0.886 to 0.934. At h=12 ACI coverage ranges from 0.655 (Peru) and 0.716 (Nigeria) to 1.000 (Uzbekistan).
- **Long horizon.** At h=12 pooled coverage is below nominal for every method (0.825 to 0.869), and the adaptive methods do not repair it. The pooled bootstrap intervals are wide: for ACI the interval [0.797, 0.914] includes 0.90, and so do the intervals of DRACP, rolling and split (upper limits 0.918, 0.920 and 0.915); those of FACI and conformal PID do not (upper limits 0.876 and 0.897).
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

At h=12 the pooled coverage of every method is below 0.90 (0.833 to 0.884). The pooled bootstrap intervals are wide and the upper limits for ACI, DRACP, rolling and split are 0.923, 0.901, 0.918 and 0.919, so for these methods 0.90 is not excluded; for FACI and conformal PID the upper limits are 0.885 and 0.884.

The CE contrasts of the hold-out panel are in Table 5. The decision rules are applied as pre-specified.

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

**R1 (ACI better calibrated than split): not met in the primary run (warm-up 48); met at warm-up 96, which is a sensitivity run and is not promoted.** At warm-up 48 the CE difference ACI minus split was -3.0 pp (p 0.054) at h=3 and -2.8 pp (p 0.092) at h=6, with confidence intervals [-5.4, +0.5] and [-3.9, +1.2] that include zero. At warm-up 96 it was -4.1 pp (p 0.018) and -5.9 pp (p 0.0025). The direction replicates in both runs. The p-values in Table 5 for the secondary contrast are unadjusted bootstrap p-values; the CSV has no Holm column for this contrast, although R1 is written in terms of "Holm p". Applying Holm over the two horizons, as `results-holdout-v1.md` does, gives 0.108 at both horizons at warm-up 48, and 0.018 (h=3) and 0.005 (h=6) at warm-up 96. At warm-up 48 the rule fails with unadjusted p-values as well as with Holm-adjusted ones. The pre-specified verdict is "not met" for the primary configuration, and warm-up 96 was not promoted to the primary configuration because R1 holds there.

**R2 (ACI improves on rolling): not shown on this panel (MDE undefined, inconclusive).** (On the second hold-out panel of the extension the same rule is met at warm-up 48 in several cells; the two results are not combined, see Section 6.11.) Holm p was 0.35 (h=3) and 1.0 (h=6) at warm-up 48, and 0.59 and 0.99 at 96. On the Winkler score, ACI was 1.0 percent lower than rolling at h=3 (95% CI [-7.1, +4.1]) and 5.3 percent higher at h=6 (95% CI [+1.4, +8.1], unadjusted p 0.005; at warm-up 96, +9.2%, 95% CI [3.4, 15.3], unadjusted p 0.001). These Winkler contrasts are descriptive and unadjusted.

**R3 (DRACP against ACI): inconclusive.** Equivalence within 2 pp was shown at warm-up 48 (TOST p 0.0005 at h=3 and 0.047 at h=6) and not shown at warm-up 96 (0.062 and 0.355). Under the registered wording, "no advantage, equivalent within 2 pp" requires equivalence at both warm-ups, so the verdict is "inconclusive" and the equivalence result is not stable. DRACP minus ACI is not negative with Holm p below 0.05 at either warm-up, so "DRACP better" is also not supported. The wording used here for DRACP is therefore: no advantage over ACI was detected in this configuration; equivalence within 2 pp held at warm-up 48 but not at 96. The 2 pp margin is of the size of the calibration error of ACI itself (Section 7.2), so even the equivalence verdict at warm-up 48 is weak.

**R4 (delayed feedback explains the h=12 shortfall; ACI at least +3 pp): not met.** ACI coverage at h=12 was 0.884 with delayed feedback and 0.908 with instant feedback, a difference of +2.4 pp. The S3 interval for this difference is given in Section 6.5.

**R5 (power): all four primary contrasts are inconclusive.** The minimum detectable difference is undefined on the full hold-out sample at both warm-ups (`power_mde_ce.csv`): the baseline calibration error is too small for a 10 pp improvement to be attainable, so the power at 10 pp is below 0.80. On random 15-month windows of the hold-out data the median MDE is 2.6 to 3.1 pp, but 63 to 68 percent of windows have an undefined MDE (`power_mde_ce_windows15.csv`). The same full-sample MDE is also undefined in the exploratory data at warm-up 48. Under R5, a contrast with an undefined MDE is inconclusive regardless of its p-value, so none of the four primary contrasts supports a conclusion.

**Table R. Summary of outcomes (first hold-out panel; the second panel has its own outcomes in Table 16)**

| Rule | Outcome | Evidence |
|---|---|---|
| R1 | Not met in the primary run (warm-up 48); met at warm-up 96 (sensitivity, not promoted) | -3.0 pp (p 0.054), -2.8 pp (p 0.092) at 48, Holm 0.108 at both; -4.1 pp (p 0.018), -5.9 pp (p 0.0025) at 96, Holm 0.018 and 0.005 |
| R2 | Not shown (MDE undefined, inconclusive) | Holm p 0.35, 1.0 at 48; 0.59, 0.99 at 96 |
| R3 | Inconclusive | TOST p 0.0005, 0.047 at 48; 0.062, 0.355 at 96 |
| R4 | Not met | +2.4 pp against the 3 pp threshold |
| R5 | All four primary contrasts inconclusive | MDE undefined on the full hold-out sample |

**What the hold-out result supports.** Adaptive methods are better calibrated than a one-shot conformal calibration, with a direction replicated in the exploratory data and in the hold-out data at both warm-up sizes, and with a strength of evidence that depends on the warm-up; at the primary warm-up the confidence intervals include zero. On this panel it does not support the statements that adaptivity helps beyond a simple rolling window, or that DRACP is better than ACI (the second panel gives a different answer for the first of these, Section 6.11). Per-country coverage varies widely: at h=12 the standard deviation of coverage across units is 0.058 for ACI and 0.152 for split.

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

**S2, other base models.** The contrasts were recomputed with ARIMA and naive B as base models of the conformal methods (Table 9; T in pp of CE, unadjusted bootstrap p in brackets). ACI minus split is negative for all three base models in both samples; for naive B at h=6 on the hold-out panel it is -10.6 pp. All DRACP minus ACI equivalence tests at warm-up 48 say "equivalent" within 2 pp, except naive B at h=6 on the hold-out panel (p 0.0515); at warm-up 96 on the hold-out panel most are "not shown". The direction "ACI better than rolling" holds for every base model and both samples, but the unadjusted p-values range from 0.016 to 0.48, and none survives the correction of the pre-specified family.

**Table 9. S2: contrasts by base model (pp of CE, p in brackets)**

| Sample | Contrast, h | LightGBM | ARIMA | Naive B |
|---|---|---|---|---|
| Exploratory | ACI - rolling, 3 | -2.2 (0.030) | -1.7 (0.059) | -1.9 (0.053) |
| Exploratory | ACI - rolling, 6 | -1.5 (0.020) | -3.3 (0.016) | -1.9 (0.067) |
| Exploratory | DRACP - ACI, 3 | +0.2 (0.70) | +0.0 (0.98) | +0.1 (0.82) |
| Exploratory | DRACP - ACI, 6 | -0.2 (0.78) | -0.4 (0.54) | +0.4 (0.54) |
| Hold-out | ACI - rolling, 3 | -1.6 (0.087) | -3.0 (0.030) | -0.9 (0.22) |
| Hold-out | ACI - rolling, 6 | -0.7 (0.48) | -1.6 (0.21) | -3.2 (0.053) |
| Hold-out | DRACP - ACI, 3 | -0.1 (0.76) | -0.2 (0.80) | +0.2 (0.71) |
| Hold-out | DRACP - ACI, 6 | -0.3 (0.66) | +0.2 (0.79) | +0.3 (0.75) |

(The robustness document rounds the LightGBM hold-out DRACP minus ACI value at h=3 to -0.2 and the p-value of ACI minus rolling at h=3 to 0.088; the CSV values are -0.149 pp and 0.0875, shown here as -0.1 and 0.087, as in Table 5.)

**S4, calibration against width** (LightGBM, warm-up 48). Each cell of Tables 10 and 10b gives CE, the ratio of the mean Winkler score to that of rolling conformal, and the ratio of the median interval width to that of rolling conformal; a ratio below 1 is better than rolling. These are three different statistics (median width ratio, pooled mean width, Winkler score) and they are kept apart in Section 6.4. The Winkler contrast with a confidence interval is given in Section 6.2.

**Table 10. S4: CE / Winkler ratio / median width ratio (relative to rolling), hold-out**

| Method | h=1 | h=3 | h=6 | h=12 |
|---|---|---|---|---|
| ACI | 0.020 / 0.95 / 0.84 | 0.020 / 0.99 / 0.90 | 0.025 / 1.05 / 0.88 | 0.048 / 1.12 / 1.09 |
| DRACP | 0.021 / 0.97 / 0.89 | 0.019 / 0.96 / 0.91 | 0.022 / 1.04 / 0.91 | 0.047 / 1.25 / 0.97 |
| FACI | 0.024 / 0.95 / 0.85 | 0.023 / 0.94 / 0.90 | 0.013 / 1.00 / 0.90 | 0.070 / 1.07 / 0.92 |
| Conformal PID | 0.024 / 0.98 / 0.95 | 0.028 / 0.97 / 0.95 | 0.021 / 1.00 / 0.94 | 0.079 / 1.05 / 0.99 |
| Rolling | 0.029 / 1 / 1 | 0.036 / 1 / 1 | 0.032 / 1 / 1 | 0.086 / 1 / 1 |
| Split | 0.056 / 1.11 / 1.35 | 0.050 / 1.07 / 1.23 | 0.053 / 1.06 / 1.27 | 0.119 / 1.02 / 1.09 |

**Table 10b. S4: CE / Winkler ratio / median width ratio (relative to rolling), exploratory (13 countries, warm-up 48)**

| Method | h=1 | h=3 | h=6 | h=12 |
|---|---|---|---|---|
| ACI | 0.013 / 0.99 / 0.91 | 0.014 / 1.06 / 0.93 | 0.035 / 1.21 / 1.11 | 0.069 / 1.00 / 1.03 |
| DRACP | 0.016 / 1.07 / 0.95 | 0.016 / 1.16 / 0.95 | 0.033 / 1.21 / 1.09 | 0.074 / 1.38 / 1.69 |
| FACI | 0.014 / 1.00 / 0.95 | 0.018 / 1.05 / 0.94 | 0.041 / 1.06 / 0.88 | 0.101 / 0.96 / 0.91 |
| Conformal PID | 0.030 / 1.00 / 0.96 | 0.033 / 1.02 / 0.98 | 0.059 / 1.02 / 0.94 | 0.105 / 1.01 / 1.01 |
| Rolling | 0.038 / 1 / 1 | 0.036 / 1 / 1 | 0.050 / 1 / 1 | 0.091 / 1 / 1 |
| Split | 0.071 / 1.08 / 1.24 | 0.060 / 1.11 / 1.29 | 0.069 / 1.02 / 1.13 | 0.139 / 0.93 / 0.94 |

S3 is reported in Section 6.5.

### 6.4 Summary of the robustness reading and the question of narrower intervals

Adaptive methods are better calibrated than a one-shot calibration for all three base models and without dependence on any single country. The direction "ACI better calibrated than a rolling window by 1 to 3 pp of CE" is seen in most settings of the design panel and the first hold-out panel but is not established at the registered level there; on the second hold-out panel it is established at the registered level in part of the cells (Section 6.11), so the statement depends on the panel. Equivalence of DRACP and ACI within 2 pp holds for most base models at warm-up 48 and not at 96.

Three statistics must be kept apart when the question is whether adaptive intervals are narrower, and they do not give the same answer.

- **Median interval width ratio (to rolling).** At h=1 and h=3, ACI, DRACP and FACI have a median width below that of rolling in both samples: ACI 0.91 and 0.93 in the exploratory data, and 0.84 and 0.90 on the hold-out panel (Tables 10 and 10b).
- **Pooled mean width.** The pooled mean width of ACI at h=3 is larger than that of rolling in both samples: 4.28 against 3.95 in the exploratory data and 5.856 against 5.786 on the hold-out panel. This indicates heavy tails in the width of the adaptive intervals.
- **Winkler score.** The Winkler ratio to rolling for ACI, DRACP and FACI at h=1 and h=3 is 0.94 to 0.99 on the hold-out panel and 0.99 to 1.16 in the exploratory data (ACI 1.06 and DRACP 1.16 at h=3). In the exploratory data ACI's Winkler score at h=3 was 6.3 percent higher than rolling's (95% CI [0.3, 19.4], unadjusted p 0.15). At h=6 and h=12 the Winkler ratio of ACI and DRACP is above 1 in most cells of both samples (up to 1.38).

So the adaptive methods have a lower median width at short horizons, but the pooled mean width and the interval score do not show a consistent gain. No efficiency advantage is established; at long horizons the better calibration is paid for with width or interval score.

### 6.5 The delayed-feedback diagnostic at h=12

At h=12 pooled coverage is below nominal for every method (0.83 to 0.88 on the hold-out panel, 0.82 to 0.87 in the exploratory data), with the qualification on the bootstrap intervals given in Sections 6.1 and 6.2. To examine the role of delayed feedback, the diagnostic run releases each outcome at origin + 1 instead of origin + 12. Table 7 gives coverage with instant feedback minus coverage with delayed feedback, with a paired block-bootstrap 95 percent interval over the same (unit, origin) cells.

**Table 7. S3: change in h=12 coverage when feedback is instant (pp; 95% interval)**

| Method | Exploratory (1738 cells) | Hold-out (1009 cells) |
|---|---|---|
| ACI | +4.1 [1.4, 7.8] | +2.4 [-0.1, 4.8] |
| DRACP | +4.3 [1.4, 7.5] | +3.9 [1.6, 6.5] |
| FACI | +8.3 [4.3, 13.6] | +6.4 [2.5, 9.6] |
| Conformal PID | +5.1 | +5.3 |
| Rolling | +1.3 | +1.3 |
| Split | 0 | 0 |

In the hold-out panel, ACI coverage is 0.884 with delayed feedback and 0.908 with instant feedback. R4 as registered (ACI at least +3 pp on the hold-out panel) is not met: the result is +2.4 pp. The interval [-0.1, 4.8] is compatible with no effect and with an effect of about 5 pp. For FACI and DRACP the effect is positive in both samples. Split conformal does not use feedback, so its difference is zero by construction. The statement supported is that feedback delay accounts for part of the shortfall at h=12, with a size that depends on the method and the sample. It is not shown that delay is, or is not, the main cause. The diagnostic is not a valid forecasting setup and is not a primary result.

### 6.6 Stress analysis (secondary, exploratory)

For the exploratory sample at h=3, coverage in the top decile of FX stress at the forecast origin is 0.849 for ACI, 0.869 for DRACP and 0.874 for split, against roughly 0.87 to 0.98 in the other deciles. At h=6 it is 0.864, 0.879 and 0.874 respectively. With about 200 observations per decile, the standard error is roughly 2.5 pp, so the top-decile shortfall of ACI at h=3 is about two standard errors. The deciles in between are not monotone. This analysis is exploratory: the same 13 countries shaped the design, many deciles, methods and horizons were examined, and the underlying association between stress and forecast error is weak (Section 5.4). No stress result is reported for the hold-out panel in the results documents used for this draft, and no confirmatory claim about stress is made.

### 6.7 The post-2025-06 months of the 13 countries (not used)

Run `confirm13` evaluates the 13 design countries on target months from 2025-07. Eleven countries contribute (Nigeria ends in 2024-12 because of the CPI break; Russia has no usable stretch after 2022-03), each with at most 16 months. With blocks of 12 months on at most 16 months, the run is degenerate: confidence limits coincide with the estimate and p-values sit at the resampling floor. It is not used for any claim, and its contrast entries are not interpreted. Pooled coverage in that period is high for every method (ACI 0.904, 0.922 and 0.940 at h=1, 3 and 6, from 167 unit-months), which is consistent with calmer inflation, and no conclusion is drawn.

### 6.8 Kazakhstan (post hoc, descriptive)

The title of the paper does not name Kazakhstan because the main results contain no separate Kazakhstan analysis, but Kazakhstan was the original focus of the study, so this subsection reports it alone. The analysis S6 is post hoc (seventh protocol entry, Section 5.2), descriptive, and carries no test. Kazakhstan is one of the 13 design countries, so the numbers are from the exploratory sample and are not independent of the design. There are 137 monthly origins at h=1 (133, 127 and 115 at h=3, 6 and 12), with target months 2014-02 to 2025-06, so the period after the August 2015 float is mixed with the preceding managed regime. The standard error of a coverage figure from about 137 correlated origins is roughly 3 pp, so only the larger gaps are clearly outside noise.

**Table 11. S6: coverage for Kazakhstan alone (exploratory sample, LightGBM base, warm-up 48; calibration error in brackets)**

| Method | h=1 | h=3 | h=6 | h=12 |
|---|---|---|---|---|
| ACI | 0.898 (0.002) | 0.902 (0.002) | 0.906 (0.006) | 0.826 (0.074) |
| DRACP | 0.905 (0.005) | 0.902 (0.002) | 0.906 (0.006) | 0.826 (0.074) |
| FACI | 0.912 (0.012) | 0.910 (0.010) | 0.874 (0.026) | 0.800 (0.100) |
| Conformal PID | 0.810 (0.090) | 0.850 (0.050) | 0.882 (0.018) | 0.835 (0.065) |
| Rolling | 0.825 (0.075) | 0.865 (0.035) | 0.882 (0.018) | 0.826 (0.074) |
| Split | 0.730 (0.170) | 0.827 (0.073) | 0.803 (0.097) | 0.713 (0.187) |

For Kazakhstan, ACI, DRACP and FACI stay close to 0.90 up to h=6, while the rolling window, conformal PID and the one-shot split calibration under-cover at short horizons (rolling 0.825 and split 0.730 at h=1). At h=12 pooled coverage is below nominal for every method (0.713 to 0.835). The pattern is consistent with a series that changed regime in 2015, where a calibration that cannot adapt fast enough falls behind, but the data do not isolate that mechanism. Kazakhstan has too few independent episodes to be an inferential unit (Section 5.4); it is a descriptive case inside the panel.

### 6.9 Native intervals (post hoc, secondary)

The analysis S7 compares conformal calibration with the native (parametric) intervals of ARIMA (Gaussian) and ETS (simulated). It is post hoc (seventh protocol entry), secondary, and carries no multiplicity correction; the p-values are unadjusted and descriptive. Table 12 gives the mean over countries of the calibration error. ETS has no conformal version in the engine, so for ETS the native calibration error is reported without a contrast.

**Table 12. S7: calibration error (mean over countries of |coverage - 0.90|)**

| Sample | Interval | h=1 | h=3 | h=6 | h=12 |
|---|---|---|---|---|---|
| Exploratory (13) | ARIMA native | 0.047 | 0.066 | 0.089 | 0.137 |
| Exploratory (13) | ARIMA with ACI | 0.010 | 0.015 | 0.026 | 0.079 |
| Exploratory (13) | ETS native | 0.044 | 0.051 | 0.064 | 0.116 |
| Hold-out (7) | ARIMA native | 0.053 | 0.058 | 0.062 | 0.073 |
| Hold-out (7) | ARIMA with ACI | 0.014 | 0.013 | 0.024 | 0.040 |
| Hold-out (7) | ETS native | 0.056 | 0.035 | 0.048 | 0.053 |

**Table 13. S7: contrast ACI minus native, ARIMA base (pp of CE; 95% block-bootstrap interval; unadjusted p; block length max(h, 12))**

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

Conformal calibration with ACI gives a lower calibration error than the native intervals of the same ARIMA model at every horizon in both samples, by about 3 to 6 pp. On the hold-out panel the interval for the difference excludes zero at h=1 and h=3 and includes zero at h=6 and h=12. The mean coverage of the native ARIMA intervals looks acceptable on the hold-out panel (0.943, 0.930, 0.919 and 0.885 at h=1, 3, 6 and 12) because over-coverage in some countries offsets under-coverage in others; the calibration error shows the dispersion. The ETS native intervals have calibration errors of the same order as the ARIMA native ones in both samples. This contrast is secondary and post hoc; the evidence against native intervals is therefore weaker in procedure than the pre-specified contrasts, although its direction is consistent.

### 6.10 The platform module (engineering application)

The repository contains a module of the application that serves calibrated inflation intervals for the 13 design economies (`GET /api/v1/inflation/calibrated-forecast`, implemented in `backend/fastapi_service/app/services/inflation_calibration.py`, with a page that shows the measured backtest coverage next to the nominal level). The service reads a CPI snapshot and forms the point forecast as h times an exponentially weighted moving average of past monthly log growth (smoothing parameter 0.2). It issues intervals by ACI on absolute residuals over a rolling calibration window of 120 months with step 0.02, with delayed feedback, and requires at least 30 revealed residuals before issuing an interval. The point forecast, the minimum calibration size (30 against the benchmark's warm-up of 48) and the data differ from the benchmark, which uses LightGBM. The module is an engineering application and is not a scientific contribution of this paper. The benchmark results bear on it only through the interval method, and the platform's own backtest coverage is displayed to users.

### 6.11 Extension: calibration on the second hold-out panel (E1, E2, E5)

The second hold-out panel has 10 countries (ZM, AM, TZ, UG, KE, IQ, BW, NA, MZ, CI) with 198 months of CPI from 2010-01 (Section 3.2). At warm-up 48 there are 89 pooled calendar months at h=3 and 83 at h=6; at warm-up 96 there are 41 and 35. Four base models are used: LightGBM, ARIMA, naive B and Chronos (zero-shot, `amazon/chronos-bolt-tiny`). The Holm family has four tests per base model (Section 5.6). The tables are in `results/holdout2_ncal48/ce_<model>/` and `results/holdout2_ncal96/ce_<model>/`. Warm-up 48 is the primary run; warm-up 96 is a sensitivity run and is not promoted.

**Table 14. Calibration error (mean over the 10 countries of |coverage - 0.90|), second hold-out panel, warm-up 48; h=3 / h=6**

| Base model | ACI | DRACP | Rolling | Split | Native |
|---|---|---|---|---|---|
| LightGBM | 0.033 / 0.045 | 0.023 / 0.032 | 0.070 / 0.080 | 0.104 / 0.125 | none |
| ARIMA | 0.034 / 0.052 | 0.019 / 0.034 | 0.066 / 0.084 | 0.098 / 0.111 | 0.058 / 0.084 |
| Naive B | 0.049 / 0.052 | 0.037 / 0.034 | 0.090 / 0.087 | 0.122 / 0.105 | none |
| Chronos | 0.034 / 0.050 | 0.030 / 0.038 | 0.067 / 0.075 | 0.109 / 0.107 | none |

For comparison, on the first hold-out panel (LightGBM, Table 10) the calibration error of the rolling window at h=3 and h=6 is 0.036 and 0.032, against 0.070 and 0.080 here. This is a descriptive observation, and its relation to the results below was not tested.

**Table 15. Primary contrasts, second hold-out panel, warm-up 48 (T in pp of CE; 95% bootstrap interval; Holm p over the four primary tests of the base model)**

| Base model | ACI - rolling, h=3 | ACI - rolling, h=6 | DRACP - ACI, h=3 | DRACP - ACI, h=6 |
|---|---|---|---|---|
| LightGBM | -3.7 [-5.1, -0.7]; 0.008 | -3.5 [-4.9, +0.5]; 0.159 | -1.0 [-2.0, +0.9]; 0.321 | -1.3 [-2.7, +2.0]; 0.337 |
| ARIMA | -3.2 [-3.6, -1.1]; 0.004 | -3.1 [-3.9, -0.5]; 0.030 | -1.5 [-2.4, +0.8]; 0.199 | -1.8 [-3.4, +0.7]; 0.199 |
| Naive B | -4.1 [-4.9, -1.5]; 0.004 | -3.4 [-4.7, -0.4]; 0.039 | -1.2 [-2.3, +0.9]; 0.422 | -1.8 [-3.3, +2.5]; 0.422 |
| Chronos | -3.3 [-4.0, -0.3]; 0.036 | -2.5 [-3.6, +0.1]; 0.088 | -0.5 [-1.8, +1.3]; 0.454 | -1.2 [-2.2, +1.3]; 0.443 |

ACI minus split (secondary, unadjusted p, h=3 and h=6): LightGBM -7.0 and -8.0 pp (0.0005, 0.0005); ARIMA -6.4 and -5.8 (0.0005, 0.001); naive B -7.3 and -5.3 (0.001, 0.0045); Chronos -7.4 and -5.7 (0.0005, 0.0005). ACI with ARIMA has a lower CE than the native ARIMA intervals (0.034 against 0.058 at h=3 and 0.052 against 0.084 at h=6, Table 14); the contrast with its interval is not reported here.

**Table 16. Outcomes of the rules on the second hold-out panel (E1)**

| Rule | Warm-up 48 (primary) | Warm-up 96 (sensitivity, not promoted) |
|---|---|---|
| R1, ACI better calibrated than split | Met for all four base models at both horizons (unadjusted p at most 0.0045) | Not met: LightGBM (0.048) and naive B (0.032) at h=3 have unadjusted p below 0.05, all other cells are above 0.05, and with Holm over the two horizons none is below 0.05 (0.096 and 0.064) |
| R2, ACI improves on rolling (Holm p below 0.05) | Met at h=3 for LightGBM, ARIMA and naive B (Holm 0.008, 0.004, 0.004) and at h=6 for ARIMA and naive B (0.030, 0.039); Chronos at h=3: Holm 0.036, MDE undefined, inconclusive under E5, not counted as met; not met at h=6 for LightGBM (0.159) and Chronos (0.088) | Not shown for any base model (Holm p 0.147 to 1.0; MDE undefined, inconclusive) |
| R3, DRACP against ACI | Inconclusive (see below) | Inconclusive (see below) |
| E5, power | MDE for ACI - rolling 1.2 to 6.6 pp, undefined for Chronos at h=3; undefined for every DRACP - ACI contrast | Undefined for all contrasts |

**R1 at warm-up 48 and at 96.** On the new countries the advantage of ACI over a calibration performed once is met at the primary warm-up for all four base models, by -5.3 to -8.0 pp of CE. At warm-up 96 it is not met. The direction replicates and the registered threshold is met on the second panel at warm-up 48; on the first hold-out panel it was met only at warm-up 96.

**R2: the result differs from the earlier panels.** At warm-up 48 R2 is met on this panel at h=3 for LightGBM, ARIMA and naive B (Holm 0.008, 0.004, 0.004) and at h=6 for ARIMA and naive B (0.030, 0.039). For Chronos at h=3 the Holm p is 0.036 but the MDE is undefined, so under E5 that cell is inconclusive and is not counted as met; Chronos at h=6 and LightGBM at h=6 are not met (0.088, 0.159). On the design panel (Table 3) and on the first hold-out panel (Table 5) it was not shown, and the MDE is undefined there (inconclusive). The earlier 20 countries were re-run from 2010-01 (the four base models were run; calibration contrasts were analysed only for LightGBM and Chronos, which narrows the E-B analysis of the protocol, stated as a deviation in Section 5.6) as a secondary analysis, and R2 is not significant there: the Holm p-values of ACI minus rolling are 0.22 to 1.0, with the MDE undefined in every cell, so these results are inconclusive under E5 and not evidence of no effect. The results are placed side by side in Table 17 and are not pooled.

**Table 17. R2 (ACI minus rolling, pp of CE; Holm p over the four tests of the run) across panels, warm-up 48**

| Panel and run | Base model | h=3 | h=6 | Outcome |
|---|---|---|---|---|
| Design panel (13), from 2000 (Table 3) | LightGBM | -2.2; 0.090 | -1.5; 0.078 | Not shown (MDE undefined, inconclusive) |
| First hold-out (7), from 2000 (Table 5) | LightGBM | -1.6; 0.35 | -0.7; 1.0 | Not shown (MDE undefined, inconclusive) |
| Design panel (13), re-run from 2010 | LightGBM | -2.1; 0.216 | -2.0; 0.216 | Not met; MDE undefined in every cell: inconclusive under E5 |
| Design panel (13), re-run from 2010 | Chronos | -1.9; 0.363 | -2.0; 0.358 | Not met; MDE undefined in every cell: inconclusive under E5 |
| First hold-out (7), re-run from 2010 | LightGBM | -2.4; 0.496 | -4.7; 0.390 | Not met; MDE undefined in every cell: inconclusive under E5 |
| First hold-out (7), re-run from 2010 | Chronos | -1.3; 1.000 | -2.0; 0.962 | Not met; MDE undefined in every cell: inconclusive under E5 |
| Second hold-out (10), from 2010 | LightGBM | -3.7; 0.008 | -3.5; 0.159 | Met at h=3 |
| Second hold-out (10), from 2010 | ARIMA | -3.2; 0.004 | -3.1; 0.030 | Met at both |
| Second hold-out (10), from 2010 | Naive B | -4.1; 0.004 | -3.4; 0.039 | Met at both |
| Second hold-out (10), from 2010 | Chronos | -3.3; Holm 0.036, MDE undefined: inconclusive (E5) | -2.5; 0.088 | Inconclusive at h=3; not met at h=6 |

Three things should be read together. First, the point estimates are negative in every row of Table 17. On the second panel they (-2.5 to -4.1 pp) are generally larger than on the earlier panels (-0.7 to -2.4 pp), with one exception, LightGBM on the re-run first hold-out panel at h=6 (-4.7 pp, Holm p 0.390, 95% interval [-9.6, +0.5]); so the direction does not differ between panels, but its size and its distance from the registered threshold do. Second, the conclusion that "ACI improves on a rolling window" is reached under the registered rule on one panel and not on the other two. The data do not say why. Candidate explanations are a shorter series (198 months from 2010), lower-income and more volatile economies, a larger share of the 198 months taken by the warm-up, and a rolling window with a larger calibration error here (Table 14); none of them was tested, and none is claimed. Third, the four base models are evaluated on the same 10 countries and the same months, so the three "met" cells at h=3 are not three independent confirmations, and the Holm correction does not extend across the base models (Section 5.6). We do not average the panels into one statement and do not select the panel on which the rule is met.

**Warm-up 96 on the second panel shows nothing.** After a warm-up of 96 the panel has 41 pooled months at h=3 and 35 at h=6. ACI minus rolling is -1.0 to -3.3 pp at h=3 (Holm p 0.147 to 1.0). At h=6 it is +0.2 pp (LightGBM), +1.1 pp (Chronos), -0.5 pp (ARIMA) and -0.6 pp (naive B), with Holm p of 0.59 or more. The minimum detectable difference is undefined for every contrast. The run is a sensitivity run, it neither confirms nor contradicts the primary run, and it is not promoted.

**R3 stays inconclusive.** At warm-up 48 DRACP has a lower CE than ACI in every cell, by 0.5 to 1.8 pp, and no difference has Holm p below 0.05 (0.199 to 0.454). Equivalence within 2 pp holds only for Chronos at h=3 (TOST p 0.0385) and is not shown in the other seven cells (p 0.15 to 0.76). At warm-up 96 equivalence holds for LightGBM and naive B at h=3 (p 0.0375 and 0.013) and not in the other six cells, and DRACP is better than ACI only at h=6 for naive B (-2.3 pp, Holm p 0.002). R3 requires the same verdict at both warm-ups, so it is not met. Under E5 every DRACP minus ACI contrast at warm-up 48 has an undefined minimum detectable difference and is inconclusive whatever its p-value, including the equivalence of Chronos at h=3. The small and consistent tendency of DRACP towards a lower CE at warm-up 48 is a descriptive observation and not a result.

**E5, power.** At warm-up 48 the minimum detectable difference for ACI minus rolling is 3.2 pp (h=3) and 6.1 pp (h=6) for LightGBM, 3.2 and 3.5 pp for ARIMA, 1.2 and 3.5 pp for naive B, and 6.6 pp for Chronos at h=6; it is undefined for Chronos at h=3, so that cell is not conclusive under the rule even though Holm p is 0.036. Where R2 is not met (LightGBM and Chronos at h=6) the minimum detectable difference of 6.1 and 6.6 pp is larger than the estimates, so "not met" there is not evidence that the effect is absent.

**E2, dependence on the base model.** On this panel the direction and the size of the contrasts are alike for the four base models (Tables 14 and 15). The conclusions about R1 and R3 do not depend on the base model; the conclusion about R2 at h=6 does (met for ARIMA and naive B, not for LightGBM and Chronos), and at h=3 Chronos is inconclusive under E5 while LightGBM, ARIMA and naive B are met. On the earlier 20 countries, re-run from 2010-01 (the four base models were run; calibration contrasts were analysed only for LightGBM and Chronos, which narrows the E-B analysis of the protocol, stated as a deviation in Section 5.6), the effect is weaker: ACI minus rolling is -1.3 to -4.7 pp with Holm p 0.22 to 1.0, and ACI minus split is -3.5 to -9.4 pp with unadjusted p between 0.002 and 0.045.

R4 (delayed feedback) was not part of the extension, and no instant-feedback run was made on the second panel.

### 6.12 Extension: point accuracy of Chronos and the question of leakage (E3, E4)

Table 18 gives the mean absolute error relative to naive B (below 1 is better) on the second hold-out panel, all target months, warm-up 48, pooled over the origins of the panel. Months before 2025-01 are flagged `possibly_seen` for Chronos, which may have met these public series in pretraining; Table 18 therefore includes months on which Chronos may have an unfair advantage, and it is not used for any claim about Chronos.

**Table 18. Relative mean absolute error (naive B = 1), second hold-out panel, all months, warm-up 48** (note: deviation from the protocol, E3 asks for bootstrap intervals next to ARIMA, ETS and LightGBM; this table has no intervals and no ETS, because ETS was not part of the extension runs; the clean-month analysis in Table 19 has intervals against LightGBM, ARIMA and naive B)

| Model | h=1 | h=3 | h=6 | h=12 |
|---|---|---|---|---|
| Chronos (flagged months included) | 0.737 | 0.586 | 0.581 | 0.934 |
| ARIMA | 0.779 | 0.602 | 0.570 | 0.880 |
| LightGBM | 0.817 | 0.619 | 0.593 | 0.943 |

Following E4, claims about accuracy are drawn only from target months from 2025-01. These are 22 calendar months with 567 country-month cells per horizon, pooled over the 30 countries of the three panels (`scripts/thesis/extension_accuracy.py`). Table 19 gives the difference in mean absolute error (Chronos minus the other model, in pp of cumulative growth; negative favours Chronos) with a paired block-bootstrap 95% interval (blocks of 3 months, months resampled jointly across countries). The intervals are unadjusted and descriptive.

**Table 19. Chronos minus other model, mean absolute error, target months from 2025-01 (pp; 95% interval)**

| h | Against LightGBM | Against ARIMA | Against naive B |
|---|---|---|---|
| 1 | -0.023 [-0.047, -0.007] | -0.037 [-0.053, -0.021] | -0.104 [-0.134, -0.081] |
| 3 | -0.031 [-0.078, +0.036] | -0.086 [-0.139, -0.031] | -0.350 [-0.519, -0.206] |
| 6 | -0.084 [-0.129, -0.025] | -0.097 [-0.204, +0.002] | -0.720 [-0.905, -0.528] |
| 12 | -0.245 [-0.465, -0.019] | -0.024 [-0.122, +0.139] | -0.256 [-0.449, -0.041] |

On these clean months the relative mean absolute error of Chronos is 0.774, 0.699, 0.654 and 0.895 at h=1, 3, 6 and 12 (LightGBM 0.824, 0.725, 0.694, 0.995; ARIMA 0.854, 0.773, 0.700, 0.905). Against LightGBM the interval excludes zero at h=1, 6 and 12, and against ARIMA at h=1 and 3 (at h=6 its upper limit is +0.002); against naive B it excludes zero at every horizon. No interval favours LightGBM or ARIMA over Chronos. The reading is that Chronos was at least as accurate as LightGBM and ARIMA in this period and more accurate than the naive baseline. The sample is thin (22 months), the block length is short because of it, the leakage assumption (the cutoff of 2025-01) is not verified, and the results are descriptive and are not a ranking of forecasters. Calibration contrasts for Chronos (Section 6.11) use all months with the flag, as specified in E4, and no calibration analysis restricted to the clean months is reported.

### 6.13 Extension: the language-model explainer (status; no result)

An explanation layer was designed and implemented: a service (`backend/fastapi_service/app/services/inflation_explainer.py`, commit `29532e7`) receives a question about a country and a horizon, calls the platform endpoint of Section 6.10 as a tool and answers in English, Russian or Kazakh. Its evaluation was specified in the eighth protocol entry before any request was made: 13 countries, 4 horizons, 3 question types and 3 languages give 468 prompts, each answered in two conditions (with the tool result in the context, and without it as an ungrounded baseline). The metrics are computed by program and not by a judge model: numerical faithfulness, omission rate and coverage overstatement, with Wilson 95% intervals, and a manual review of 30 answers per language for fluency and terminology; there is no pass threshold.

**The evaluation has not been run on a real language model, and no result is reported.** The service and the harness were tested with a deterministic fake client that only exercises the code; the tables it produces are not results. The test suite of the LLM layer has 18 tests (31 together with the 13 platform-service tests). To run the evaluation an API key for the model provider is needed (`OPENROUTER_API_KEY`, or the fallback `GROQ_API_KEY`), the model identifier must be written into the code and into the results before the run, and the command must be confirmed with `--yes-spend`; it makes 936 calls (468 prompts in two conditions), an estimated 0.3 million input and 0.2 million output tokens. No claim of this paper depends on this component.


---

## 7 Discussion

### 7.1 What is established and what is not

Four statements are supported by the evidence, with the qualifications given. First, adaptive conformal intervals (ACI, FACI, conformal PID, DRACP) were better calibrated than a conformal calibration performed once on the first months and never updated. The direction is the same in the exploratory data, in the hold-out panel at both warm-ups, for three base forecasters, and after removing any single country (Table 8). The strength of the evidence depends on the warm-up size: the registered rule R1 was met only at warm-up 96, which is a sensitivity run, and at the primary warm-up 48 the confidence intervals of the contrast include zero ([-5.4, +0.5] at h=3 and [-3.9, +1.2] at h=6). The statement is therefore one of consistent direction, not of a pre-specified confirmation. On the second hold-out panel of the extension R1 was met at warm-up 48 for all four base models and not at warm-up 96 (Section 6.11), which adds a replication at the primary warm-up on new countries. Second, in a secondary, post hoc analysis, ACI with an ARIMA base model had a lower calibration error than the native ARIMA intervals at every horizon in both samples; on the hold-out panel the interval includes zero at h=6 and h=12 (Section 6.9). Third, at the 12-month horizon pooled coverage is below nominal for every method, and delayed feedback accounts for part of the shortfall, the size depending on the method and sample. Fourth, at short horizons ACI, DRACP and FACI have a median interval width below that of a rolling window in both samples, but the pooled mean width of ACI at h=3 is larger than that of rolling in both samples, and the Winkler advantage exists only on the hold-out panel (Section 6.4); no efficiency advantage is established.

Three statements are not established, and the first of them is split by panel. (i) Whether ACI improves on a rolling window depends on the panel. On the design panel and the first hold-out panel it was not shown (R2); the point estimates are negative, in the direction of an advantage of about 1 to 3 pp of CE, but they do not reach the registered level, and their MDE is undefined, so they are inconclusive; the re-run of the earlier 20 countries from 2010-01 shows the rule as not significant (Holm p 0.22 to 1.0), again with the MDE undefined in every cell and so inconclusive under E5. On the second hold-out panel the rule is met at warm-up 48 at h=3 for LightGBM, ARIMA and naive B (Holm 0.008, 0.004, 0.004) and at h=6 for ARIMA and naive B (0.030, 0.039); for Chronos at h=3 the Holm p is 0.036 but the MDE is undefined, so it is inconclusive under E5 and not counted as met, and Chronos and LightGBM at h=6 are not met (0.088, 0.159) (Section 6.11). The reason for the difference is not known, and candidate explanations were not tested. The panels are not pooled; the statement supported by the evidence taken together is that the result is panel dependent, and it is neither "ACI does not improve on a rolling window" nor "ACI improves on a rolling window". (ii) An advantage of DRACP over ACI was not detected, and equivalence within 2 pp was not stable across warm-up sizes (R3); on the second panel DRACP had a lower CE than ACI in every cell at warm-up 48 by 0.5 to 1.8 pp, with no difference at Holm p below 0.05, and the verdict stays inconclusive. (iii) That delayed feedback explains the h=12 shortfall was not met at the registered threshold (R4). None of these results is evidence that the effects are absent. In particular, the wording "DRACP does not transfer" or "ACI and DRACP are equal" is not allowed by the data. Two descriptive findings of the extension carry no inferential weight: Chronos used zero-shot as a base forecaster leaves the calibration conclusions unchanged, and on the 22 target months from 2025-01 its mean absolute error was at least as low as that of LightGBM and ARIMA (Section 6.12). The language-model explainer has not been evaluated, and nothing is claimed about it (Section 6.13).

### 7.2 Why null results, power, the ceiling effect and the equivalence margin

Several reasons may contribute to the null outcomes, and the data do not allow us to apportion them.

**Sample size and dependence.** The hold-out panel has 7 countries and about 200 origin months at h=3. Errors of h-step forecasts overlap, adaptive methods have a long memory (about 50 months at step 0.02), and countries share common shocks. The block bootstrap respects this dependence at the cost of wide intervals; the 95 percent intervals of the primary contrasts are about 2 to 6 pp wide on the CE scale (Table 5).

**Ceiling effect.** The calibration error of the rolling baseline is already small: in the hold-out panel its CE is 0.029 at h=1, 0.036 at h=3 and 0.032 at h=6 (Table 10), and ACI's is 0.020, 0.020 and 0.025. There is little room to improve. The power simulation reflects this: its alternative cannot reduce CE below zero, so the improvement it can create is bounded by the baseline CE (about 3 to 4 pp), and 80 percent power at the first Holm step was not reached up to 10 pp on the full hold-out sample. The MDE is therefore undefined for all four primary contrasts (R5). The same is true for the exploratory sample. The MDE on random 15-month windows has a median of 2.6 to 3.1 pp on the hold-out panel, but is undefined in 63 to 68 percent of windows. A contrast without defined power cannot support a claim of absence of an effect, and the pre-specified R5 therefore classifies all four contrasts as inconclusive. We interpret this as a limit of the design (a small and already well-calibrated reference) and not as a finding about the methods.

**The equivalence margin is about the size of ACI's own calibration error.** The equivalence margin of 2 pp is about the size of the calibration error of ACI itself (about 1.5 to 2 pp at h=1 and h=3: 0.013 and 0.014 in the exploratory data, and 0.020 and 0.020 on the hold-out panel). A test of whether DRACP differs from ACI by less than 2 pp therefore asks whether a method with an error of about 2 pp differs from another by less than that amount, and the verdict "equivalent" is weak by construction. For the same reason the contrasts against ACI cannot be powered: this is a ceiling effect, and the null outcomes for ACI against rolling and for DRACP against ACI were likely before the run. The informative contrasts are those against weak references, split (CE 0.050 to 0.056 on the hold-out panel at h=1 to 6) and the native intervals (Section 6.9), where there is room for a difference. The margin of 2 pp was fixed in advance and is not justified beyond that.

**The ACI-against-rolling result depends on the panel.** The second hold-out panel is an honest counter-example to the null outcomes above, and it must be reported next to them. At warm-up 48 the registered rule R2 is met there (at h=3 for LightGBM, ARIMA and naive B, Holm 0.008, 0.004, 0.004, and at h=6 for ARIMA and naive B, 0.030 and 0.039; Chronos at h=3 has Holm 0.036 but an undefined MDE, so it is inconclusive under E5 and not counted as met), where it was not shown on the design panel and the first hold-out panel, and it is not significant on the earlier 20 countries re-run from 2010-01 (all four base models were run there; calibration contrasts were analysed only for LightGBM and Chronos), where the MDE is undefined in every cell, so those results are inconclusive and not evidence of no effect. The data do not say why. Panel differences are candidate explanations: a shorter series (198 months from 2010-01), lower-income and more volatile economies, a warm-up that takes a larger share of 198 months, and a larger calibration error of the rolling window, which leaves more room (0.066 to 0.090 at h=3 against 0.036 on the first hold-out panel). The last point is consistent with the ceiling argument above, because on this panel the minimum detectable difference for ACI minus rolling is defined (1.2 to 6.6 pp), but consistency is not a test, and none of these candidates was tested. Warm-up 96 on the new panel cannot arbitrate: it has 41 and 35 pooled months, an undefined minimum detectable difference and point estimates of both signs. Two reading errors are avoided. The panels are not averaged into a single estimate, because they differ in the number of countries, the length of the series, the start date and the base models, and because the registered rules apply to each panel by itself. The favourable panel is not selected either: the evidence is one panel on which the rule is met and two on which it is not, and a correction across the four base models, which share their countries and months, was not applied. A reader who wants a recommendation for a new set of countries cannot take it from this study.

**A true small or zero difference.** The data are also compatible with ACI and a rolling window being close to each other in this setting, and with DRACP and ACI being close, but this cannot be separated from low power with the present sample.

**Specific to DRACP.** DRACP trains its regime and scale models on half of the warm-up (24 rows at warm-up 48), which is a small sample for these models, and its results depend on the warm-up: equivalence holds at 48 and not at 96. In the exploratory data at warm-up 96, DRACP was wider than ACI: its Winkler score was 33 percent higher at h=3 (Section 6.1). This does not hold on the hold-out panel: at warm-up 96 the Winkler score of DRACP was 5.8 percent lower than that of ACI at h=3 (95% CI [-14.2, +3.3], unadjusted p 0.18), with a mean width of 6.11 against 6.31, and the mean width of DRACP is larger than ACI's only in the exploratory data (4.97 against 4.28 at h=3). The authors of DRACP state that the advantage of their method is specific to one-step-ahead forecasting and depends on the point forecaster (Section 2.3); the present design uses multi-month cumulative targets, a different point forecaster and a different panel, and it does not test their one-step claim. Our reproduction of the one-step setting was partial and qualitative: ACI 0.874 and DRACP 0.871 in coverage over 5 countries with one seed, against 0.884 and 0.890 reported by the authors over 48 series, so the claim of being closest to nominal could not be distinguished from ACI there either. This is a limitation of the transfer comparison, not a finding about the method.

### 7.3 Implications for practice

A practitioner who produces inflation intervals for a commodity-dependent economy should not calibrate once and leave the calibration unchanged: one-shot calibration had a higher calibration error than ACI in every CE contrast reported (both samples, both warm-ups, three base models), with a consistent direction, although the registered rule R1 was met only at the sensitivity warm-up and the confidence intervals at the primary warm-up include zero. Its coverage also varied the most across countries (the standard deviation of coverage across units at h=12 is 0.152 for split against 0.058 for ACI on the hold-out panel). The native intervals of an ARIMA model had a higher calibration error than ACI on the same model in both samples, in a post hoc comparison. Updating the calibration, either with a rolling window or with ACI, is a low-cost improvement. Between a rolling window and ACI this study cannot recommend one on statistical grounds, because the comparison depends on the panel (not shown on two panels, met at warm-up 48 on a third, Section 6.11), and it cannot recommend one on efficiency grounds either: the median width of ACI is smaller at short horizons, the pooled mean width and the Winkler score do not show a consistent gain (Section 6.4). At the 12-month horizon, pooled coverage is below nominal for every method (0.83 to 0.88 on the hold-out panel), and users should treat the nominal level there as an upper bound. A part of the shortfall comes from the delay with which the outcome arrives, and cannot be removed in real use.

### 7.4 The choice of ACI in the platform

The platform uses ACI. ACI was chosen as an adaptive method that is better calibrated than a one-shot calibration and than native intervals, and it is simple to implement and explain. The benchmark did not show it to be better than a rolling window on the design panel and the first hold-out panel, and on the second hold-out panel it was better at warm-up 48 in part of the cells; the result depends on the panel. No efficiency advantage (narrower intervals without a loss of interval score) is claimed. The platform module is an engineering application with a simpler point forecast (an exponentially weighted moving average, with a minimum calibration size of 30) and is not a scientific contribution of the paper. The platform displays measured backtest coverage next to the nominal level so that a user can see the actual calibration.

### 7.5 Scope of the hold-out and of the term "commodity-dependent"

**Independence of the hold-out.** The hold-out countries are independent of the design sample by country only. They share calendar months with it, including the global shocks of 2020 to 2022, so common shocks affect both samples. The methods, the contrasts and the horizons were chosen on the design countries. The agreement between the two samples is therefore weaker evidence of generality than if the hold-out countries had been observed in different periods. The second hold-out panel (2010 to 2026) shares calendar months with both earlier samples in the same way, and its rules E1-E5 were written after all earlier results were known. Its agreement with the earlier samples on R1 and its disagreement on R2 are both results about new countries, not about new periods.

**Commodity dependence is not defined by a measurable criterion.** No export-share rule was applied to select the countries, and Georgia and Uruguay are borderline cases. The hold-out sets were determined by IMF data availability under fixed rules: 7 of 14 candidates qualified for the first panel, and the first 10 eligible candidates formed the second panel (Section 3.2). The phrase "commodity-dependent economies" in the title describes the intended setting and not a tested property of the panel; the study does not compare commodity-dependent with other economies.

---

## 8 Limitations

1. **Procedural boundary.** The hold-out countries are untouched with respect to countries only, and they share calendar months with the design sample. The methods, the form of the contrasts, the horizons, the margin of 2 pp and the thresholds of 3 pp and 7 pp were chosen on the 13 design countries, and the author had seen the post-2025-06 months of these countries before the amendments. The rules R1 to R5 were written after the exploratory results at both warm-ups were known. The pre-specification is a repository commit history, kept by one author and self-attested, with all entries on 2026-11-18 or 2026-11-19, and not an external registry or an independent timestamp.
2. **Power and the ceiling effect.** The minimum detectable difference is undefined on the full hold-out sample for all four primary contrasts. All null outcomes are therefore inconclusive and are not evidence of equality. The 2 pp equivalence margin is about the size of ACI's own calibration error, so the equivalence verdict for DRACP against ACI is weak by construction and the contrasts against ACI cannot be powered; null outcomes were likely before the run. The MDE simulation has not been reviewed independently, and it assumes that the observed hit pattern of the baseline describes the true dependence and that dependence beyond the block length is zero.
3. **Small panel.** The hold-out panel has 7 countries; Ghana and Angola have high-inflation episodes, so pooled results can be driven by few units. S1 shows that removing one country changes the sign of ACI against rolling at h=6 on the hold-out panel in one case of seven.
4. **One point-forecaster family dominates the contrasts of Sections 6.1 to 6.10.** LightGBM is the base model for the primary family of R1-R5. ARIMA and naive B give the same direction in S2, but they were not part of the registered decision rules. In the extension the four base models share the same countries and months, so they are not independent replications, and the Holm correction is applied within each base model and not across them.
5. **Data revisions and vintages were not checked.** The IMF publishes dated CPI vintages, which allow a real-time revision check, but this was not done. Evaluation uses the revised data of the snapshot date. Small revisions for Russia and Mongolia are noted between the two snapshots, but their effect on intervals was not studied. Nigeria's series ends at 2024-12 because of a methodology break, so that country has no recent months.
6. **No systematic literature search was run.** The statements about novelty and the state of the literature are based on the author's reading only. Several statements are marked [CITATION NEEDED] and the bibliography is limited to a fixed list of works.
7. **"Commodity-dependent" is not defined by a measurable criterion.** No export-share rule was applied to the 13 design countries or to the hold-out candidates; Georgia and Uruguay are borderline. The hold-out set was determined by IMF data availability under a fixed written rule, and 7 of 14 candidates qualified.
8. **Reproduction of DRACP is partial.** Five countries with annual HICP inflation, one seed, and a mean coverage of ACI 0.874, DRACP 0.871 (against 0.884 and 0.890 reported over 48 series with 20 seeds). The criterion of reproducing a published number within 2 pp could not be tested because the published numbers are averages over different series. The DRACP configuration in the benchmark follows the reproduction script and was not tuned. The description of DRACP in Section 2.3 is as described by its authors and was read, not re-derived.
9. **Calibration error is noisy and its bootstrap is not validated at the boundary.** CE is biased upward in small samples, and percentile intervals are not symmetric around the estimate. The validity of the CE bootstrap at the boundary of the absolute value (where coverage is close to 0.90) was not checked by simulation, so the size of the test is unknown. The choice of the 2 pp equivalence margin and of the 3 pp threshold of R4 is not justified beyond being fixed in advance.
10. **Stress analysis is secondary and exploratory.** The FX-based flag is a weak proxy of inflation shocks (lift below 2), is affected by exchange-rate regimes, and many deciles, methods and horizons were examined. Pegged and managed currencies were not analysed separately.
11. **Items in the protocol that are not reported.** The central-bank target baseline, the exchange-rate-regime split, and per-country heterogeneity beyond coverage ranges are mentioned in the protocol; the results documents do not report them. The foundation-model forecaster (Chronos) is reported in Sections 6.11 and 6.12 as an extension, with the limitations of items 16 to 20. The native ARIMA and ETS intervals are reported only as a post hoc secondary analysis (Section 6.9), and Kazakhstan only descriptively (Section 6.8).
12. **The post-2025-06 months of the 13 countries are degenerate** (at most 16 months per unit, blocks of 12) and are not used for any claim. The h=12 horizon has few non-overlapping windows (80 non-overlapping cells on the hold-out panel in run A).
13. **The platform is not the benchmark.** The platform uses an EWMA point forecast and a smaller minimum calibration size, so the benchmark results apply to its interval method but not to its point forecast. The module is an engineering application and not a scientific contribution.
14. **Point forecasts matter for interval width but were not optimised.** All hyperparameters were fixed in advance, and the point models are simple; better point forecasts could change absolute calibration and width.
15. **The post hoc additions have no multiplicity correction.** S6 (Kazakhstan) is descriptive with about 137 origins of one design-panel country and no test; S7 (native intervals) uses unadjusted p-values and one base model for the contrast.
16. **The ACI-against-rolling result depends on the panel, and the reason is not known.** R2 is met at warm-up 48 on the second hold-out panel (at h=3 for LightGBM, ARIMA and naive B, Holm 0.008, 0.004, 0.004, and at h=6 for ARIMA and naive B, 0.030 and 0.039; Chronos at h=3, Holm 0.036, has an undefined MDE and is inconclusive under E5) and is not shown (MDE undefined, inconclusive) on the design panel and the first hold-out panel, and not significant (MDE undefined in every cell, inconclusive) on the earlier 20 countries re-run from 2010-01. Candidate explanations (a shorter series, more volatile and lower-income economies, a warm-up that takes a larger share of the series, a rolling window with a larger calibration error) were not tested. The panels are not pooled, and no panel is selected.
17. **The second hold-out panel is short.** It has 198 months from 2010-01, so 89 and 83 pooled months at h=3 and h=6 at warm-up 48, and 41 and 35 at warm-up 96. Warm-up 96 shows nothing on it, and the minimum detectable difference is undefined for every contrast at warm-up 96 and for every DRACP minus ACI contrast at warm-up 48. Several of its countries are the candidates that failed the first hold-out rule on history length, so the two panels differ in the length of their series by construction.
18. **Chronos: possible leakage and a thin clean sample.** Chronos may have seen public CPI series in pretraining. The pretraining cutoff was not verified, and 2025-01 is a conservative assumption. Accuracy claims rest on 22 calendar months (567 country-month cells per horizon), with a short block length. Calibration contrasts for Chronos use all months with the flag, and no analysis restricted to clean months is reported. Only the smallest Chronos-Bolt model was used, zero-shot; larger models, fine-tuning and covariates were not tried. On the earlier 20 countries the four base models were run; calibration contrasts were analysed only for LightGBM and Chronos, which narrows the E-B analysis of the protocol (stated as a deviation in Section 5.6).
19. **The language-model explainer is not evaluated.** The 468-prompt, two-condition evaluation (936 calls) is specified but was not run on a real model, because it needs an API key; the fake-client output is not a result. No claim is made about the faithfulness, omissions or overstatements of such a layer.
20. **Extension specified with knowledge of earlier results.** The eighth entry and the rules E1-E5 were written after R1-R5 had been applied and all earlier results, including R2 on the first hold-out panel, were known; the extension is a replication on new countries in the sense of Section 5.3 and not a blind test.

---

## 9 Reproducibility

**Repository layout.**

| Path | Content |
|---|---|
| `docs/thesis/` | `topic.md`, `experiment-protocol.md` (with the "Changes" log), `shock-definition.md`, results documents `results-exploratory-v1.md`, `results-holdout-v1.md`, `results-robustness-v1.md`, `results-addenda-v1.md` (post hoc S6 and S7), `results-extension-v1.md` (the extension) |
| `docs/thesis/results/<run>/` | CSV result tables per run (`explore_v1`, `explore_v2_ncal96`, `holdout_ncal48`, `holdout_ncal96`, `diag_instant_h12`, `diag_instant_h12_holdout`, `confirm13`); S1-S4 under `robust/`; S6 and S7 in `extra_descriptive/` (code `scripts/thesis/extra_descriptive.py`); extension: `holdout2_ncal48`, `holdout2_ncal96`, `ext_design13`, `ext_holdout1` (per-base-model analyses in `ce_<model>/`) and `extension_accuracy/` (code `scripts/thesis/extension_accuracy.py`) |
| `scripts/thesis/*.mjs` | Data download (IMF through DBnomics and the SDMX API), the shock rule, the validity checks; `fetch_holdout2.mjs` holds the candidate list and the rule of the second panel |
| `scripts/thesis/data/` | `snapshot.json`, `confirmatory.json`, `holdout.json`, `holdout2.json` |
| `scripts/thesis/exp/` | The engine: `data.py`, `forecasters.py` (including the Chronos forecaster), `intervals.py`, `evaluate.py`, `calibration.py`, `power.py`, `robust.py`, `run.py`, and `tests/` |
| `scripts/thesis/llm_eval/`, `backend/fastapi_service/app/services/inflation_explainer.py` | The language-model explainer, the prompt generator, the evaluation harness and a deterministic fake client, with tests |
| `scripts/thesis/repro_dracp.py` | Partial reproduction of the DRACP one-step setting through the public API of `dracp` 0.2.0 |
| `backend/fastapi_service/app/services/inflation_calibration.py` | Platform service |

**Environment.** Python 3.12 virtual environment under `scripts/thesis/.venv` with pandas, numpy, scipy, statsmodels, scikit-learn, LightGBM and the `dracp` package (0.2.0 in the reproduction check). The machine default was Python 3.14 with only numpy, and the package lists Python 3.10 to 3.12.

**Commands** (run from `scripts/thesis`, with the venv interpreter `.venv/Scripts/python.exe`).

- Tests: `-m pytest exp/tests -q`. The test modules cover data and chaining, the absence of look-ahead in forecasters, the timing of delayed and instant feedback, the equivalence of the independent ACI implementation with the package at h=1, calibration-error contrasts, Holm, TOST, the power simulation, the hold-out loader, the robustness analyses, the Chronos forecaster with its leakage flag and the reading of results files (the country code NA). The suite in `scripts/thesis/exp` has 81 tests, and the tests of the LLM layer (service and harness) have 18 (31 together with the 13 platform-service tests).
- Exploratory run v1 (code commit `2229076`): `-m exp.run full --start 2000-01 --end 2025-06 --out explore_v1 --resume`.
- Sensitivity run at warm-up 96 on the design countries: `-m exp.run full --start 2000-01 --end 2025-06 --n-cal 96 --out explore_v2_ncal96` [VERIFY: inferred from the run name and options, not copied from a document].
- Hold-out runs (all with `--holdout --start 2000-01 --end 2026-06`): (A) `--out holdout_ncal48`; (B) `--n-cal 96 --out holdout_ncal96`; (C) `--instant-feedback --horizons 12 --models lgbm --conformal-models lgbm --out diag_instant_h12_holdout`.
- Instant-feedback diagnostic on the design countries: `diag_instant_h12` [VERIFY: command not recorded in the documents; presumably the analogue of (C) without `--holdout`].
- Supplementary run: `--start 2000-01 --out confirm13` (degenerate: blocks of 12 months on at most 16 months; not used for any claim).
- Calibration-error contrasts: `-m exp.run ce --in results/<run> --out results/<run> --sample exploratory|holdout [--window-mde]`.
- Robustness analyses: `-m exp.run robust --in results/holdout_ncal48 --sample holdout --instant results/diag_instant_h12_holdout`.
- Extension, second hold-out panel (code commit `ca43ddc`): `-m exp.run full --holdout2 --start 2010-01 --models naive_b,arima,lgbm,chronos --conformal-models naive_b,arima,lgbm,chronos --out holdout2_ncal48`, and the same with `--n-cal 96 --out holdout2_ncal96` [VERIFY: reconstructed from the command-line options of `exp.run` and the run names; the exact command lines are not recorded in the documents].
- Extension, earlier 20 countries re-run from 2010-01 (the four base models were run; calibration contrasts were analysed only for LightGBM and Chronos): `-m exp.run full --start 2010-01 --out ext_design13` and the same with `--holdout --out ext_holdout1` [VERIFY: the model options of the exact command lines are not recorded in the documents; the result files contain the four base models].
- Extension, calibration-error analysis per base model: `-m exp.run ce --in results/holdout2_ncal48 --out results/holdout2_ncal48/ce_<model> --model <model> --sample holdout2` [VERIFY: same status]. Clean-month accuracy of Chronos: `scripts/thesis/extension_accuracy.py` [VERIFY: arguments].
- Language-model explainer (from `backend/fastapi_service`, interpreter `.venv-thesis-check/Scripts/python.exe`; `scripts/thesis/llm_eval/README.md`): `python ../../scripts/thesis/llm_eval/generate_prompts.py --out prompts.csv`; `python ../../scripts/thesis/llm_eval/run_eval.py --client fake --fake-mode faithful --out OUT` (harness check only, not a result); `python -m pytest tests/test_inflation_explainer.py ../../scripts/thesis/llm_eval/tests`. The real run, `run_eval.py --client openrouter --yes-spend --out OUT_REAL`, needs `OPENROUTER_API_KEY` (or `GROQ_API_KEY`) and makes 936 calls; it has not been run.

**Hashes and commits.** The data hashes are in Appendix B. Commits: shock rule frozen `58871dc`; exploratory code `2229076`; hold-out specification and rules `1480604`; fourth protocol entry `0ff08d8`; robustness specification `552fa67`; robustness results `de93501`; post hoc additions S6 and S7 specified `30d488c`; eighth entry (the extension specified before any computation) `dfe0b2c`; explainer and its evaluation harness `29532e7` (git log); Chronos forecaster, leakage flag and loading of the second panel `ca43ddc`; extension results `accd674`. The Chronos model is `amazon/chronos-bolt-tiny`, used zero-shot; the package version is not recorded in the documents read [VERIFY]. The shock rule document is dated 2026-11-18; the first commit that contains it is `58871dc`.

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

Outcome: R1 not met in the primary run (met at warm-up 96, a sensitivity run, not promoted); R2 not shown; R3 inconclusive; R4 not met (+2.4 pp against 3 pp); R5 all four primary contrasts inconclusive. These outcomes are those of the first hold-out panel. The extension rules E1-E5 are given in Section 5.6 and their outcomes on the second hold-out panel in Section 6.11 (Table 16).

## Appendix B. Data snapshots and hashes

| File | Content | SHA-256 |
|---|---|---|
| `scripts/thesis/data/snapshot.json` | IMF CPI, FX per USD and Brent, 13 design countries, via DBnomics (indexed 2025-08-31) | `d01b8360c4167f0b3d829f3d7af0438c36fe858c9f2e2745e9b258039cc2d739` |
| `scripts/thesis/data/confirmatory.json` | CPI, FX and Brent from 2024-01, IMF SDMX API, written by `fetch_confirmatory.mjs` | `e2001e5aad677567a7d572a6cf1d22929b18bfe1d3c1ad94bff47b75a3981a74` |
| `scripts/thesis/data/holdout.json` | CPI and FX of BO, PY, UY, GH, GE, KG, AO, written by `fetch_holdout.mjs` | `0245eab6c75d6bd7fe800fe5978a7ca5670550dff4b3f23e817177f9c6fae9ac` |
| `scripts/thesis/data/holdout2.json` | CPI and FX of ZM, AM, TZ, UG, KE, IQ, BW, NA, MZ, CI (198 months from 2010-01), written by `fetch_holdout2.mjs` (candidate list and rule fixed there before any forecast) | `72bcfee645ef3c5f89a67763278a3ee8ee2a74523e38a26739b16726c8947c75` |

Notes. Brent in the direct IMF API needs the area code `G001`. The overlap of the first two snapshots (2024-01 to 2025-05) is identical for FX, Brent and CPI except for the rebasing of the index level of KZ (0.477) and NG (0.131), small revisions for RU (up to 0.07 percent) and MN (up to 0.05 percent), and the Nigerian methodology break at 2025-01 (the index falls from 113.9 to 110.7 in rebased terms; growth between 2024-12 and 2025-01 is excluded). The IMF also publishes dated CPI vintages (`CPI_2026_JAN/FEB/APR/MAY_VINTAGE`), which were not used.

## Appendix C. Change log summary

| Date | Document | Change | Before which result |
|---|---|---|---|
| 2026-11-18 (date in the document; first commit `58871dc`) | `shock-definition.md` | Rule A frozen (threshold 3, window 3, 60-month lookback, floor 0.005) | Any forecast |
| 2026-11-19 | `shock-definition.md` | Validity checks logged; label timing defined; stress made secondary; confirmatory evaluation planned | Any forecast |
| 2026-11-19 | `experiment-protocol.md`, entry 1 | After committee review 5.5/10: claim hierarchy, confirmatory limited to h = 1, 3, 6, second snapshot, FACI and PID, DRACP tolerance and fallback, two naive baselines, block length at least h, primary tests at h=3 and 6, MDE threshold | Any forecast |
| 2026-11-19 | entry 2 | Second snapshot checked; confirmatory restricted to the pooled panel; Nigerian break; topic fixed | Any forecast |
| 2026-11-19 | entry 3 | Engine decisions (start 2000-01, 60 months of history, warm-up 48, window 120, step 0.02, LightGBM primary, chaining fix); first run exploratory only | Any full run |
| 2026-11-19 | entry 4 (`0ff08d8`) | CE replaces pooled coverage; reference becomes rolling; TOST for DRACP against ACI with 2 pp margin; warm-up 96 sensitivity; 7 hold-out countries; block length at least 12; stress stays exploratory; allowed DRACP wording | Hold-out forecasts (after exploratory v1) |
| 2026-11-19 | entry 5 (`1480604`) | Hold-out runs A, B, C specified; R1-R5 fixed | Hold-out run |
| 2026-11-19 | entry 6 (`552fa67`) | Robustness S1-S5 written down | Their computation (after the hold-out result) |
| 2026-11-19 | entry 7 (`30d488c`, post hoc) | S6 (Kazakhstan alone) and S7 (native intervals) written down after the manuscript review | Their computation (after the hold-out result and S1-S4) |
| 2026-11-19 | entry 8 (`dfe0b2c`) | Extension specified: second hold-out panel (10 countries, `holdout2.json`), Chronos zero-shot forecaster with leakage flag, rules E1-E5, evaluation of the language-model explainer (468 prompts, two conditions) | Any forecast for the second panel; any explainer request |
| 2026-11-19 | code `29532e7`, `ca43ddc` | Explainer and harness with fake client; Chronos forecaster, leakage flag, loading of the second panel | Extension results |
| 2026-11-19 | results `accd674` (`results-extension-v1.md`) | Extension results; CSV reader fixed for the country code NA (forecasts not affected, analysis step repeated) | - |
| 2026-11-19 | `topic.md` | Contribution text revised to match the hold-out result | - |

Commits: `58871dc` (shock rule), `810a60c` (protocol draft), `2229076` (engine and first run), `bf78f53` (exploratory results), `0ff08d8` (fourth entry, amendments), `1480604` (fifth entry, hold-out run specification and rules R1-R5), `46a2474` (hold-out results), `552fa67` (robustness specification), `c3c3c0f` (topic alignment), `de93501` (robustness results), `30d488c` (seventh entry, post hoc S6 and S7 specified before computing), `dfe0b2c` (eighth entry, extension specified before any computation), `29532e7` (explainer and harness), `ca43ddc` (Chronos, leakage flag, second panel loading), `accd674` (extension results).
