"""Minimum detectable difference (MDE) in coverage for the two primary contrasts.

Assumptions (stated so they can be criticised)
----------------------------------------------
1. The unit of analysis is the per-cell difference d = 1{covered by A} - 1{covered by B} for
   (unit, origin month); the pooled estimate is the ratio of sums over cells.
2. Dependence is taken from the data: the observed per-calendar-month sums (s_t = sum of d over
   units, c_t = number of units observed) are resampled in moving blocks of length
   max(h, 6) months, jointly across units.  This keeps cross-country common shocks and the
   h-step overlap of errors, but assumes the dependence beyond the block length is zero.
3. Alternative with true difference delta: s*_t = s_t - est*c_t + delta*c_t (centre the observed
   difference at zero, then shift by delta in every cell).
4. Each simulated dataset is tested with the same centred block bootstrap used in the real
   analysis (evaluate.contrast_test logic, B_inner draws), two-sided.
5. alpha = 0.05 with Holm over 4 tests.  Holm's first step is the Bonferroni threshold
   alpha/4, which is what a contrast must meet to be rejected first; we use alpha/4 for every
   contrast, i.e. a conservative (upper-bound) MDE for the Holm procedure.
6. Common random numbers are used across delta values so power is monotone in delta and
   bisection is valid.  MDE = smallest delta with power >= 0.80, reported in percentage points.
7. The exploratory data are used; confirmatory sample sizes (<= ~16 months) will be smaller,
   hence MDE there is larger.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .evaluate import PRIMARY, block_indices, block_len_for, month_sums, paired_panel


def power_at(delta, s0, c, h, out_idx, in_idx, crit):
    """Rejection rate at true difference ``delta`` (fraction, e.g. 0.05)."""
    rej = 0
    for idx in out_idx:
        s = s0[idx] + delta * c[idx]
        cc = c[idx]
        est = s.sum() / cc.sum()
        bs = s[in_idx].sum(1) / np.maximum(cc[in_idx].sum(1), 1e-12)
        p = (1 + np.sum(np.abs(bs - est) >= abs(est))) / (len(bs) + 1)
        rej += p <= crit
    return rej / len(out_idx)


def mde_panel(panel: pd.DataFrame, h: int, alpha: float = 0.05, n_tests: int = 4, power: float = 0.80,
              n_outer: int = 200, B_inner: int = 199, seed: int = 7) -> dict:
    if panel.empty:
        return dict(n_cells=0, n_months=0, mde_pp=np.nan)
    s, c, _ = month_sums(panel, "d")
    est = s.sum() / c.sum()
    s0 = s - est * c                                   # centred at zero difference
    if np.allclose(s0, 0):                             # no discordant cells: variance is not identified
        return dict(n_cells=int(c.sum()), n_months=int((c > 0).sum()), observed_diff_pp=100 * est, mde_pp=np.nan)
    T = len(s)
    rng = np.random.default_rng(seed)
    bl = block_len_for(h)
    out_idx = block_indices(T, bl, n_outer, rng)
    in_idx = block_indices(T, bl, B_inner, rng)
    crit = alpha / n_tests
    lo, hi = 0.0, 0.6
    if power_at(hi, s0, c, h, out_idx, in_idx, crit) < power:
        return dict(n_cells=int(c.sum()), n_months=int((c > 0).sum()), mde_pp=np.nan)
    for _ in range(9):
        mid = (lo + hi) / 2
        if power_at(mid, s0, c, h, out_idx, in_idx, crit) >= power:
            hi = mid
        else:
            lo = mid
    return dict(n_cells=int(c.sum()), n_months=int((c > 0).sum()), observed_diff_pp=100 * est,
                mde_pp=100 * hi)


def mde_table(iv: pd.DataFrame, model: str, sample: str | None = "exploratory", **kw) -> pd.DataFrame:
    rows = []
    for h in (3, 6):
        for a, b in PRIMARY:
            r = mde_panel(paired_panel(iv, model, h, a, b, sample), h, **kw)
            r.update(model=model, h=h, contrast=f"{a}-{b}", sample=sample)
            r["status"] = ("ok (<=7pp)" if r["mde_pp"] <= 7 else
                           "inconclusive (>10pp)" if (r["mde_pp"] > 10 or np.isnan(r["mde_pp"])) else "between 7 and 10pp")
            rows.append(r)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- CE contrast MDE
# MDE for the calibration-error (CE) contrast  T = mean_u (CE_u,a - CE_u,b)  (see calibration.py).
#
# What is simulated (an analogue of the coverage MDE, because T is nonlinear in the hits and the
# "shift every cell by delta" device of mde_panel cannot be used):
# 1. Baseline method b keeps its OBSERVED hit pattern (unit x origin month), so cross-country common
#    shocks and h-step overlap stay in the data.
# 2. Method a is constructed from b: per unit with observed coverage cb_u a target coverage pa_u is
#    set so that CE_a = max(CE_b - delta, 0) on the same side of 0.90
#    (pa = 0.90 + sign(cb-0.90) * max(|cb-0.90| - delta, 0)).  If pa < cb each hit of b becomes a
#    miss with prob (cb-pa)/cb; if pa > cb each miss becomes a hit with prob (pa-cb)/(1-cb).
#    Fixed uniform draws are reused across delta (common random numbers), so a's hits are nested in
#    delta and power is monotone.  At delta = 0, a == b and T = 0.  Units with CE_b < delta can only
#    be improved to 0, so the realised mean improvement is a bit below delta (reported as
#    realised_T_pp).
# 3. Each outer replicate resamples origin months in moving blocks of max(h, 6) jointly over units
#    (dependence taken from the data, zero beyond a block), recomputes T and applies the same
#    centred block-bootstrap test as the real analysis (B_inner draws), two-sided.
# 4. alpha = 0.05 with Holm over 4 tests -> each contrast tested at alpha/4 (Bonferroni, an upper
#    bound on the MDE under Holm).  MDE = smallest delta with power >= 0.80, by bisection, in
#    percentage points of mean |coverage - 0.90|.
# Assumptions: observed hits of b describe the true dependence and calibration heterogeneity; the
# alternative is a pure reduction of calibration error (a = b thinned/thickened); the exploratory
# sample is used, so confirmatory MDEs (about 15 months per unit) will be larger.


def _ce_alt_hits(Hb, O, delta, Uni, nominal=0.90):
    n = O.sum(1)
    cb = np.where(n > 0, Hb.sum(1) / np.maximum(n, 1), nominal)
    pa = nominal + np.sign(cb - nominal) * np.maximum(np.abs(cb - nominal) - delta, 0.0)
    down = (pa < cb)[:, None]
    p_down = (np.maximum(cb - pa, 0) / np.maximum(cb, 1e-12))[:, None]
    p_up = (np.maximum(pa - cb, 0) / np.maximum(1 - cb, 1e-12))[:, None]
    Ha = np.where(down & (Hb == 1) & (Uni < p_down), 0.0, Hb)
    Ha = np.where((~down) & (Hb == 0) & (O == 1) & (Uni < p_up), 1.0, Ha)
    return Ha * O


def _ce_power(delta, Hb, O, Uni, out_idx, in_idx, crit):
    from .calibration import t_stat
    Ha = _ce_alt_hits(Hb, O, delta, Uni)
    rej = 0
    for idx in out_idx:
        Ha_, Hb_, O_ = Ha[:, idx], Hb[:, idx], O[:, idx]
        est = t_stat(Ha_, Hb_, O_)
        bs = t_stat(Ha_, Hb_, O_, in_idx)
        p = (1 + np.sum(np.abs(bs - est) >= abs(est))) / (len(bs) + 1)
        rej += p <= crit
    return rej / len(out_idx)


def mde_ce_panel(arrs, h: int, alpha: float = 0.05, n_tests: int = 4, power: float = 0.80,
                 n_outer: int = 100, B_inner: int = 199, seed: int = 7, block_len: int = 12) -> dict:
    from .calibration import block_len_ce, t_stat
    if arrs is None:
        return dict(n_units=0, n_months=0, mde_pp=np.nan, realised_T_pp=np.nan)
    _, Hb, O, units = arrs
    rng = np.random.default_rng(seed)
    Uni = rng.random(Hb.shape)
    T = O.shape[1]
    bl = block_len_ce(h, block_len)
    out_idx = block_indices(T, bl, n_outer, rng)
    in_idx = block_indices(T, bl, B_inner, rng)
    crit = alpha / n_tests
    info = dict(n_units=len(units), n_months=int((O.sum(0) > 0).sum()))
    lo, hi = 0.0, 0.10
    if _ce_power(hi, Hb, O, Uni, out_idx, in_idx, crit) < power:
        return dict(**info, mde_pp=np.nan, realised_T_pp=np.nan)
    for _ in range(8):
        mid = (lo + hi) / 2
        if _ce_power(mid, Hb, O, Uni, out_idx, in_idx, crit) >= power:
            hi = mid
        else:
            lo = mid
    Ha = _ce_alt_hits(Hb, O, hi, Uni)
    return dict(**info, mde_pp=100 * hi, realised_T_pp=100 * t_stat(Ha, Hb, O))


def mde_ce_table(iv: pd.DataFrame, model: str, sample: str | None = "exploratory", **kw) -> pd.DataFrame:
    from .calibration import CE_HORIZONS, CE_PRIMARY, ce_arrays
    rows = []
    for h in CE_HORIZONS:
        for a, b in CE_PRIMARY:
            r = mde_ce_panel(ce_arrays(iv, model, h, a, b, sample), h, **kw)
            r.update(model=model, h=h, contrast=f"{a}-{b}", sample=sample)
            rows.append(r)
    return pd.DataFrame(rows)


def mde_ce_windows(iv: pd.DataFrame, model: str, sample: str | None = "exploratory", window: int = 15,
                   n_windows: int = 60, seed: int = 11, n_outer: int = 40, B_inner: int = 99,
                   block_len: int = 12) -> pd.DataFrame:
    """MDE of the CE contrasts on random ``window``-month stretches of the (exploratory) data, to
    judge confirmatory-size panels.  For each contrast, ``n_windows`` windows of consecutive origin
    months are drawn uniformly (all units kept; the months are therefore jointly resampled as in
    the real analysis) and mde_ce_panel is run on each (block length max(h, block_len), clipped to
    the window length).  Reported per contrast: median, quartiles of the MDE over windows, the
    share of windows where the MDE is undefined (> 10 pp) and the share with MDE <= 7 pp."""
    from .calibration import CE_HORIZONS, CE_PRIMARY, ce_arrays
    rows = []
    for h in CE_HORIZONS:
        for a, b in CE_PRIMARY:
            arrs = ce_arrays(iv, model, h, a, b, sample)
            base = dict(model=model, h=h, contrast=f"{a}-{b}", sample=sample, window=window)
            if arrs is None or arrs[2].shape[1] < window:
                rows.append(dict(**base, n_windows=0, mde_median_pp=np.nan))
                continue
            Ha, Hb, O, units = arrs
            T = O.shape[1]
            rng = np.random.default_rng(seed + h)
            starts = rng.integers(0, T - window + 1, size=n_windows)
            mdes, kept = [], 0
            for i, s0 in enumerate(starts):
                sl = slice(int(s0), int(s0) + window)
                if O[:, sl].sum() == 0:
                    continue
                kept += 1
                r = mde_ce_panel((Ha[:, sl], Hb[:, sl], O[:, sl], units), h, n_outer=n_outer,
                                 B_inner=B_inner, seed=seed + i, block_len=block_len)
                mdes.append(r["mde_pp"])
            m = np.array(mdes, float)
            fin = m[np.isfinite(m)]
            rows.append(dict(**base, n_windows=kept,
                             mde_median_pp=float(np.median(fin)) if len(fin) else np.nan,
                             mde_q25_pp=float(np.quantile(fin, 0.25)) if len(fin) else np.nan,
                             mde_q75_pp=float(np.quantile(fin, 0.75)) if len(fin) else np.nan,
                             share_undefined=float(np.mean(~np.isfinite(m))) if len(m) else np.nan,
                             share_le_7pp=float(np.mean(np.isfinite(m) & (m <= 7))) if len(m) else np.nan))
    return pd.DataFrame(rows)
