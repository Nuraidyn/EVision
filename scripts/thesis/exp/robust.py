"""Robustness analyses S1-S5 (sixth protocol entry), computed from EXISTING interval outputs only.

No forecast is re-run and no new data is read.  Thresholds, the 2 pp equivalence margin, block-length
rule max(h, 12) and the contrast definitions are those of calibration.py (functions are reused).
Rows with sample == 'confirmatory' are refused.  All analyses are secondary and do not replace R1-R5.

Subcommand (from scripts/thesis):
    .venv/Scripts/python.exe -m exp.run robust --in results/holdout_ncal48 --sample holdout \
        [--instant results/diag_instant_h12_holdout] [--delayed results/holdout_ncal48] \
        [--out results/holdout_ncal48/robust] [--n-cal 48] [--boot 2000] [--boot-loo 500] [--model lgbm]

Flags
  --in         run (delayed feedback) whose intervals_all.csv feeds S1, S2, S4 (and S3 as the delayed side)
  --instant    diagnostic run with instant feedback at h=12 (S3); S3 is skipped when absent
  --delayed    optional override of the delayed side of S3 (default: --in)
  --sample     exploratory | holdout
  --n-cal      warm-up of the run, only used for labels (48 = primary, anything else = sensitivity)
  --boot       bootstrap replicates for S2/S3 (default 2000, as the primary contrasts)
  --boot-loo   bootstrap replicates for S1 (default 500, fewer for speed; same seed and block rule)
  --only       comma list of s1,s2,s3,s4 (default all)

Outputs (<out>/): s1_leave_one_out.csv, s2_other_models.csv, s3_feedback_diff.csv, s4_width_efficiency.csv,
s4_compact.csv.
S1: one row per (contrast, h, removed_unit) with T and CI, plus a SUMMARY row per contrast/h (min/max T over
    removals, number of removals changing the sign of the full-sample T).  Units are the 'unit' column, so a
    Russia stretch is one unit per stretch.
S2: contrasts with each base model in the 'model' column; TOST verdict for dracp-aci.
S3: coverage(instant) - coverage(delayed), identical (unit, origin) cells, moving-block bootstrap of origin
    months (block 12, months resampled jointly across units); pooled (unit == 'ALL', cells equally weighted)
    and per unit.
S4: per method/horizon: per-unit and pooled (equal unit weights) ratio of mean Winkler and of median width to
    rolling conformal on cells common to both, next to CE.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .calibration import (BLOCK_LEN, CE_HORIZONS, CE_PRIMARY, CE_SECONDARY, NOMINAL, TOST_CONTRAST,
                          block_len_ce, ce_arrays, ce_contrast_test, tost_test)
from .evaluate import block_indices

CONTRASTS = CE_SECONDARY + CE_PRIMARY            # aci-split, aci-rolling, dracp-aci
S2_MODELS = ("lgbm", "arima", "naive_b")         # lgbm = reference
S3_METHODS = ("aci", "dracp", "faci", "rolling", "split", "pid")
S4_HORIZONS = (1, 3, 6, 12)
REF = "rolling"


def _sample_rows(iv: pd.DataFrame, sample: str) -> pd.DataFrame:
    if sample == "confirmatory":
        raise ValueError("robust analyses must not use the confirmatory sample")
    g = iv[iv["sample"] == sample]
    if g.empty:
        raise ValueError(f"no rows with sample={sample!r}")
    return g


# ------------------------------------------------------------------------------------- S1
def s1_leave_one_out(iv, model="lgbm", sample="exploratory", B=500, seed=12345, block_len=BLOCK_LEN):
    iv = _sample_rows(iv, sample)
    rows = []
    for h in CE_HORIZONS:
        for a, b in CONTRASTS:
            arrs = ce_arrays(iv, model, h, a, b, sample)
            name = f"{a}-{b}"
            if arrs is None:
                continue
            Ha, Hb, O, units = arrs
            full = ce_contrast_test(arrs, h, B, seed, block_len)
            rows.append(dict(contrast=name, h=h, removed_unit="NONE(full)", n_units=len(units), T=full["T"],
                             ci_lo=full["ci_lo"], ci_hi=full["ci_hi"], p=full["p"], sign_change=False))
            loo = []
            for i, u in enumerate(units):
                keep = np.arange(len(units)) != i
                r = ce_contrast_test((Ha[keep], Hb[keep], O[keep], [x for x in units if x != u]), h, B, seed,
                                     block_len)
                chg = bool(np.sign(r["T"]) != np.sign(full["T"]))
                loo.append(r["T"])
                rows.append(dict(contrast=name, h=h, removed_unit=u, n_units=len(units) - 1, T=r["T"],
                                 ci_lo=r["ci_lo"], ci_hi=r["ci_hi"], p=r["p"], sign_change=chg))
            loo = np.array(loo)
            rows.append(dict(contrast=name, h=h, removed_unit="SUMMARY", n_units=len(units), T=full["T"],
                             T_min=float(loo.min()), T_max=float(loo.max()),
                             n_sign_changes=int((np.sign(loo) != np.sign(full["T"])).sum()),
                             n_removals=len(loo), B=B))
    df = pd.DataFrame(rows)
    df.insert(0, "sample", sample)
    df.insert(1, "model", model)
    return df


# ------------------------------------------------------------------------------------- S2
def s2_other_models(iv, models=S2_MODELS, sample="exploratory", B=2000, seed=12345, block_len=BLOCK_LEN):
    iv = _sample_rows(iv, sample)
    rows = []
    for m in models:
        if m not in set(iv.model):
            continue
        for h in CE_HORIZONS:
            for a, b in CONTRASTS:
                arrs = ce_arrays(iv, m, h, a, b, sample)
                r = ce_contrast_test(arrs, h, B, seed, block_len)
                row = dict(sample=sample, model=m, contrast=f"{a}-{b}", h=h, **r)
                if (a, b) == TOST_CONTRAST:
                    t = tost_test(arrs, h, B=B, seed=seed, block_len=block_len)
                    row.update(p_tost=t["p_tost"], tost_verdict=t["verdict"])
                rows.append(row)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------- S3
def paired_cells(instant: pd.DataFrame, delayed: pd.DataFrame, method: str, model="lgbm", h=12):
    """(unit, origin) cells present in both runs for one method; columns cov_instant, cov_delayed."""
    k = ["unit", "origin"]

    def f(d):
        return d[(d.model == model) & (d.h == h) & (d.method == method)][k + ["covered"]]

    x = f(instant).merge(f(delayed), on=k, suffixes=("_instant", "_delayed"))
    x = x.rename(columns={"covered_instant": "cov_instant", "covered_delayed": "cov_delayed"})
    return x, len(f(instant)), len(f(delayed))


def paired_diff_boot(x: pd.DataFrame, h=12, B=2000, seed=12345, block_len=BLOCK_LEN, per_unit=True):
    """Instant-minus-delayed coverage with a joint moving-block bootstrap of origin months.
    Returns rows (unit 'ALL' pooled with equal cell weights, then each unit)."""
    if x.empty:
        return []
    o = pd.PeriodIndex(x["origin"], freq="M")
    grid = pd.period_range(o.min(), o.max(), freq="M")
    t = np.array([(p - grid[0]).n for p in o], dtype=int)
    units = sorted(x["unit"].unique())
    ui = x["unit"].map({u: i for i, u in enumerate(units)}).values
    U, T = len(units), len(grid)
    D, C, N = np.zeros((U, T)), np.zeros((U, T)), np.zeros((U, T))
    D[ui, t] = (x["cov_instant"] - x["cov_delayed"]).values
    C[ui, t] = x["cov_delayed"].values
    N[ui, t] = 1.0
    rng = np.random.default_rng(seed)
    idx = block_indices(T, block_len_ce(h, block_len), B, rng)

    def one(d, c, n):
        n_ = n.sum()
        est = d.sum() / n_
        bs = d[idx].sum(1) / np.maximum(n[idx].sum(1), 1e-12)
        return dict(n=int(n_), cov_delayed=c.sum() / n_, cov_instant=c.sum() / n_ + est, diff=est,
                    ci_lo=float(np.quantile(bs, 0.025)), ci_hi=float(np.quantile(bs, 0.975)))

    rows = [dict(unit="ALL", **one(D.sum(0), C.sum(0), N.sum(0)))]
    if per_unit:
        rows += [dict(unit=u, **one(D[i], C[i], N[i])) for i, u in enumerate(units)]
    return rows


def s3_feedback(instant, delayed, model="lgbm", sample="exploratory", h=12, methods=S3_METHODS, B=2000,
                seed=12345, block_len=BLOCK_LEN):
    instant, delayed = _sample_rows(instant, sample), _sample_rows(delayed, sample)
    rows = []
    for m in methods:
        x, ni, nd = paired_cells(instant, delayed, m, model, h)
        for r in paired_diff_boot(x, h, B, seed, block_len):
            rows.append(dict(sample=sample, model=model, h=h, method=m, cells_instant=ni, cells_delayed=nd,
                             cells_paired=len(x), **r))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------- S4
def s4_width_efficiency(iv, model="lgbm", sample="exploratory", hs=S4_HORIZONS, ref=REF):
    """Per method/h: per unit and pooled (equal unit weights) ratios to ``ref`` on common cells."""
    iv = _sample_rows(iv, sample)
    g = iv[iv.model == model]
    k = ["unit", "origin"]
    rows = []
    for h in hs:
        gh = g[g.h == h]
        r = gh[gh.method == ref][k + ["winkler", "width"]].rename(
            columns={"winkler": "winkler_ref", "width": "width_ref"})
        for m in sorted(gh.method.unique()):
            x = gh[gh.method == m][k + ["winkler", "width", "covered"]].merge(r, on=k)
            if x.empty:
                continue
            pu = x.groupby("unit").agg(n=("covered", "size"), cov=("covered", "mean"), wink=("winkler", "mean"),
                                       wink_ref=("winkler_ref", "mean"), width=("width", "median"),
                                       width_ref=("width_ref", "median")).reset_index()
            pu["ce"] = (pu["cov"] - NOMINAL).abs()
            for _, q in pu.iterrows():
                rows.append(dict(sample=sample, model=model, h=h, method=m, unit=q["unit"], n=int(q["n"]),
                                 coverage=q["cov"], ce=q["ce"], winkler_ratio=q["wink"] / q["wink_ref"],
                                 width_ratio=q["width"] / q["width_ref"]))
            rows.append(dict(sample=sample, model=model, h=h, method=m, unit="POOLED", n=int(pu["n"].sum()),
                             coverage=pu["cov"].mean(), ce=pu["ce"].mean(),
                             winkler_ratio=pu["wink"].mean() / pu["wink_ref"].mean(),
                             width_ratio=pu["width"].mean() / pu["width_ref"].mean()))
    return pd.DataFrame(rows)


def s4_compact(s4: pd.DataFrame) -> pd.DataFrame:
    p = s4[s4.unit == "POOLED"]
    out = p.pivot_table(index="method", columns="h", values=["ce", "winkler_ratio", "width_ratio"])
    order = ["ce", "winkler_ratio", "width_ratio"]
    cols = sorted(out.columns, key=lambda c: (c[1], order.index(c[0])))
    out = out[cols]
    out.columns = [f"{a}_h{b}" for a, b in out.columns]
    return out.reset_index()
