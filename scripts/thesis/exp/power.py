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
