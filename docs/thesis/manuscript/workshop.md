# Calibrating Prediction Intervals for Inflation Forecasts in Commodity-Dependent Economies: A Multi-Horizon Panel Benchmark of Conformal Methods, with Kazakhstan as a Case Study

Short version for a workshop on conformal prediction and forecasting, or for arXiv. Draft 2026-11-19. Full text: `main.md`. Notes for the reviewer: `REVIEW_NOTES.md`.

---

## Abstract

Prediction intervals for inflation are used for decisions in commodity-dependent economies, but it is not known whether adaptive conformal methods that perform well on euro-area and US data keep their nominal coverage there. We build a multi-horizon (1, 3, 6 and 12 months) calibration benchmark of split, rolling-window, adaptive (ACI, FACI), conformal PID and regime-aware (DRACP) intervals at nominal level 0.90, using monthly IMF consumer price indices for 13 design economies and 7 hold-out economies selected by a fixed data-availability rule. The primary outcome is the calibration error (CE), the mean over countries of |coverage - 0.90|. Contrasts are tested with a moving-block bootstrap and Holm correction, equivalence of DRACP and ACI with two one-sided tests and a 2 percentage-point margin, and decision rules R1-R5 were pre-specified in a version-controlled protocol before the hold-out run (a self-attested commit history; the rules were written after the exploratory results were known). Adaptive methods were better calibrated than a calibration performed once and than the native intervals of the forecasting model, and the direction is consistent in both samples. The registered rule R1 was met only at a 96-month warm-up, a sensitivity run that is not promoted, and not at the primary 48-month warm-up (ACI minus split at h=3: -3.0 pp, p=0.054; at h=6: -2.8 pp, p=0.092; Holm-adjusted 0.108 at both horizons). An advantage of ACI over a rolling window was not shown (Holm p 0.35 and 1.0), no efficiency advantage is established, and DRACP against ACI is inconclusive; because the 2 pp equivalence margin is about the size of ACI's own calibration error, the equivalence verdict is weak by construction. At h=12 pooled coverage is below nominal for every method (0.83 to 0.88 on the hold-out panel), and releasing outcomes immediately raised ACI coverage by 2.4 pp (95% CI -0.1 to 4.8), below the pre-specified 3 pp threshold. In a secondary, post hoc analysis without multiplicity correction, ACI with an ARIMA base model had a lower calibration error than the native ARIMA intervals at every horizon in both samples (-3.3 to -6.4 pp); on the hold-out panel the interval includes zero at h=6 and h=12. The hold-out countries are untouched only with respect to countries.

---

## 1 Introduction

A forecast of inflation is useful for decisions only together with a statement of its uncertainty, and a prediction interval with a nominal level of 90 percent claims that about nine realised values in ten fall inside it. Whether this holds is a question of calibration that can be checked against realised data; it is not guaranteed by the forecasting model, whose error distribution is estimated from a past that may not resemble the future. Commodity-dependent economies are a demanding setting, because their price levels are exposed to exchange-rate and commodity-price movements and their inflation regimes can change within a few years [CITATION NEEDED: empirical evidence on the volatility and regime changes of inflation in commodity-dependent economies].

Conformal prediction (Vovk, Gammerman and Shafer, 2005) gives finite-sample coverage under exchangeability, which time series violate. Adaptive conformal methods (Gibbs and Candes, 2021, 2024; Angelopoulos, Candes and Tibshirani, 2023; Bhatnagar et al., 2023) were designed for that case, and a recent regime-aware variant, DRACP (Oancea, 2026), reports gains on euro-area inflation. Whether such results transfer to commodity-dependent economies and to multi-month horizons has not been tested to our knowledge [CITATION NEEDED: no systematic literature search was run].

This is a transfer and benchmark study and not a new method. We evaluate six interval methods on top of point forecasts of the cumulative h-month log growth of the consumer price index, with outcome feedback delayed by h months as in real use. The panel has 13 economies used to design the study and 7 hold-out economies for which no forecast existed before the pre-specified hold-out run. We report outcomes exactly as the pre-specified rules classify them; most are null or inconclusive, and a null outcome is not evidence of equality.

Contributions: (1) a calibration benchmark on 20 economies with calibration error, interval score, width and power-aware inference; (2) evidence that adaptive methods are better calibrated than a calibration performed once and than native model intervals, with a consistent direction in both samples and with the registered rule R1 met only at the sensitivity warm-up; (3) a feedback-delay diagnostic; (4) an open pipeline with hashed data snapshots, tests and a committed protocol.

---

## 2 Related work

Conformal prediction turns a point predictor into a prediction set with finite-sample coverage under exchangeability (Vovk, Gammerman and Shafer, 2005). Beyond exchangeability, Barber et al. (2023) bound the coverage gap using weights, Xu and Xie (2021) build intervals for dynamic time series, and Zaffran et al. (2022) study adaptive conformal predictions and the role of the learning rate. ACI (Gibbs and Candes, 2021) updates the working miscoverage level online by a step size times the difference between the target and the realised miss indicator, so that the long-run miss frequency approaches the target. FACI (Gibbs and Candes, 2024) aggregates several step sizes, conformal PID control (Angelopoulos, Candes and Tibshirani, 2023) combines proportional, integral and forecasting components, and SAOCP (Bhatnagar et al., 2023) uses strongly adaptive online learning. These guarantees concern long-run miss frequency and are not stated for outcomes that arrive h months late.

DRACP, as described by its authors (Oancea, 2026, arXiv:2608.17079v2), keeps the split-conformal radius but replaces the equal weights on past errors by a weighted quantile. The weight is a product of four factors: temporal decay, a density-ratio correction for covariate shift, an effective-sample-size-floored Gaussian kernel and a regime-similarity term from a Gaussian mixture model; an online controller adjusts the significance level from realised coverage, aggregating adaptive-conformal experts over several learning rates. It is evaluated on 48 macroeconomic and financial series (28 HICP inflation series of the euro area and EU member states, 13 US macro and energy series, 7 daily financial series) against split, rolling, ACI, FACI, SAOCP and conformal PID, mainly at one step, with an additional multi-horizon evaluation (h=3, 6, 12; direct forecasts; delayed feedback). The authors state that the advantage is specific to one-step-ahead forecasting and depends on the point forecaster [VERIFY against the paper]. Our study is a transfer of this method to a different panel and does not test their one-step claim. We found no systematic literature on the calibration of inflation intervals in emerging markets and cite none [CITATION NEEDED].

---

## 3 Data and setting

Monthly consumer price indices (all items) are from the IMF (series `M.<country>.PCPI_IX`); the exchange rate (domestic currency per US dollar, IMF IFS) and the Brent price (IMF primary commodity prices) are features of the LightGBM forecaster. The target is y(t, h) = 100 ln(CPI(t+h) / CPI(t)) for horizons h in {1, 3, 6, 12}, which is invariant to the index base.

**Design countries (13):** BR, MX, CL, CO, PE, ZA, ID, KZ, RU, AZ, UZ, NG, MN; they were used to shape the design (contrasts, horizons, warm-up). **Hold-out countries (7):** BO, PY, UY, GH, GE, KG, AO. They were fixed by a written data-availability rule (at least 220 months of IMF monthly CPI and exchange rate within 2000-01 to 2026-06, at most 3 missing CPI months, in a fixed candidate order); 7 of 14 candidates qualified and the rule was not relaxed. Target months of the hold-out panel run from 2009-02 to 2026-06. No export-share criterion for "commodity-dependent" was applied, and Georgia and Uruguay are borderline. The hold-out countries are independent of the design sample by country only: they share calendar months with it, including the global shocks of 2020 to 2022. Data snapshots are dated and hashed (SHA-256; see the repository). Nigeria's series ends at 2024-12 because of a methodology break, and Russia enters only through stretches of at least 60 consecutive months.

---

## 4 Methods

**Point forecasts and intervals.** Forecasts are made at one origin per month on an expanding window using only data dated at or before the origin. The primary base model is LightGBM (Ke et al., 2017), a direct forecast with fixed hyperparameters (200 trees, learning rate 0.05, 8 leaves); ARIMA and naive B serve as other base models in a robustness analysis. Six methods are run on the same point forecasts through the released `dracp` package: split conformal (quantile of absolute residuals on the warm-up, never updated); rolling conformal (most recent 120 residuals); ACI (step 0.02, window 120); FACI and conformal PID with package defaults; and DRACP with the configuration of the reproduction script (calibration window 120, temporal decay 0.985, 3 regimes). The nominal level is 0.90. The primary warm-up is 48 residuals; a warm-up of 96 is a sensitivity run applied to all methods and is not promoted to the primary result.

**Delayed feedback.** For an h-step forecast made at origin j, the outcome is observed at month j+h. At origin k the update for origin j is applied only if j+h <= k, and the interval actually issued is the one scored. A diagnostic option releases each outcome at origin + 1; it is not a valid forecasting setup and isolates the effect of delay.

**Calibration error.** For unit u and method m, CE(u, m) = |cov(u, m) - 0.90|, and a contrast between methods m1 and m2 is T = mean over units of [CE(u, m1) - CE(u, m2)]; a negative T means m1 is better calibrated. CE is used instead of pooled coverage because opposite deviations of different countries cancel in a pooled average. The interval (Winkler, 1972) score is W = (u - l) + (2/alpha) max(l - y, 0) + (2/alpha) max(y - u, 0), with alpha = 0.10; lower is better (see also Gneiting and Raftery, 2007).

**Inference.** Origin calendar months are resampled in moving blocks (Kunsch, 1989) of length max(h, 12), jointly across units, with 2000 replicates; we report the estimate, a 95 percent percentile interval and a two-sided centred bootstrap p-value. The primary family has four tests (ACI minus rolling and DRACP minus ACI, each at h=3 and h=6, LightGBM base), controlled by Holm's procedure (Holm, 1979). ACI minus split is a secondary contrast outside the family. DRACP against ACI is also tested for equivalence with two one-sided tests (Schuirmann, 1987) and a margin of 2 pp of CE; equivalence is declared if the larger one-sided p-value is below 0.05, otherwise the verdict is "not shown". The minimum detectable difference (MDE) is simulated by keeping the observed hit pattern of the baseline and thinning or thickening the hits of the comparison method; a contrast with an undefined MDE or an MDE above 7 pp is inconclusive (rule R5).

**Pre-specified rules.** R1: ACI is better calibrated than split if ACI minus split is negative with Holm p < 0.05 at both h=3 and h=6. R2: "ACI improves on rolling" only if ACI minus rolling is negative with Holm p < 0.05, otherwise "not shown". R3: "no advantage, equivalent within 2 pp" only if equivalence holds at both warm-ups; "DRACP better" only if DRACP minus ACI is negative with Holm p < 0.05 at both; otherwise "inconclusive". R4: delayed feedback explains the h=12 shortfall if ACI coverage with instant feedback exceeds delayed by at least 3 pp on the hold-out panel. R5 as above. The rules were committed to the repository before the hold-out run, which is a self-attested commit history and not an external registry or an independent timestamp, and they were written after the exploratory results on the design countries were known. The commit history is in the repository.

---

## 5 Results

All results use LightGBM and level 0.90 unless stated otherwise. Unadjusted p-values outside the registered family are descriptive; the word "significant" is not used for them.

**Pooled coverage.** Table 1 gives pooled coverage on the hold-out panel at warm-up 48 (1163, 1135, 1093 and 1009 unit-months at h=1, 3, 6 and 12). Split conformal over-covers at short horizons (0.954, 0.932, 0.936), and the adaptive methods are closer to 0.90. At h=12 pooled coverage is below nominal for every method (0.833 to 0.884). The pooled bootstrap intervals are wide and for ACI, DRACP, rolling and split their upper limits (0.923, 0.901, 0.918, 0.919) do not exclude 0.90; in the exploratory sample the pooled bootstrap interval of ACI at h=12 is [0.797, 0.914].

**Table 1. Pooled coverage, hold-out, 7 countries, warm-up 48**

| Method | h=1 | h=3 | h=6 | h=12 |
|---|---|---|---|---|
| Split | 0.954 | 0.932 | 0.936 | 0.861 |
| Rolling | 0.924 | 0.918 | 0.921 | 0.872 |
| ACI | 0.914 | 0.907 | 0.908 | 0.884 |
| FACI | 0.919 | 0.910 | 0.897 | 0.835 |
| Conformal PID | 0.912 | 0.910 | 0.909 | 0.833 |
| DRACP | 0.917 | 0.904 | 0.894 | 0.865 |

**Rule outcomes.** Table 2 gives the outcome of each pre-specified rule. R1 was not met at the primary warm-up: ACI minus split was -3.0 pp (95% CI [-5.4, +0.5], p 0.054) at h=3 and -2.8 pp ([-3.9, +1.2], p 0.092) at h=6, Holm-adjusted 0.108 at both horizons. It was met at warm-up 96 (-4.1 pp, p 0.018, and -5.9 pp, p 0.0025; Holm 0.018 and 0.005), a sensitivity run that is not promoted. The direction replicates in the exploratory data (-4.6 pp at h=3 and -3.4 pp at h=6 at warm-up 48), for three base models, and after removing any single country (leave-one-out ranges -4.1 to -2.2 pp at h=3 and -3.5 to -2.1 pp at h=6 on the hold-out panel, no sign flips). The statement supported is therefore one of consistent direction and not of pre-specified confirmation, and at the primary warm-up the confidence intervals include zero. ACI minus rolling was -1.6 pp (95% CI [-3.0, +0.5], Holm p 0.35) at h=3 and -0.7 pp ([-2.8, +1.3], Holm p 1.0) at h=6: not shown. On the Winkler score ACI was 1.0 percent lower than rolling at h=3 (95% CI [-7.1, +4.1]) and 5.3 percent higher at h=6 (95% CI [+1.4, +8.1], unadjusted p 0.005; descriptive). DRACP minus ACI was -0.1 pp and -0.3 pp at warm-up 48, with equivalence within 2 pp shown (TOST p 0.0005 and 0.047) and not shown at warm-up 96 (0.062 and 0.355). The minimum detectable difference is undefined on the full hold-out sample, so all four primary contrasts are inconclusive.

**Table 2. Outcomes of the pre-specified rules (hold-out, LightGBM)**

| Rule | Outcome | Evidence |
|---|---|---|
| R1 | Not met at warm-up 48; met at warm-up 96 (sensitivity, not promoted) | -3.0 pp (p 0.054), -2.8 pp (p 0.092), Holm 0.108 at 48; -4.1 pp (p 0.018), -5.9 pp (p 0.0025) at 96 |
| R2 | Not shown | Holm p 0.35 and 1.0 at 48; 0.59 and 0.99 at 96 |
| R3 | Inconclusive | TOST p 0.0005 and 0.047 at 48; 0.062 and 0.355 at 96 |
| R4 | Not met | +2.4 pp against the 3 pp threshold |
| R5 | All four primary contrasts inconclusive | MDE undefined on the full hold-out sample |

**Width and efficiency.** Three statistics should be kept apart. At h=1 and h=3, ACI, DRACP and FACI have a median interval width below that of rolling in both samples (median width ratio for ACI 0.91 and 0.93 in the exploratory data, 0.84 and 0.90 on the hold-out panel). The pooled mean width of ACI at h=3 is larger than rolling's in both samples (4.28 against 3.95 exploratory; 5.856 against 5.786 hold-out). The Winkler ratio to rolling for these methods at h=1 and h=3 is 0.94 to 0.99 on the hold-out panel and 0.99 to 1.16 in the exploratory data. No efficiency advantage is established.

**Native intervals (post hoc, secondary).** Table 3 compares ACI with an ARIMA base model against the native ARIMA intervals, with the calibration error of the native ETS intervals for reference. The analysis was written into the protocol before it was computed but is post hoc; p-values are unadjusted and there is no multiplicity correction. ACI had a lower CE than the native ARIMA intervals at every horizon in both samples, by 3.3 to 6.4 pp; on the hold-out panel the interval excludes zero at h=1 and h=3 and includes it at h=6 ([-4.4, +1.2]) and h=12 ([-4.9, +1.3]). Native ARIMA coverage looks acceptable on the hold-out panel (0.943, 0.930, 0.919, 0.885) because over-coverage in some countries offsets under-coverage in others.

**Table 3. Calibration error (CE) of native and ACI intervals, and the contrast ACI minus native (ARIMA base; pp)**

| Sample | h | ARIMA native CE | ARIMA with ACI CE | ETS native CE | ACI minus native (95% interval; unadjusted p) |
|---|---|---|---|---|---|
| Exploratory (13) | 1 | 0.047 | 0.010 | 0.044 | -3.7 [-4.6, -0.6]; 0.004 |
| Exploratory (13) | 3 | 0.066 | 0.015 | 0.051 | -5.1 [-6.2, -1.0]; 0.003 |
| Exploratory (13) | 6 | 0.089 | 0.026 | 0.064 | -6.4 [-7.7, -1.3]; 0.002 |
| Exploratory (13) | 12 | 0.137 | 0.079 | 0.116 | -5.8 [-7.8, -1.9]; 0.003 |
| Hold-out (7) | 1 | 0.053 | 0.014 | 0.056 | -3.9 [-4.5, -1.3]; below 0.001 |
| Hold-out (7) | 3 | 0.058 | 0.013 | 0.035 | -4.5 [-4.8, -0.6]; 0.010 |
| Hold-out (7) | 6 | 0.062 | 0.024 | 0.048 | -3.8 [-4.4, +1.2]; 0.082 |
| Hold-out (7) | 12 | 0.073 | 0.040 | 0.053 | -3.3 [-4.9, +1.3]; 0.100 |

**Delayed feedback at h=12 (S3).** Table 4 gives coverage with instant feedback minus coverage with delayed feedback, with a paired block-bootstrap 95 percent interval. R4 was not met for ACI: coverage was 0.884 with delayed and 0.908 with instant feedback on the hold-out panel, +2.4 pp with an interval that includes zero. The statement supported is that delay accounts for part of the shortfall, with a size that depends on the method and the sample; it is not shown that delay is, or is not, the main cause. The diagnostic is not a valid forecasting setup.

**Table 4. Change in h=12 coverage with instant feedback (pp; 95% interval)**

| Method | Exploratory (1738 cells) | Hold-out (1009 cells) |
|---|---|---|
| ACI | +4.1 [1.4, 7.8] | +2.4 [-0.1, 4.8] |
| DRACP | +4.3 [1.4, 7.5] | +3.9 [1.6, 6.5] |
| FACI | +8.3 [4.3, 13.6] | +6.4 [2.5, 9.6] |
| Conformal PID | +5.1 | +5.3 |
| Rolling | +1.3 | +1.3 |
| Split | 0 | 0 |

**Kazakhstan (post hoc, descriptive).** For Kazakhstan alone (one design-panel country, exploratory sample, 137 origins at h=1 and 133, 127 and 115 at h=3, 6 and 12, target months 2014-02 to 2025-06, no test) ACI and DRACP have coverage close to 0.90 up to h=6 (ACI 0.898, 0.902, 0.906; DRACP 0.905, 0.902, 0.906) and FACI as well (0.912, 0.910, 0.874), while rolling (0.825 at h=1), conformal PID (0.810) and split (0.730) under-cover at h=1. At h=12 every method is below nominal (0.713 to 0.835). With about 137 correlated origins the standard error of a coverage figure is roughly 3 pp, so only the larger gaps are clearly outside noise. The pattern is consistent with a regime change in 2015, but the data do not isolate that mechanism.

A stress analysis of coverage against exchange-rate shocks is secondary and exploratory, and the exchange-rate flag is a weak proxy of inflation shocks (see `main.md`).

---

## 6 Discussion and limitations

**What is supported.** Adaptive methods (ACI, FACI, conformal PID, DRACP) are better calibrated than a calibration performed once and than native model intervals, with a direction that is consistent across both samples, three base models and the removal of any single country. The registered rule R1 was met only at the sensitivity warm-up, and the evidence against native intervals is secondary and post hoc. At h=12 pooled coverage is below nominal for every method, and delayed feedback explains only part of it.

**What is not supported.** The data do not show that adaptivity helps beyond a rolling window, that DRACP is better than ACI, or that DRACP fails to transfer. None of the null outcomes is evidence of equality.

**The ceiling effect.** The calibration error of ACI is already small (0.013 and 0.014 at h=1 and h=3 in the exploratory data, 0.020 and 0.020 on the hold-out panel, about 1.5 to 2 pp), and the 2 pp equivalence margin is about the size of ACI's own calibration error. The equivalence verdict for DRACP against ACI is therefore weak by construction, and the contrasts against ACI cannot be powered: the simulated alternative cannot reduce CE below zero, so the improvement it can create is bounded by the baseline CE, and the MDE is undefined for all four primary contrasts. Null outcomes were likely before the run. The informative contrasts are those against weak references, split (CE 0.050 to 0.056 at h=1 to 6 on the hold-out panel) and native intervals. We read this as a limit of the design and not as a finding about the methods. DRACP also trains its regime and scale models on half of the warm-up (24 rows at warm-up 48), and its equivalence result depends on the warm-up; its authors report that its advantage is specific to one-step forecasts, which this design does not test.

**The procedural boundary.** The hold-out countries are independent of the design sample by country only. They share calendar months with it, the methods, contrasts and horizons were chosen on the design countries, and the author had seen the post-2025-06 months of the design countries before the amendments. The rules R1-R5 were written after the exploratory results were known, and the pre-specification is a self-attested commit history. The hold-out result is therefore a test on new countries and not a blind test of the design. The run on the post-2025-06 months of the design countries is degenerate (blocks of 12 months on at most 16 months) and is not used for any claim.

**Other limitations.** The hold-out panel has 7 countries, two of which (Ghana and Angola) have high-inflation episodes. "Commodity-dependent" is not defined by a measurable criterion, and the hold-out set was determined by data availability. LightGBM carries the registered contrasts; ARIMA and naive B give the same direction but were not part of the decision rules. The validity of the CE bootstrap at the boundary of the absolute value was not checked by simulation, so the size of the test is unknown. CPI vintages and data revisions were not checked. Our reproduction of the one-step DRACP setting was partial (ACI 0.874 and DRACP 0.871 on 5 countries with one seed). The S6 and S7 additions are post hoc and uncorrected for multiplicity. Intervals are for cumulative log growth; point forecasts were simple and not optimised.

---

## 7 Reproducibility

The code, the tests, the protocol with its dated change log, the dated and hashed data snapshots and the result tables are in the project repository (`docs/thesis/` and `scripts/thesis/exp/`, branch `thesis/inflation-calibration`); the commit history of the pre-specification is described in `main.md` Section 5. The engine needs a Python 3.12 environment with the `dracp` package (0.2.0 in the reproduction check) and runs with `-m exp.run`; the tests are run with `-m pytest exp/tests -q`.

---

## References

Details marked [VERIFY] must be checked against the publisher or arXiv record before submission.

Angelopoulos, A. N., Candes, E. J. and Tibshirani, R. J. (2023). Conformal PID control for time series prediction. *Advances in Neural Information Processing Systems (NeurIPS) 36*. [VERIFY volume and pages]
Barber, R. F., Candes, E. J., Ramdas, A. and Tibshirani, R. J. (2023). Conformal prediction beyond exchangeability. *The Annals of Statistics*, 51(2), 816-845. [VERIFY issue and pages]
Bhatnagar, A., Wang, H., Xiong, C. and Bai, Y. (2023). Improved online conformal prediction via strongly adaptive online learning. *Proceedings of the 40th International Conference on Machine Learning (ICML)*, PMLR 202. [VERIFY pages]
Gibbs, I. and Candes, E. J. (2021). Adaptive conformal inference under distribution shift. *Advances in Neural Information Processing Systems (NeurIPS) 34*. [VERIFY pages]
Gibbs, I. and Candes, E. J. (2024). Conformal inference for online prediction with arbitrary distribution shifts. *Journal of Machine Learning Research*, 25. [VERIFY article number and pages]
Gneiting, T. and Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation. *Journal of the American Statistical Association*, 102(477), 359-378. [VERIFY pages]
Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics*, 6(2), 65-70.
Hyndman, R. J., Koehler, A. B., Snyder, R. D. and Grose, S. (2002). A state space framework for automatic forecasting using exponential smoothing methods. *International Journal of Forecasting*, 18(3), 439-454. [VERIFY pages]
Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q. and Liu, T.-Y. (2017). LightGBM: A highly efficient gradient boosting decision tree. *Advances in Neural Information Processing Systems (NeurIPS) 30*. [VERIFY author list and pages]
Kunsch, H. R. (1989). The jackknife and the bootstrap for general stationary observations. *The Annals of Statistics*, 17(3), 1217-1241. [VERIFY pages]
Oancea, B. (2026). Dynamic Regime-Aware Conformal Calibration for Reliable Economic Forecast Intervals under Multiple Distribution Shifts. arXiv:2608.17079. [VERIFY author's first name or initial, version and submission date; the reported results are quoted only as recorded in `docs/thesis/experiment-protocol.md`, and the description of the method in `main.md` Section 2.3 is as described by the authors, read from the HTML version of version 2 and to be checked against the paper]
Schuirmann, D. J. (1987). A comparison of the two one-sided tests procedure and the power approach for assessing the equivalence of average bioavailability. *Journal of Pharmacokinetics and Biopharmaceutics*, 15(6), 657-680. [VERIFY pages]
Vovk, V., Gammerman, A. and Shafer, G. (2005). *Algorithmic Learning in a Random World*. Springer, New York.
Winkler, R. L. (1972). A decision-theoretic approach to interval estimation. *Journal of the American Statistical Association*, 67(337), 187-191. [VERIFY pages]
Xu, C. and Xie, Y. (2021). Conformal prediction interval for dynamic time-series. *Proceedings of the 38th International Conference on Machine Learning (ICML)*, PMLR 139. [VERIFY pages]
Zaffran, M., Feron, O., Goude, Y., Josse, J. and Dieuleveut, A. (2022). Adaptive conformal predictions for time series. *Proceedings of the 39th International Conference on Machine Learning (ICML)*, PMLR 162. [VERIFY pages]
