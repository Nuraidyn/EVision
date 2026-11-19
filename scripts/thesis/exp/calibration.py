"""Calibration-error (CE) contrasts: the primary family after the fourth protocol amendment.

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

Primary family (Holm over 4 tests): aci-rolling and dracp-aci at h = 3, 6.  aci-split is a
secondary descriptive contrast.  dracp-aci is additionally tested for equivalence (TOST, margin
2 pp of CE), reported separately (not part of the Holm family).  Winkler (relative difference of
the equal-unit-weight mean Winkler score) and the cross-unit SD of coverage are reported next to CE.

Inference: moving-block bootstrap of ORIGIN calendar months, block length max(h, block_len) with
block_len = 12 by default, the same month indices for all units (joint resampling).  Per replicate
the per-unit statistics are recomputed from the resampled months (units without an observation in a
replicate are skipped).  Reported: estimate, 95% percentile CI, two-sided centred-bootstrap p (share
of replicates with |T* - T| >= |T|).

Caveat: |cov - 0.90| is biased upward by sampling noise (more so for small n per unit); the bias
largely cancels in T because both methods have the same n per unit, but see null_ce_bias().
Samples: 'exploratory', 'confirmatory' and 'holdout' are all pooled over units the same way.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .evaluate import block_indices, holm

NOMINAL = 0.90
CE_PRIMARY = [("aci", "rolling"), ("dracp", "aci")]      # primary family, 4 tests with h
CE_SECONDARY = [("aci", "split")]                         # descriptive
CE_HORIZONS = (3, 6)
BLOCK_LEN = 12                                            # block length = max(h, BLOCK_LEN)
TOST_CONTRAST = ("dracp", "aci")
TOST_MARGIN = 0.02                                        # 2 pp of CE
TOST_ALPHA = 0.05


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


def value_arrays(iv: pd.DataFrame, model: str, h: int, a: str, b: str, sample: str | None = "exploratory",
                 col: str = "covered"):
    """Unit x month matrices (Va, Vb, obs, units) of column ``col`` on the complete monthly origin grid.
    obs is 1 where the (unit, origin) cell exists for both methods (paired panel)."""
    g = iv[(iv.model == model) & (iv.h == h)]
    if sample:
        g = g[g["sample"] == sample]
    k = ["unit", "origin"]
    x = g[g.method == a][k + [col]].merge(g[g.method == b][k + [col]], on=k, suffixes=("_a", "_b"))
    if x.empty:
        return None
    o = pd.PeriodIndex(x["origin"], freq="M")
    grid = pd.period_range(o.min(), o.max(), freq="M")
    t = np.array([(p - grid[0]).n for p in o], dtype=int)
    units = sorted(x["unit"].unique())
    ui = x["unit"].map({u: i for i, u in enumerate(units)}).values
    shape = (len(units), len(grid))
    Va, Vb, O = np.zeros(shape), np.zeros(shape), np.zeros(shape)
    Va[ui, t] = x[f"{col}_a"].values
    Vb[ui, t] = x[f"{col}_b"].values
    O[ui, t] = 1.0
    return Va, Vb, O, units


def ce_arrays(iv: pd.DataFrame, model: str, h: int, a: str, b: str, sample: str | None = "exploratory"):
    """(hits_a, hits_b, obs, units); see value_arrays."""
    return value_arrays(iv, model, h, a, b, sample, "covered")


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


def w_stat(Wa, Wb, O, idx=None):
    """Relative difference of the equal-unit-weight mean Winkler score: mean_u(Wa)/mean_u(Wb) - 1."""
    if idx is None:
        n = O.sum(1)
        ok = n > 0
        return float(np.mean(Wa.sum(1)[ok] / n[ok]) / np.mean(Wb.sum(1)[ok] / n[ok]) - 1.0)
    B, U = idx.shape[0], O.shape[0]
    ma, mb, ok = np.zeros((U, B)), np.zeros((U, B)), np.zeros((U, B), bool)
    for u in range(U):
        n = O[u][idx].sum(1)
        ok[u] = n > 0
        nd = np.maximum(n, 1)
        ma[u] = Wa[u][idx].sum(1) / nd
        mb[u] = Wb[u][idx].sum(1) / nd
    k = np.maximum(ok.sum(0), 1)
    return ((ma * ok).sum(0) / k) / np.maximum((mb * ok).sum(0) / k, 1e-12) - 1.0


def block_len_ce(h: int, block_len: int = BLOCK_LEN) -> int:
    """Block length of the calibration contrasts: max(h, block_len)."""
    return max(int(h), int(block_len))


def boot_stat(stat, arrs, h: int, B: int = 2000, seed: int = 12345, block_len: int = BLOCK_LEN):
    """Point estimate and (B,) bootstrap replicates of ``stat`` (t_stat or w_stat) with joint
    moving-block resampling of origin months."""
    Ha, Hb, O, _ = arrs
    est = stat(Ha, Hb, O)
    rng = np.random.default_rng(seed)
    idx = block_indices(O.shape[1], block_len_ce(h, block_len), B, rng)
    return est, stat(Ha, Hb, O, idx)


def _summ(est, bs, B):
    p = (1 + np.sum(np.abs(bs - est) >= abs(est))) / (B + 1)
    return dict(ci_lo=float(np.quantile(bs, 0.025)), ci_hi=float(np.quantile(bs, 0.975)), p=p)


def ce_contrast_test(arrs, h: int, B: int = 2000, seed: int = 12345, block_len: int = BLOCK_LEN) -> dict:
    if arrs is None:
        return dict(n_units=0, n_months=0, T=np.nan, ci_lo=np.nan, ci_hi=np.nan, p=np.nan)
    est, bs = boot_stat(t_stat, arrs, h, B, seed, block_len)
    O = arrs[2]
    return dict(n_units=len(arrs[3]), n_months=int((O.sum(0) > 0).sum()), T=est, **_summ(est, bs, B))


def tost_test(arrs, h: int, margin: float = TOST_MARGIN, B: int = 2000, seed: int = 12345,
              block_len: int = BLOCK_LEN) -> dict:
    """Two one-sided tests of equivalence |T| < margin (T = CE contrast, fraction units).
    p_lower tests H0: T <= -margin, p_upper tests H0: T >= +margin, both against the centred
    bootstrap distribution shifted to the boundary.  Equivalence if max(p) < alpha."""
    if arrs is None:
        return dict(T=np.nan, margin_pp=100 * margin, p_lower=np.nan, p_upper=np.nan, p_tost=np.nan,
                    verdict="not shown")
    est, bs = boot_stat(t_stat, arrs, h, B, seed, block_len)
    d = bs - est
    p_lower = (1 + np.sum(d >= est + margin)) / (B + 1)     # P(T_hat >= est | T = -margin)
    p_upper = (1 + np.sum(d <= est - margin)) / (B + 1)     # P(T_hat <= est | T = +margin)
    pt = max(p_lower, p_upper)
    return dict(T=est, margin_pp=100 * margin, p_lower=p_lower, p_upper=p_upper, p_tost=pt,
                verdict="equivalent" if pt < TOST_ALPHA else "not shown")


def ce_contrasts(iv: pd.DataFrame, model: str = "lgbm", sample: str | None = "exploratory",
                 B: int = 2000, seed: int = 12345, block_len: int = BLOCK_LEN,
                 secondary: bool = True) -> pd.DataFrame:
    """Primary family (4 tests, Holm) plus, if ``secondary``, descriptive secondary contrasts."""
    rows = []
    for fam, pairs in (("primary", CE_PRIMARY), ("secondary", CE_SECONDARY if secondary else [])):
        for h in CE_HORIZONS:
            for a, b in pairs:
                r = ce_contrast_test(ce_arrays(iv, model, h, a, b, sample), h, B, seed, block_len)
                rows.append(dict(model=model, h=h, contrast=f"{a}-{b}", family=fam, sample=sample,
                                 block_len=block_len_ce(h, block_len), **r))
    df = pd.DataFrame(rows)
    df["p_holm"] = np.nan
    prim = df["family"] == "primary"
    if df.loc[prim, "p"].notna().all():
        df.loc[prim, "p_holm"] = holm(df.loc[prim, "p"].tolist())
    return df


def tost_table(iv: pd.DataFrame, model: str = "lgbm", sample: str | None = "exploratory",
               margin: float = TOST_MARGIN, B: int = 2000, seed: int = 12345,
               block_len: int = BLOCK_LEN) -> pd.DataFrame:
    rows = []
    for h in CE_HORIZONS:
        r = tost_test(ce_arrays(iv, model, h, *TOST_CONTRAST, sample), h, margin, B, seed, block_len)
        rows.append(dict(model=model, h=h, contrast="-".join(TOST_CONTRAST), sample=sample, **r))
    return pd.DataFrame(rows)


def winkler_contrasts(iv: pd.DataFrame, model: str = "lgbm", sample: str | None = "exploratory",
                      B: int = 2000, seed: int = 12345, block_len: int = BLOCK_LEN) -> pd.DataFrame:
    """Relative difference of per-unit mean Winkler (equal unit weights); descriptive, unadjusted p."""
    rows = []
    for h in CE_HORIZONS:
        for a, b in CE_PRIMARY + CE_SECONDARY:
            arrs = value_arrays(iv, model, h, a, b, sample, "winkler")
            if arrs is None:
                r = dict(rel_diff=np.nan, ci_lo=np.nan, ci_hi=np.nan, p=np.nan)
            else:
                est, bs = boot_stat(w_stat, arrs, h, B, seed, block_len)
                r = dict(rel_diff=est, **_summ(est, bs, B))
            rows.append(dict(model=model, h=h, contrast=f"{a}-{b}", sample=sample, **r))
    return pd.DataFrame(rows)


def sd_coverage(iv: pd.DataFrame, hs=(1, 3, 6, 12), sample: str | None = "exploratory") -> pd.DataFrame:
    """Cross-unit standard deviation (ddof=1) of per-unit coverage, per model/method/h."""
    pu = per_unit_coverage(iv, hs, sample)
    if pu.empty:
        return pd.DataFrame()
    g = pu.groupby(["model", "method", "h", "sample"])["coverage"]
    return g.agg(n_units="size", mean_coverage="mean",
                 sd_coverage=lambda x: x.std(ddof=1) if len(x) > 1 else np.nan,
                 min_coverage="min", max_coverage="max").reset_index()


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
