"""Rolling-origin evaluation, metrics and moving-block bootstrap.

Decisions (also in README.md)
-----------------------------
* One origin per month, expanding window, first forecast origin = ``min_train`` months of data
  (default 60 monthly-inflation observations) so that LightGBM/ETS/ARIMA have a training sample.
* Interval evaluation rows are origins k >= n_cal + h - 1 (see intervals.py).  The point table
  uses exactly the same rows so that point and interval results are on the same sample.
* Sample label: exploratory if the TARGET month < 2025-07, confirmatory otherwise.
* Pooled statistics weight every (unit, origin month) cell equally (ratio of sums).
* Bootstrap: moving blocks of ORIGIN calendar months, block length = max(h, 6), the same
  month indices are used for all units (joint resampling), months without observations
  contribute zero weight.  p-values: centred bootstrap, two-sided.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .data import HORIZONS, sample_label
from .forecasters import make_forecasters
from .intervals import ALPHA, METHODS, run_method

EXTRA_FEATURES = ["m0", "m2", "roll3", "roll12", "fx0", "br0", "msin", "mcos"]


@dataclass
class Config:
    models: tuple = ("naive_a", "naive_b", "ets", "arima", "lgbm")
    conformal_models: tuple = ("naive_a", "naive_b", "ets", "arima", "lgbm")
    methods: tuple = tuple(METHODS)
    horizons: tuple = (1, 3, 6, 12)
    alpha: float = ALPHA
    min_train: int = 60
    n_cal: int = 48
    n_eval_last: int | None = None      # smoke: only forecast the last origins
    boot_B: int = 1000
    seed: int = 12345
    lgbm: dict = field(default_factory=dict)


# ----------------------------------------------------------------------------- running
def run_unit(unit: str, frame: pd.DataFrame, cfg: Config):
    """Returns (points_df, intervals_df) for one consecutive stretch."""
    L = len(frame)
    hs = list(cfg.horizons)
    hmin, hmax = min(hs), max(hs)
    pos_start = cfg.min_train
    if cfg.n_eval_last is not None:
        pos_start = max(pos_start, (L - 1 - hmax) - (cfg.n_cal + hmax - 1 + cfg.n_eval_last) + 1)
    pos_end = L - 1 - hmin
    if pos_end < pos_start:
        return pd.DataFrame(), pd.DataFrame()
    fcs = make_forecasters(cfg.models, lgbm=cfg.lgbm)
    store = {(mn, h): [] for mn in fcs for h in hs}
    for pos in range(pos_start, pos_end + 1):
        for mn, fc in fcs.items():
            res = fc.forecast(frame, pos, hs)
            for h in hs:
                store[(mn, h)].append((pos,) + res[h])
    country = frame.attrs.get("country", unit)
    pts, ivs = [], []
    for h in hs:
        for mn in fcs:
            rows = [r for r in store[(mn, h)] if r[0] <= L - 1 - h]
            if not rows:
                continue
            pos = np.array([r[0] for r in rows])
            point = np.array([r[1] for r in rows], float)
            nlo = np.array([np.nan if r[2] is None else r[2] for r in rows], float)
            nhi = np.array([np.nan if r[3] is None else r[3] for r in rows], float)
            y = frame[f"y{h}"].values[pos]
            n_fb = int(np.isnan(point).sum())
            if n_fb:   # failed fit: carry the previous point forecast forward (counted)
                point = pd.Series(point).ffill().bfill().values
                if np.isnan(point).any():
                    continue
            e = cfg.n_cal + h - 1
            if len(pos) <= e:
                continue
            origin = frame.index[pos]
            target = origin + h
            base = dict(unit=unit, country=country, model=mn, h=h, origin=origin.astype(str),
                        target=target.astype(str), y=y, point=point,
                        stress=frame["stress"].values[pos],
                        sample=[sample_label(t) for t in target], n_fallback=n_fb)
            pdf = pd.DataFrame(base).iloc[e:]
            pts.append(pdf)
            if mn in cfg.conformal_models:
                X = np.column_stack([point] + [np.nan_to_num(frame[c].values[pos]) for c in EXTRA_FEATURES])
                for me in cfg.methods:
                    out = run_method(me, X, y, h, cfg.n_cal, cfg.alpha)
                    d = pdf.copy()
                    d["method"] = me
                    d["lo"], d["hi"] = out["lo"][e:], out["hi"][e:]
                    d["n_capped"] = out["n_capped"]
                    ivs.append(d)
            if np.isfinite(nlo).any():
                d = pdf.copy()
                d["method"] = "native"
                d["lo"], d["hi"] = nlo[e:], nhi[e:]
                d["n_capped"] = 0
                d = d.dropna(subset=["lo", "hi"])
                ivs.append(d)
    pts = pd.concat(pts, ignore_index=True) if pts else pd.DataFrame()
    ivs = add_interval_columns(pd.concat(ivs, ignore_index=True), cfg.alpha) if ivs else pd.DataFrame()
    return pts, ivs


def add_interval_columns(iv: pd.DataFrame, alpha: float = ALPHA) -> pd.DataFrame:
    iv = iv.copy()
    iv["covered"] = ((iv["y"] >= iv["lo"]) & (iv["y"] <= iv["hi"])).astype(float)
    iv["width"] = iv["hi"] - iv["lo"]
    iv["winkler"] = winkler(iv["y"].values, iv["lo"].values, iv["hi"].values, alpha)
    return iv


def winkler(y, lo, hi, alpha=ALPHA):
    y, lo, hi = map(np.asarray, (y, lo, hi))
    return (hi - lo) + (2 / alpha) * np.maximum(lo - y, 0) + (2 / alpha) * np.maximum(y - hi, 0)


# ----------------------------------------------------------------------------- point metrics
def point_metrics(pts: pd.DataFrame) -> pd.DataFrame:
    """MAE/RMSE per (model, h, sample, unit) and pooled ('ALL'), relative to naive A and naive B.
    Relative = metric(model) / metric(naive) on identical rows."""
    p = pts.copy()
    p["err"] = p["y"] - p["point"]
    p["ae"], p["se"] = p["err"].abs(), p["err"] ** 2
    key = ["unit", "h", "origin", "sample"]
    ref = {}
    for nv in ("naive_a", "naive_b"):
        r = p[p["model"] == nv][key + ["ae", "se"]].rename(columns={"ae": f"ae_{nv}", "se": f"se_{nv}"})
        ref[nv] = r
    m = p
    for r in ref.values():
        m = m.merge(r, on=key, how="left")
    rows = []

    def agg(g, unit):
        r = dict(unit=unit, n=len(g), mae=g.ae.mean(), rmse=np.sqrt(g.se.mean()))
        for nv in ("naive_a", "naive_b"):
            ok = g[f"ae_{nv}"].notna()
            r[f"rel_mae_{nv}"] = g.ae[ok].mean() / g[f"ae_{nv}"][ok].mean() if ok.any() else np.nan
            r[f"rel_rmse_{nv}"] = (np.sqrt(g.se[ok].mean() / g[f"se_{nv}"][ok].mean())) if ok.any() else np.nan
        return r

    for (mod, h, smp), g in m.groupby(["model", "h", "sample"]):
        for u, gu in g.groupby("unit"):
            rows.append(dict(model=mod, h=h, sample=smp, **agg(gu, u)))
        r = dict(model=mod, h=h, sample=smp, **agg(g, "ALL"))
        # geometric mean of per-country relative MAE (scale-free across countries)
        for nv in ("naive_a", "naive_b"):
            vals = [x[f"rel_mae_{nv}"] for x in rows[-g["unit"].nunique():] if np.isfinite(x[f"rel_mae_{nv}"]) and x[f"rel_mae_{nv}"] > 0]
            r[f"gmean_rel_mae_{nv}"] = float(np.exp(np.mean(np.log(vals)))) if vals else np.nan
        rows.append(r)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- bootstrap
def block_indices(T: int, block_len: int, B: int, rng: np.random.Generator) -> np.ndarray:
    """(B, T) matrix of month indices from moving blocks (start uniform in [0, T-b])."""
    b = int(min(block_len, T))
    nb = int(np.ceil(T / b))
    starts = rng.integers(0, T - b + 1, size=(B, nb))
    idx = (starts[:, :, None] + np.arange(b)[None, None, :]).reshape(B, nb * b)
    return idx[:, :T]


def month_sums(df: pd.DataFrame, col: str):
    """Per-origin-calendar-month (sum, count) over all units, on the complete monthly grid."""
    o = pd.PeriodIndex(df["origin"], freq="M")
    grid = pd.period_range(o.min(), o.max(), freq="M")
    g = df.assign(_o=o).groupby("_o")[col].agg(["sum", "count"]).reindex(grid, fill_value=0)
    return g["sum"].values.astype(float), g["count"].values.astype(float), grid


def boot_ratio(sums, counts, block_len, B, rng):
    idx = block_indices(len(sums), block_len, B, rng)
    return sums[idx].sum(1) / np.maximum(counts[idx].sum(1), 1e-12)


def block_len_for(h: int) -> int:
    return max(h, 6)


def interval_summary(iv: pd.DataFrame, B: int = 1000, seed: int = 12345) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for (mod, me, h, smp), g in iv.groupby(["model", "method", "h", "sample"]):
        for u, gu in g.groupby("unit"):
            rows.append(dict(model=mod, method=me, h=h, sample=smp, unit=u, n=len(gu),
                             coverage=gu.covered.mean(), mean_width=gu.width.mean(),
                             winkler=gu.winkler.mean(), n_nonoverlap=len(gu) // h))
        s, c, _ = month_sums(g, "covered")
        bs = boot_ratio(s, c, block_len_for(h), B, rng) if len(s) > 1 else np.array([np.nan])
        units = rows[-g["unit"].nunique():]
        rows.append(dict(model=mod, method=me, h=h, sample=smp, unit="ALL", n=len(g),
                         coverage=g.covered.mean(), mean_width=g.width.mean(), winkler=g.winkler.mean(),
                         n_nonoverlap=sum(r["n_nonoverlap"] for r in units),
                         cov_lo=np.nanquantile(bs, 0.025), cov_hi=np.nanquantile(bs, 0.975),
                         mean_width_country_avg=float(np.mean([r["mean_width"] for r in units]))))
    return pd.DataFrame(rows)


def paired_panel(iv: pd.DataFrame, model: str, h: int, a: str, b: str, sample: str | None = None):
    """Per-cell difference of coverage indicators method a minus method b (same unit, origin)."""
    g = iv[(iv.model == model) & (iv.h == h)]
    if sample:
        g = g[g["sample"] == sample]
    k = ["unit", "origin"]
    x = g[g.method == a][k + ["covered"]].merge(g[g.method == b][k + ["covered"]], on=k, suffixes=("_a", "_b"))
    x["d"] = x["covered_a"] - x["covered_b"]
    return x


def contrast_test(panel: pd.DataFrame, h: int, B: int = 2000, seed: int = 12345) -> dict:
    if panel.empty:
        return dict(n=0, diff=np.nan, ci_lo=np.nan, ci_hi=np.nan, p=np.nan)
    s, c, _ = month_sums(panel, "d")
    est = s.sum() / c.sum()
    rng = np.random.default_rng(seed)
    bs = boot_ratio(s, c, block_len_for(h), B, rng)
    p = (1 + np.sum(np.abs(bs - est) >= abs(est))) / (B + 1)
    return dict(n=int(c.sum()), diff=est, ci_lo=np.quantile(bs, 0.025), ci_hi=np.quantile(bs, 0.975), p=p)


def holm(pvals: list[float]) -> list[float]:
    p = np.array(pvals, float)
    order = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    run = 0.0
    for r, i in enumerate(order):
        run = max(run, (m - r) * p[i])
        adj[i] = min(run, 1.0)
    return adj.tolist()


PRIMARY = [("aci", "split"), ("dracp", "aci")]


def primary_contrasts(iv: pd.DataFrame, model: str, sample: str | None = "exploratory",
                      B: int = 2000, seed: int = 12345) -> pd.DataFrame:
    rows = []
    for h in (3, 6):
        for a, b in PRIMARY:
            r = contrast_test(paired_panel(iv, model, h, a, b, sample), h, B, seed)
            rows.append(dict(model=model, h=h, contrast=f"{a}-{b}", sample=sample, **r))
    df = pd.DataFrame(rows)
    if df["p"].notna().all():
        df["p_holm"] = holm(df["p"].tolist())
    else:
        df["p_holm"] = np.nan
    return df


# ----------------------------------------------------------------------------- stress deciles
def coverage_by_stress_decile(iv: pd.DataFrame, model: str, h: int) -> pd.DataFrame:
    """Within-unit percentile rank of FX stress at the forecast origin -> deciles 1..10."""
    g = iv[(iv.model == model) & (iv.h == h)].dropna(subset=["stress"]).copy()
    if g.empty:
        return pd.DataFrame()
    first = g[g.method == g.method.iloc[0]][["unit", "origin", "stress"]]
    first["pct"] = first.groupby("unit")["stress"].rank(pct=True)
    first["decile"] = np.minimum(9, np.floor(first["pct"] * 10 - 1e-9)).astype(int) + 1
    g = g.merge(first[["unit", "origin", "decile"]], on=["unit", "origin"])
    out = g.groupby(["method", "decile"]).agg(n=("covered", "size"), coverage=("covered", "mean"),
                                               mean_width=("width", "mean")).reset_index()
    out.insert(0, "h", h)
    out.insert(0, "model", model)
    return out
