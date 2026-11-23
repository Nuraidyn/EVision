# Review notes for `main.md` and `workshop.md` (not part of the paper)

The manuscripts were written only from the project documents and the result tables in `docs/thesis/results/`. No analysis was re-run. Before the text is used, the following should be checked.

## Numbers to re-check against the CSV tables (all in `docs/thesis/results/<run>/`)

1. CE contrasts, confidence intervals and p-values in Tables 3, 4 and 5: `calibration_contrasts.csv` and `calibration_tost.csv` in `explore_v1`, `explore_v2_ncal96`, `holdout_ncal48`, `holdout_ncal96`.
2. Pooled coverage in Tables 2 and 4 and the bootstrap limits quoted at h=12: `interval_summary.csv` (rows with `unit = ALL`, model `lgbm`; columns `cov_lo`, `cov_hi`).
3. Delayed-feedback differences in Table 7: `robust/s3_feedback_diff.csv` (rows `unit = ALL`).
4. S1, S2 and S4 (Tables 8 to 10b): `robust/s1_leave_one_out.csv`, `robust/s2_other_models.csv`, `robust/s4_compact.csv`.
5. Minimum detectable differences: `power_mde_ce.csv` and `power_mde_ce_windows15.csv`.
6. Winkler contrasts: `winkler_contrasts.csv` (including the warm-up 96 hold-out DRACP minus ACI value of -5.8 percent, CI [-14.2, +3.3], p 0.18, quoted in Section 7.2).
7. Mean widths quoted in Sections 6.4 and 7.2 (4.28 and 3.95 exploratory; 5.856 and 5.786 hold-out at warm-up 48; 6.11 and 6.31 hold-out at warm-up 96, DRACP and ACI): `interval_summary.csv`.
8. Post hoc additions: `results/extra_descriptive/s6_kazakhstan.csv`, `s7_native_ce.csv`, `s7_aci_vs_native_arima.csv` (Tables 11 to 13).

## Places where the source documents and the CSV tables differ in the last digit

The text follows the CSV in each case, with one exception noted last.

- R1 at warm-up 96, h=3: `results-holdout-v1.md` gives -4.2 pp in an earlier version; the CSV gives -0.04150, which is -4.1 pp.
- R1 at warm-up 48, h=6: p 0.0925 in the CSV, written 0.092.
- FACI, instant minus delayed feedback, hold-out: `results-holdout-v1.md` gives +6.5 pp; the CSV and the robustness document give +6.4 pp (0.0644).
- DRACP, S3, hold-out, upper limit: the CSV value is 0.0645, at the rounding boundary; the manuscripts write 6.5 as in `results-robustness-v1.md`.
- Hold-out DRACP minus ACI at h=3 (LightGBM): CSV -0.149 pp, written -0.1 in Tables 5 and 9 (the robustness document writes -0.2).
- Hold-out ACI minus rolling at h=3, p: CSV 0.08746, written 0.087 everywhere (the robustness document writes 0.088).
- Exploratory ACI minus rolling at h=6, p: CSV 0.01949. By instruction it is written 0.020 everywhere; strict rounding to three decimals would give 0.019. Decide once and apply to both documents.
- Table 10, DRACP at h=3, Winkler ratio: CSV 0.9649, written 0.96 (the robustness document writes 0.97).
- The p-values reported for R1 in the results documents are unadjusted bootstrap p-values (the secondary contrast has no Holm column in the CSV), although R1 is written with "Holm p". Holm over the two horizons, as computed in `results-holdout-v1.md`, gives 0.108 at both horizons at warm-up 48, and 0.018 and 0.005 at warm-up 96; these Holm values come from that document and not from a CSV column.
- S2: the unadjusted ACI minus rolling p-values range from 0.016 to 0.48 (the robustness document says 0.22 as the upper end and should be corrected).

## Items marked [VERIFY] or [CITATION NEEDED]

- Section 2.3 (checked 2026-11-23): the description of DRACP was compared with the HTML version 2 of arXiv 2608.17079 (author Bogdan Oancea; v1 2026-08-17, v2 2026-10-19). Four points are recorded in Section 2.3 (no numeric hyperparameters in the paper; the paper's controller is a heuristic distinct from FACI; SAOCP has the best interval score; DRACP coverage falls with the horizon). Appendices other than B and C were not read.
- [VERIFY] The exact command lines of the runs `explore_v2_ncal96` and `diag_instant_h12` (Section 9).
- Bibliographic details in `references.md` were checked on 2026-11-23 against primary records (the record is named per entry). Unresolved: the 2005 publisher record of Vovk et al. (second edition 2022 confirmed), the TMLR page of Chronos (OpenReview did not load; venue confirmed through the model card, the repository BibTeX and a search result), and the JSTOR page of Holm (bibliographic data from search results).
- Section 1, commodity-dependent economies: Gelos and Ustyugova (2017) cited for the exposure of inflation to commodity price shocks; the statement that regimes change within a few years has no source and says so.
- Section 2.4: the Dallas Fed working paper is Duncan and Martinez-Garcia (WP 338, 2018; IJF 2019), about point forecasts. A limited search (2026-11-23) found conformal intervals for inflation in BRIC (Sengupta et al., 2025) and Tunisia (Brahem, 2026), which limits the novelty claim: it is now a coverage benchmark of several adaptive conformal methods, not conformal intervals for emerging-economy inflation as such.
- Section 4.2: AICc cited (Hurvich and Tsai, 1989); no source is cited for ARMA modelling.
- Novelty statement in Section 1: rewritten as "not found to our knowledge" after a limited, non-systematic search (Section 2.4).

Resolved in this revision: the commit of the fourth protocol entry is `0ff08d8` and that of the fifth entry is `1480604`; the shock rule document is dated 2026-11-18 and the first commit that contains it is `58871dc`.

## Wording rules kept in both manuscripts

- "Pre-specified", never "pre-registered" and never "independently timestamped": the history is self-attested, and R1-R5 were written after the exploratory results were known.
- "Significant" is not used for anything outside the registered family.
- "Not shown" is never turned into "no effect".
- Warm-up 96 is a sensitivity run and is not promoted.
- Narrower intervals: the median width ratio, the pooled mean width and the Winkler score are three statistics and are stated separately; no efficiency advantage is established.
- The advantage over one-shot calibration is stated as a consistent direction, not as a clear result: at warm-up 48 the confidence intervals include zero.
- At h=12: "pooled coverage is below nominal for every method", with the note that several pooled bootstrap intervals (ACI in the exploratory sample, [0.797, 0.914]) include 0.90.

## Procedural boundary to keep in view

Hold-out countries are untouched with respect to countries only; they share calendar months (2020 to 2022 shocks) with the design sample. The methods, contrasts and horizons were chosen on the 13 design countries. The author had seen the post-2025-06 months of the 13 countries before the amendments. The stress analysis, S1-S4, and the post hoc additions S6 and S7 are secondary. The run `confirm13` is degenerate and is not used.

## Open items

- Notify the author of DRACP before the text is posted (arXiv or a workshop). The study is a transfer study of a published method; it attributes to the author only the limitation that the authors themselves state (the advantage is specific to one-step-ahead forecasting and depends on the point forecaster), and it asks for a courtesy notice and for a check of the description in Section 2.3.
- The size of the CE bootstrap at the boundary of the absolute value was not checked by simulation (Section 8, item 9).
- Resolved in part: a measured post hoc criterion (UNCTAD 60%, 2021-2023) is now defined in the text; 27 of 30 qualify, Mexico, Indonesia and Georgia are kept as comparison cases, and the title is unchanged. Remaining caveats: the classification was applied after the panels were chosen and part of the shares had been read before it was written down; no dependent versus other comparison is possible (`results-commodity-v1.md`).
- The Kazakh abstract and the Russian abstract need a native-speaker check of terminology (see `abstracts.md`).
- `results-robustness-v1.md` should be corrected for the S2 p-value range (0.016 to 0.48) and for the roundings listed above, so that the documents agree.
- The `workshop.md` version omits the commit history, the stress validity analysis and the platform; keep it consistent with `main.md` if numbers change.

## Title proposals

The title in `main.md`, `workshop.md` and `abstracts.md` is unchanged:

- Current (EN): Evaluating Methods for Building Reliable Prediction Intervals for Machine-Learning Inflation Forecasts in Commodity-Dependent Economies.
- Proposal, to be adopted only once the extension is accepted by the supervisor or committee, adding the pretrained models:
  - RU: «Сравнение методов построения надёжных интервалов прогноза инфляции с помощью моделей машинного обучения и предобученных моделей временных рядов в странах, зависящих от сырья»
  - EN: Comparing Methods for Building Reliable Prediction Intervals for Machine-Learning and Foundation-Model Inflation Forecasts in Commodity-Dependent Economies

The author decides. The current titles in the three languages are kept in the files until then.

## Extension (eighth entry; results `accd674`): what to check

Numbers in the new sections 6.11 to 6.13 of `main.md` come from `results-extension-v1.md` and from the CSV tables in `docs/thesis/results/holdout2_ncal48`, `holdout2_ncal96`, `ext_design13`, `ext_holdout1` and `extension_accuracy`. Where the two differ, the text follows the CSV:

- `results-extension-v1.md` contains stray fragments ("0.737|") in the Chronos rows of the E1 CE table and of the Chronos accuracy table, which shift the columns. They were resolved against the CSVs: Chronos CE at h=3 is ACI 0.034, DRACP 0.030, rolling 0.067, split 0.109; relative MAE over all months is 0.737, 0.586, 0.581, 0.934 (recomputed as the n-weighted pooled ratio from `point_metrics.csv`, which matches the other models' figures in the document). Fix the source document.
- Naive B, ACI minus rolling at h=6: the source document gives -3.5 pp; the CSV is -3.4465 pp, written -3.4.
- Chronos, ACI minus rolling at h=6: Holm p 0.0885 in the CSV, written 0.088 (the source document writes 0.089).
- Table 14 (CE at h=3 and h=6 for the four base models and the ARIMA native intervals) was computed from `interval_summary.csv` (mean over the 10 countries of |coverage - 0.90|); only the h=3 values are in `results-extension-v1.md` and they agree. The h=6 values are new and should be checked.
- Table 17 puts the R2 outcomes of all panels side by side. The Holm p-values of the re-runs from 2010-01 come from `ext_design13` and `ext_holdout1` (`calibration_contrasts.csv`); the source document states only the range 0.22 to 1.0.
- The pooled-month counts (89 and 83 at warm-up 48; 41 and 35 at 96) and the minimum detectable differences are as in the source document and `power_mde_ce.csv`.
- On the earlier 20 countries the four base models were run; calibration contrasts were analysed only for LightGBM and Chronos, which narrows the E-B analysis of the protocol (stated as a deviation in Section 5.6), so Table 17 has LightGBM and Chronos only for those panels. The MDE is undefined in every cell of those panels (`power_mde_ce.csv` of `ext_design13` and `ext_holdout1`), so their R2 results are inconclusive under E5 and not evidence of no effect.
- R2 on the second hold-out panel: met at h=3 for LightGBM, ARIMA and naive B (Holm 0.008, 0.004, 0.004) and at h=6 for ARIMA and naive B (0.030, 0.039); Chronos at h=3 (Holm 0.036) has an undefined MDE and is inconclusive under E5; Chronos and LightGBM at h=6 are not met (0.088, 0.159).
- R1 in Section 6.11: the direction replicates and the registered threshold is met on the second panel at warm-up 48; on the first hold-out panel it was met only at warm-up 96.
- E3 deviation: Table 18 (all months) has no bootstrap intervals and no ETS (ETS was not in the extension runs); the clean-month analysis in Table 19 has intervals against LightGBM, ARIMA and naive B. Stated in Section 5.6 and in the Table 18 note.

Remaining [VERIFY] and [CITATION NEEDED] items added by the extension:

- Chronos reference verified (2026-11-23); the model card states no pretraining cutoff, the repository gives the Chronos-Bolt release date 2024-11-26.
- [VERIFY] the exact command lines of the extension runs (Section 9); they are reconstructed from the options of `exp.run` and the run names.
- [VERIFY] the version of the `chronos` package (not looked up). The cutoff of `amazon/chronos-bolt-tiny` is not stated on the model card; 2025-01 stays a conservative assumption.
- Section 2.5: Jetwiriyanon et al. (2025) and Michael et al. (2026) added (abstracts only); no study of interval calibration of foundation models for inflation found.
- The test counts (81 in `scripts/thesis/exp`, 18 in the LLM layer: 4 in `test_inflation_explainer.py` and 14 in `llm_eval/tests`; 31 together with the 13 platform-service tests of `test_inflation_calibration.py`) are as given by the author and were not re-run here.

Wording rules for the extension, kept in all three files: "R2 met" is a statement about one panel at the primary warm-up; the conclusion about ACI against a rolling window is "depends on the panel"; the panels are not averaged and the favourable panel is not selected; warm-up 96 on the second panel "shows nothing"; Holm is applied within each base model and not across the four base models, which share countries and months; the language-model explainer result (936 answers, one model) is reported as pre-specified v1 and post hoc v2 side by side, with both metric defects, the single-reader (model, not human) validation, the unscored manual review and no claim that grounding works in general or that the model is faithful in general (status updated 2026-11-23; numbers from `docs/thesis/results-llm-eval-v1.md`).

Keep the Kazakh and Russian sentences about the extension for the native-speaker check (see `abstracts.md`).

## Explainer evaluation (2026-11-23): what to check

- Numbers in `main.md` Section 6.13, `workshop.md`, `abstracts.md` (EN/RU/KK), `paper/` and `paper_short/` all come from `docs/thesis/results-llm-eval-v1.md`: v1 grounded 90.6% / 9.0% / 23.3%, ungrounded 69.0% / 100% / 26.5%; v2 grounded 100% / 0% / 3.0%, ungrounded 69.0% / 100% / 13.0%; 145 of 156 ungrounded answers with numbers have an unmatched number; validation 56/60, 60/60, 52/60.
- The v2 validation was made by the model that wrote the analysis, knowing the flags; it is not an independent review. A human review of `manual_review_sample.csv` (90 rows) is still open, and Kazakh fluency needs a native speaker.
- The Kazakh abstract sentence on the explainer and the Russian one are new and need a native-speaker check.
- Ungrounded v2 overstatement (13.0%) is not informative (coverage-gap cases by construction plus list-item false alarms); do not present it as a finding.
