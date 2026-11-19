# Shock definition (frozen before any forecast is run)

Date fixed: 2026-11-18. Status: frozen by the author; any later change must be logged in
the "Changes" section below with a date and a reason, and all affected results re-run.

## Purpose

The thesis evaluates coverage of inflation forecast intervals separately in calm and shock
periods. A shock period must be defined independently of the inflation series being
forecast, using only information available at time t, so the split cannot be tuned to the
results.

## Primary rule (rule A)

Driver: monthly average exchange rate, domestic currency per US dollar
(IMF IFS, indicator `ENDA_XDC_USD_RATE`, via DBnomics `IMF/IFS/M.<country>.ENDA_XDC_USD_RATE`).

For each country and month t:

1. `d_t = ln(FX_t / FX_{t-1})`.
2. Over the 60 months before t (t excluded): `m` = median of `d`, `s` = max(1.4826 * MAD of `d`, 0.005).
3. `z_t = (d_t - m) / s`. Month t is a shock event if `|z_t| > 3`.
4. The shock window is the event month and the 3 following months. Overlapping or adjacent
   windows are merged into one episode.
5. Months outside any window are calm.

The first 60 months of each series are used only to estimate `m` and `s`; no events are
flagged there.

## Secondary driver

Brent crude, monthly, US dollars (IMF PCPS `M.W00.POILBRE.USD`), same rule. Reported as a
variant ("FX or Brent"); it is not used for the primary results.

## Robustness checks (reported alongside every primary result)

- Threshold 2.5 and 3.5 instead of 3.
- Window length 0 and 6 following months instead of 3.
- Dated events (rule B): a list of external episodes written down before results are seen.
- Statistical regime detector on inflation (rule C): robustness only, because it is
  circular.
- Managed or pegged currencies analysed separately with a different floor, since the floor
  of 0.005 flags any move above roughly 1.5% there.

## Unit of inference

Months inside one episode are dependent, so the unit of inference is the episode, not the
month. Coverage is reported with confidence intervals that account for this (block
bootstrap by episode, and pooling across countries). No country-level conclusion is drawn
for a country with fewer than 10 independent episodes.

## Data snapshot used for the feasibility check

- CPI: IMF `CPI`, monthly all-items index `M.<country>.PCPI_IX`, via DBnomics, snapshot
  indexed 2025-08-31. Ends mid-2025 for most countries; later months to be added from
  national sources. Russia has 30 gaps. Base-year breaks and splices are not yet checked.
- Panel: Kazakhstan, Russia, Azerbaijan, Uzbekistan, Colombia, Chile, Peru, Brazil,
  Mexico, Nigeria, Mongolia, Indonesia, South Africa.

## Feasibility result at threshold 3, FX only (before freezing)

Total episodes 220, of which 41 start after 2015-09. Kazakhstan alone has 6 episodes after
2015-09 (7 at threshold 2.5, 4 at 3.5), which is below the 10 needed for a country-level
conclusion, so Kazakhstan is a case study inside a pooled panel and not a stand-alone
inferential unit. Reproduced from the committed snapshot by `scripts/thesis/episodes.mjs`.

## Known weaknesses

- Sensitivity to the threshold is large for Kazakhstan (7, 6, 4 episodes).
- Pegged and managed currencies (Nigeria, Uzbekistan, Azerbaijan) can produce flags that
  reflect the exchange-rate regime and not an economic shock.
- Brent adds little at threshold 3 (events only in 2015-16 and 2020).
- The window length of 3 months is not yet checked against actual pass-through to prices.

## Changes

### 2026-11-19 (before any forecast was run)

Reason: a committee review scored the frozen rule 5.5/10; its main objection was that an
FX-based flag measures currency turbulence, not an inflation shock, and that the label's
timing was undefined. Two validity checks were then run. They are exploratory: they use the
same 13 countries that were used to shape the design.

Disclosures:

- The threshold of 3 was chosen after looking at the episode counts for 2.5, 3 and 3.5. It
  was not set blindly.
- The 60-month lookback for Kazakhstan before mid-2020 includes the years of the managed
  exchange rate, which lowers the scale `s` and produces more flags.
- Of the 6 Kazakhstan episodes after 2015-09 (2015-08..2017-05, 2020-03..2020-06,
  2022-03..2022-10, 2023-09..2023-12, 2024-07..2024-10, 2024-12..2025-03) only the first
  three are linked to a known event. The last three are moderate tenge moves that are not
  yet matched to events.

Label timing, now defined: results are reported for two labels. The origin label flags the
month in which the forecast is made (information available at forecast time). The target
label flags the month being forecast (contemporaneous; used only as a comparison).

Validity check 1, discrete label (`scripts/thesis/validity_check.mjs`, threshold 3, window +3):
share of the top-decile one-step errors of a naive forecast of monthly inflation that falls
inside shock windows, relative to the share of shock months.

| Sample | Label | Shock share | Recall | Lift | Permutation p |
|---|---|---|---|---|---|
| All evaluable months, 13 countries | target | 0.204 | 0.382 | 1.87 | 0.0005 |
| All evaluable months | origin | 0.204 | 0.364 | 1.79 | 0.0005 |
| Since 2015-09 | target | 0.172 | 0.288 | 1.68 | 0.0015 |
| Since 2015-09 | origin | 0.171 | 0.255 | 1.49 | 0.0125 |

Lift is below the committee's bar of 2. Nigeria and Uzbekistan have 35-41% of months in
shock windows, which points to an exchange-rate-regime artefact.

Validity check 2, continuous stress (`scripts/thesis/stress_check.mjs`): stress at month t
is the maximum |z| of the FX one-month log change over t-3..t. Pooled within-country rank
correlation with the naive one-step error: 0.075 (permutation p = 0.001) for origin stress
over all months, 0.091 for target stress, 0.050 (p = 0.0495) for origin stress since
2015-09. The relation is not monotone: deciles 2-8 are flat, and the share of top-decile
errors is 0.134 in decile 9 and 0.235 in decile 10 (base rate 0.10; 0.210 in decile 10
since 2015-09). Decile 1 is also raised (0.142) and is not explained.

Decisions:

1. The main contribution of the thesis does not depend on shocks: multi-step intervals
   (horizons 1-12 months), a panel of commodity-dependent economies, foundation-model
   forecasters next to classical and ML ones, and coverage reported with confidence
   intervals and pooling across countries.
2. The stress analysis is a secondary contribution. Stress is analysed as a continuous
   variable (coverage by stress decile), with the discrete shock windows as a secondary
   check. The result is reported as it is: a weak association concentrated in the upper
   tail of stress.
3. Parameters of the discrete rule stay as frozen above. They are not tuned to raise lift.
   The upper decile is not promoted to a primary threshold after the fact.
4. Confirmatory evaluation of any stress claim is planned on months after the snapshot
   (after 2025-06) and on countries not used for shaping the design. Everything computed on
   the current snapshot is exploratory.
5. Snapshot: `scripts/thesis/data/snapshot.json`, SHA-256
   `d01b8360c4167f0b3d829f3d7af0438c36fe858c9f2e2745e9b258039cc2d739`.
