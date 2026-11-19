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
inferential unit. The script that produced the counts is not part of the repository.

## Known weaknesses

- Sensitivity to the threshold is large for Kazakhstan (7, 6, 4 episodes).
- Pegged and managed currencies (Nigeria, Uzbekistan, Azerbaijan) can produce flags that
  reflect the exchange-rate regime and not an economic shock.
- Brent adds little at threshold 3 (events only in 2015-16 and 2020).
- The window length of 3 months is not yet checked against actual pass-through to prices.

## Changes

None.
