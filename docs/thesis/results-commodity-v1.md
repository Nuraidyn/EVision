# Commodity-dependence classification of the 30 countries (post hoc, descriptive), v1 (2026-11-23)

Status: **post hoc, descriptive**. Criterion fixed in the tenth entry of `experiment-protocol.md` before the classification was run. No forecast was recomputed; no hypothesis test is reported.

Reproduce: `scripts/thesis/.venv/Scripts/python.exe scripts/thesis/commodity_criterion.py` (offline; tests in `scripts/thesis/tests/test_commodity_criterion.py`). Tables: `results/commodity_criterion/`.

## Source and definition

- UNCTAD, The State of Commodity Dependence 2025 (UNCTAD/DITC/COM/2025/3), country profiles; https://unctad.org/system/files/official-document/ditccom2025d3_en.pdf; retrieved 2026-11-23; PDF sha256 e0799b129601d5c1dd5182cdc7110d2a313cd344a4d0ccad9b1573565a7c3122.
- Indicator: commodity exports as a share of all allocated product exports (UNCTAD definition of commodities: primary commodities incl. energy, ores, metals, precious stones and non-monetary gold), 3-year average. Primary window 2021-2023; second window 2012-2014. The average over each country's own sample is not available from this source and is not computed.
- Extraction check: the extracted profile table reproduces the report's headline counts exactly (103 dependent economies at 2021-2023, 106 at 2012-2014).
- Vintage: report of July 2025 on UNCTADstat data of November 2024, i.e. a pre-2026 vintage; the export structure of 2024-2025 is not covered. A machine-readable UNCTADstat table was not found; the numbers come from the PDF profile pages through `scripts/thesis/extract_unctad_profiles.py` (needs `pdftotext`).
- Class: share >= 60 strong (UNCTAD rule), 40-60 moderate, < 40 not. The report states the rule as 'more than 60'; no country has a share of exactly 60.0, so >= and > coincide.

## Classification

| country | name | panel | share_2021_2023 | class_2021_2023 | share_2012_2014 | class_2012_2014 |
|---|---|---|---|---|---|---|
| KZ | Kazakhstan | design13 | 83.5 | strong | 89.0 | strong |
| RU | Russian Federation (the) | design13 | 76.6 | strong | 83.9 | strong |
| AZ | Azerbaijan | design13 | 96.0 | strong | 97.9 | strong |
| UZ | Uzbekistan | design13 | 63.1 | strong | 72.9 | strong |
| CO | Colombia | design13 | 80.2 | strong | 83.4 | strong |
| CL | Chile | design13 | 83.5 | strong | 86.5 | strong |
| PE | Peru | design13 | 91.1 | strong | 87.4 | strong |
| BR | Brazil | design13 | 75.3 | strong | 66.7 | strong |
| MX | Mexico | design13 | 18.2 | not | 23.8 | not |
| NG | Nigeria | design13 | 96.3 | strong | 97.3 | strong |
| MN | Mongolia | design13 | 98.9 | strong | 97.5 | strong |
| ID | Indonesia | design13 | 55.9 | moderate | 62.4 | strong |
| ZA | South Africa | design13 | 63.9 | strong | 58.1 | moderate |
| BO | Bolivia (Plurinational State of) | holdout1 | 95.3 | strong | 95.4 | strong |
| PY | Paraguay | holdout1 | 85.6 | strong | 91.5 | strong |
| UY | Uruguay | holdout1 | 82.9 | strong | 77.2 | strong |
| GH | Ghana | holdout1 | 93.9 | strong | 92.8 | strong |
| GE | Georgia | holdout1 | 46.4 | moderate | 40.3 | moderate |
| KG | Kyrgyzstan | holdout1 | 74.7 | strong | 72.9 | strong |
| AO | Angola | holdout1 | 97.9 | strong | 98.0 | strong |
| ZM | Zambia | holdout2 | 89.7 | strong | 87.6 | strong |
| AM | Armenia | holdout2 | 69.8 | strong | 76.4 | strong |
| TZ | United Republic of Tanzania (the) | holdout2 | 89.8 | strong | 87.0 | strong |
| UG | Uganda | holdout2 | 80.6 | strong | 70.2 | strong |
| KE | Kenya | holdout2 | 69.6 | strong | 65.7 | strong |
| IQ | Iraq | holdout2 | 99.5 | strong | 99.8 | strong |
| BW | Botswana | holdout2 | 94.3 | strong | 94.4 | strong |
| NA | Namibia | holdout2 | 82.2 | strong | 76.8 | strong |
| MZ | Mozambique | holdout2 | 95.6 | strong | 93.2 | strong |
| CI | Côte d’Ivoire | holdout2 | 92.3 | strong | 87.4 | strong |

## Counts (primary window 2021-2023)

| panel | n | ge60 | ge40 | moderate | below40 | missing |
|---|---|---|---|---|---|---|
| design13 | 13 | 11 | 12 | 1 | 1 | 0 |
| holdout1 | 7 | 6 | 7 | 1 | 0 | 0 |
| holdout2 | 10 | 10 | 10 | 0 | 0 | 0 |
| all30 | 30 | 27 | 29 | 2 | 1 | 0 |

Second window 2012-2014:

| panel | n | ge60 | ge40 | moderate | below40 | missing |
|---|---|---|---|---|---|---|
| design13 | 13 | 11 | 12 | 1 | 1 | 0 |
| holdout1 | 7 | 6 | 7 | 1 | 0 | 0 |
| holdout2 | 10 | 10 | 10 | 0 | 0 | 0 |
| all30 | 30 | 27 | 29 | 2 | 1 | 0 |

Not qualifying at 60% (2021-2023): MX (18.2), ID (55.9), GE (46.4).

Countries whose class differs between the two windows: ID (strong -> moderate), ZA (moderate -> strong).

Missing in the source: none. Nothing is imputed.

## Descriptive cut of existing results (calibration error by class)

Source: committed `interval_summary.csv` of `explore_v1` (design 13, exploratory sample), `holdout_ncal48`, `holdout2_ncal48`; LightGBM base, warm-up 48, nominal 0.90. Cell = mean over countries of |coverage - 0.90| in percentage points (CE), with the number of countries n (qualify / not). `pooled30` = design exploratory + hold-out 1 + hold-out 2 (each country once). The design-panel confirmatory months (`confirm13`, at most 16 per unit) are in the CSV only. Nothing is tested: subsets of 1-9 countries with dependent errors have no power calculation here, the block bootstrap of `exp/calibration.py` tests contrasts between methods, not differences between subsets, and is not reused (E5/R5 rule: undefined power means inconclusive). Differences are descriptive and inconclusive; no 'no difference' conclusion is drawn.

### Qualify = share >= 60%

| Method | h | design13_exploratory: qualify / not | holdout1: qualify / not | holdout2: qualify / not | pooled30: qualify / not |
|---|---|---|---|---|---|
| split | 3 | 5.9 (n=11) / 6.6 (n=2) | 4.5 (n=6) / 7.9 (n=1) | 10.4 (n=10) / - | 7.3 (n=27) / 7.1 (n=3) |
| split | 6 | 7.2 (n=11) / 5.6 (n=2) | 5.0 (n=6) / 7.1 (n=1) | 12.5 (n=10) / - | 8.6 (n=27) / 6.1 (n=3) |
| rolling | 3 | 3.8 (n=11) / 2.5 (n=2) | 3.4 (n=6) / 5.2 (n=1) | 7.0 (n=10) / - | 4.9 (n=27) / 3.4 (n=3) |
| rolling | 6 | 4.9 (n=11) / 5.6 (n=2) | 2.8 (n=6) / 5.7 (n=1) | 8.0 (n=10) / - | 5.6 (n=27) / 5.6 (n=3) |
| aci | 3 | 1.6 (n=11) / 0.4 (n=2) | 2.0 (n=6) / 2.4 (n=1) | 3.3 (n=10) / - | 2.3 (n=27) / 1.1 (n=3) |
| aci | 6 | 3.5 (n=11) / 3.2 (n=2) | 2.3 (n=6) / 3.5 (n=1) | 4.5 (n=10) / - | 3.6 (n=27) / 3.3 (n=3) |
| dracp | 3 | 1.7 (n=11) / 0.9 (n=2) | 1.9 (n=6) / 1.7 (n=1) | 2.3 (n=10) / - | 2.0 (n=27) / 1.2 (n=3) |
| dracp | 6 | 3.7 (n=11) / 1.1 (n=2) | 2.2 (n=6) / 2.1 (n=1) | 3.2 (n=10) / - | 3.2 (n=27) / 1.4 (n=3) |

### Qualify = share >= 40%

| Method | h | design13_exploratory: qualify / not | holdout1: qualify / not | holdout2: qualify / not | pooled30: qualify / not |
|---|---|---|---|---|---|
| split | 3 | 6.2 (n=12) / 3.3 (n=1) | 5.0 (n=7) / - | 10.4 (n=10) / - | 7.4 (n=29) / 3.3 (n=1) |
| split | 6 | 7.4 (n=12) / 1.2 (n=1) | 5.3 (n=7) / - | 12.5 (n=10) / - | 8.6 (n=29) / 1.2 (n=1) |
| rolling | 3 | 3.9 (n=12) / 0.7 (n=1) | 3.6 (n=7) / - | 7.0 (n=10) / - | 4.9 (n=29) / 0.7 (n=1) |
| rolling | 6 | 5.2 (n=12) / 2.3 (n=1) | 3.2 (n=7) / - | 8.0 (n=10) / - | 5.7 (n=29) / 2.3 (n=1) |
| aci | 3 | 1.5 (n=12) / 0.2 (n=1) | 2.0 (n=7) / - | 3.3 (n=10) / - | 2.3 (n=29) / 0.2 (n=1) |
| aci | 6 | 3.6 (n=12) / 1.8 (n=1) | 2.5 (n=7) / - | 4.5 (n=10) / - | 3.7 (n=29) / 1.8 (n=1) |
| dracp | 3 | 1.7 (n=12) / 1.2 (n=1) | 1.9 (n=7) / - | 2.3 (n=10) / - | 1.9 (n=29) / 1.2 (n=1) |
| dracp | 6 | 3.4 (n=12) / 1.2 (n=1) | 2.2 (n=7) / - | 3.2 (n=10) / - | 3.1 (n=29) / 1.2 (n=1) |

Full table (all 7 methods, h = 1, 3, 6, 12, mean coverage, confirmatory design months): `results/commodity_criterion/ce_by_class.csv`.

## What the classification means for the title and the claims

Facts (primary window 2021-2023, UNCTAD indicator, threshold fixed in the tenth protocol entry):

- 27 of 30 countries qualify at 60% (design 11 of 13, hold-out 1 6 of 7, hold-out 2 10 of 10); 29 of 30
  qualify at 40%. Three do not reach 60%: **Mexico (18.2%, below 40%, a manufacturing exporter)**,
  **Indonesia (55.9%, moderate; it was 62.4% in 2012-2014 and UNCTAD itself reports that it left the
  dependent group)** and **Georgia (46.4%, moderate; 40.3% in 2012-2014)**. South Africa (63.9%) qualifies
  in 2021-2023 but not in 2012-2014 (58.1%), so it is a threshold case that flipped the other way. Uruguay
  (82.9%) is clearly strong, so it is not "borderline" by this measure, unlike what the manuscript says in
  Section 7.5.
- 3 of 30 (10%) fail at 60%, so the "more than a quarter" trigger for rewording is **not met**. All three
  failing countries are in the original design panel and the first hold-out, and the failure at 40% is
  one country (Mexico). The weakest part of the "commodity-dependent" label is the design panel (2 of 13
  fail at 60%, 15%) and, in particular, the platform text that calls all 13 of them commodity-dependent.
- The result describes the sample as drawn; it does not turn the selection into a measured design. The
  classification was written after the panel was fixed and after most results were known, it is
  descriptive and post hoc, and it uses a recent three-year window (and an older one) rather than each
  country's whole 2000-2026 history. The study still does not compare commodity-dependent with other
  economies; with 3 non-qualifying countries and no power calculation such a comparison is not possible.
- The descriptive cut of the committed results (tables above) shows no pattern that can be read from the
  1-3 non-qualifying countries per cell; it is inconclusive and supports neither "the results hold for
  both groups" nor "they differ".

Recommended wording (the decision is the user's; nothing below has been applied to any file):

1. Keep "commodity-dependent" in the title only if the text defines it by the measured criterion:
   "27 of the 30 economies (90%) had commodities above 60% of merchandise exports in 2021-2023 (UNCTAD);
   Mexico, Indonesia and Georgia did not, and are retained as comparison cases". This is the least
   invasive option.
2. Safer alternative that is accurate for all 30 without a caveat: replace "Commodity-Dependent
   Economies" by "Emerging and Commodity-Exporting Economies" (EN), "развивающихся и сырьевых
   экономиках" (RU), "дамушы және шикізат экспорттаушы экономикаларда" (KK, machine-drafted, needs a native speaker). Mexico is a commodity
   exporter in the weak sense only (its share is 18%), so even "commodity-exporting" needs the caveat
   "most of which".
3. In the platform README (`README.md:48`) and wherever the 13 design economies are described, do not
   write "13 commodity-dependent economies"; write "13 emerging economies, 11 of which are
   commodity-dependent by the UNCTAD 60% criterion".
4. In Section 7.5 and limitation 7 of the manuscript, replace "not defined by a measurable criterion" by
   the measured result above (the statement that no export-share rule was used to select the countries
   stays true and should be kept).

## Sentences that make the "commodity-dependent" claim (file:line, not edited)

| File:line | Sentence or fragment |
|---|---|
| `docs/thesis/topic.md:17` | Title (EN): "... Inflation Forecasts in Commodity-Dependent Economies" |
| `docs/thesis/topic.md:19` | "Do prediction intervals for monthly inflation in commodity-dependent economies keep their nominal coverage ..." |
| `docs/thesis/topic.md:41-42` | RU: "... интервалы прогноза месячной инфляции в сырьевых экономиках ..." (and the RU title just above) |
| `docs/thesis/topic.md:60,63` | KK title and question: "Шикізатқа тәуелді елдерде ..." and "Шикізатқа тәуелді экономикалардағы ..." |
| `README.md:48` | "Monthly inflation forecasts for 13 commodity-dependent economies ..." |
| `README.md:55` | Title of the thesis as in the topic ("... Commodity-Dependent Economies") |
| `docs/thesis/manuscript/main.md:1` | Title |
| `docs/thesis/manuscript/main.md:9` | Abstract: "Prediction intervals for inflation are used for decisions in commodity-dependent economies ..." |
| `docs/thesis/manuscript/main.md:15` | "Central banks, finance ministries and firms in commodity-dependent economies use inflation forecasts ..." |
| `docs/thesis/manuscript/main.md:17` | "Commodity-dependent economies are a demanding setting for calibration. ..." |
| `docs/thesis/manuscript/main.md:59` | "The literature on inflation forecasting in emerging and commodity-dependent economies is large ..." |
| `docs/thesis/manuscript/main.md:667` | "A practitioner who produces inflation intervals for a commodity-dependent economy should not ..." |
| `docs/thesis/manuscript/main.md:673-677,689` | Section 7.5 and limitation 7 ("not defined by a measurable criterion"; "Georgia and Uruguay are borderline") |
| `docs/thesis/manuscript/abstracts.md:3,11,17,23` | EN title, EN abstract, RU abstract ("сырьевых экономиках"), KK abstract ("шикізатқа тәуелді") |
| `docs/thesis/manuscript/workshop.md:1,9` | Title and abstract |
| `docs/thesis/manuscript/REVIEW_NOTES.md:36,61,71,74` | Notes that already flag the missing criterion and propose titles |
| `paper/main.tex:42` | `\title{... in Commodity-Dependent Economies}` (no other occurrence of the term in the body) |
| `paper_short/main.tex:36` | `\title{... in Commodity-Dependent Economies}` (same) |
