"""Calibration-error (CE) contrasts: a second family of primary contrasts.

Pooled coverage can cancel opposite deviations of different units (one method over-covers in some
countries and under-covers in others).  The CE family is robust to this.

Definition (fixed)
------------------
For base model, horizon h and sample, per unit u (country; a Russia stretch is its own unit):
    coverage_{u,m} = share of origin months in which the target lies in the interval of method m
    CE_{u,m}       = |coverage_{u,m} - 0.90|
    T(m1, m2)      = mean over units (equal weights) of CE_{u,m1} - CE_{u,m2}
Negative T means m1 is better calibrated.  Only (unit, origin) cells present for BOTH methods
are used (paired panel).

Inference: moving-block bootstrap of ORIGIN calendar months, block length max(h, 6), the same
month indices for all units (joint resampling) -- the same machinery as evaluate.py (block_indices,
block_len_for).  Per replicate the per-unit coverages are recomputed from the resampled months
(units without an observation in a replicate are skipped), then T.  Reported: T, 95% percentile
CI, two-sided centred-bootstrap p (same formula as evaluate.contrast_test: share of replicates
with |T* - T| >= |T|), Holm over the 4 tests.

Caveat: |cov - 0.90| is biased upward by sampling noise (more so for small n per unit); the bias
largely cancels in T because both methods have the same n per unit, but see null_ce_bias().
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .evaluate import block_indices, block_len_for, holm

NOMINAL = 0.90
CE_PRIMARY = [("aci", "split"), ("dracp", "aci")]
CE_HORIZONS = (3, 6)


def ce_value(cov, nominal: float = NOMINAL):
    return np.abs(np.asarray(cov, float) - nominal)


def per_unit_coverage(iv: pd.DataFrame, hs=(1, 3, 6, 12), sample: str | None = "exploratory") -> pd.DataFrame:
    """Long table: model, method, h, sample, unit, n, coverage, ce."""
    g = iv if sample is None else iv[iv["sample"] == sample]
    g = g[g.h.isin(hs)]
    out = (g.groupby(["model", "method", "h", "sample", "unit"])["covered"]
           .agg(n="size", coverage="mean").reset_index())
    out["ce"] = ce_value(out["coverage"])
    return out


def ce_arrays(iv: pd.DataFrame, model: str, h: int, a: str, b: str, sample: str | None = "exploratory"):
    """Unit x month matrices (hits_a, hits_b, obs) on the complete monthly origin grid.
    obs is 1 where the (unit, origin) cell exists for both methods."""
    g = iv[(iv.model == model) & (iv.h == h)]
    if sample:
        g = g[g["sample"] == sample]
    k = ["unit", "origin"]
    x = g[g.method == a][k + ["covered"]].merge(g[g.method == b][k + ["covered"]], on=k, suffixes=("_a", "_b"))
    if x.empty:
        return None
    o = pd.PeriodIndex(x["origin"], freq="M")
    grid = pd.period_range(o.min(), o.max(), freq="M")
    t = np.array([(p - grid[0]).n for p in o], dtype=int)
    units = sorted(x["unit"].unique())
    ui = x["unit"].map({u: i for i, u in enumerate(units)}).values
    shape = (len(units), len(grid))
    Ha, Hb, O = np.zeros(shape), np.zeros(shape), np.zeros(shape)
    Ha[ui, t] = x["covered_a"].values
    Hb[ui, t] = x["covered_b"].values
    O[ui, t] = 1.0
    return Ha, Hb, O, units


def t_stat(Ha, Hb, O, idx=None, nominal: float = NOMINAL):
    """T for the original data (idx None) or for each row of idx (B, T) -> array (B,)."""
    if idx is None:
        n = O.sum(1)
        ok = n > 0
        cea = np.abs(Ha.sum(1)[ok] / n[ok] - nominal)
        ceb = np.abs(Hb.sum(1)[ok] / n[ok] - nominal)
        return float(np.mean(cea - ceb))
    B = idx.shape[0]
    U = O.shape[0]
    na, nb, nn = np.zeros((U, B)), np.zeros((U, B)), np.zeros((U, B))
    for u in range(U):
        na[u] = Ha[u][idx].sum(1)
        nb[u] = Hb[u][idx].sum(1)
        nn[u] = O[u][idx].sum(1)
    ok = nn > 0
    nd = np.maximum(nn, 1)
    d = np.abs(na / nd - nominal) - np.abs(nb / nd - nominal)
    return np.where(ok, d, 0.0).sum(0) / np.maximum(ok.sum(0), 1)


def ce_contrast_test(arrs, h: int, B: int = 2000, seed: int = 12345) -> dict:
    if arrs is None:
        return dict(n_units=0, n_months=0, T=np.nan, ci_lo=np.nan, ci_hi=np.nan, p=np.nan)
    Ha, Hb, O, units = arrs
    est = t_stat(Ha, Hb, O)
    rng = np.random.default_rng(seed)
    idx = block_indices(O.shape[1], block_len_for(h), B, rng)
    bs = t_stat(Ha, Hb, O, idx)
    p = (1 + np.sum(np.abs(bs - est) >= abs(est))) / (B + 1)
    return dict(n_units=len(units), n_months=int((O.sum(0) > 0).sum()), T=est,
                ci_lo=float(np.quantile(bs, 0.025)), ci_hi=float(np.quantile(bs, 0.975)), p=p)


def ce_contrasts(iv: pd.DataFrame, model: str = "lgbm", sample: str | None = "exploratory",
                 B: int = 2000, seed: int = 12345) -> pd.DataFrame:
    rows = []
    for h in CE_HORIZONS:
        for a, b in CE_PRIMARY:
            r = ce_contrast_test(ce_arrays(iv, model, h, a, b, sample), h, B, seed)
            rows.append(dict(model=model, h=h, contrast=f"{a}-{b}", sample=sample, **r))
    df = pd.DataFrame(rows)
    df["p_holm"] = holm(df["p"].tolist()) if df["p"].notna().all() else np.nan
    return df


def null_ce_bias(n: int, p: float = NOMINAL, nominal: float = NOMINAL, n_sim: int = 200_000,
                 seed: int = 1) -> dict:
    """Simulate a unit with n independent hits of true coverage p.
    Returns E[CE] (mean |cov - nominal|) and, for two independent methods with the same true
    coverage p, E[T] = E[CE_1 - CE_2] (should be ~0) with its Monte-Carlo standard error."""
    rng = np.random.default_rng(seed)
    c1 = rng.binomial(n, p, n_sim) / n
    c2 = rng.binomial(n, p, n_sim) / n
    ce1, ce2 = np.abs(c1 - nominal), np.abs(c2 - nominal)
    d = ce1 - ce2
    return dict(n=n, true_cov=p, expected_ce=float(ce1.mean()), expected_T_null=float(d.mean()),
                se_T_null=float(d.std(ddof=1) / np.sqrt(n_sim)))
