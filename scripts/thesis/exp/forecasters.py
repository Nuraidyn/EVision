"""Point forecasters (and model-native intervals) for the cumulative h-month log growth.

Common interface
----------------
``fc.forecast(frame, pos, horizons) -> {h: (point, lo, hi)}`` where ``lo``/``hi`` are model-native
90% bounds or ``None``.  ONLY rows ``frame.iloc[:pos+1]`` may be read, and target columns
``y{h}`` only for rows s with s + h <= pos (the outcome is already observable at origin pos).
tests/test_no_lookahead.py checks this by corrupting everything after ``pos``.

Everything is refitted on an expanding window.  Hyperparameters are FIXED here (not tuned):
 * ETS      : additive error, no trend, additive seasonal (period 12), on monthly inflation m.
 * ARIMA    : ARMA(p,q), p,q in {0,1,2}, constant + 2 annual harmonics as exog (the same
              seasonal setting for every country); order chosen by AICc, re-selected every
              ``select_every`` origins, parameters re-estimated at every origin.
 * LightGBM : direct, one model per horizon, 200 trees, lr .05, 8 leaves; refit every
              ``refit_every`` origins.  Features = FEATURE_COLS (NaN allowed).
Point forecast of the h-step cumulative growth for ETS/ARIMA = sum of the h monthly forecasts.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy.stats import norm

from .data import FEATURE_COLS

Z90 = float(norm.ppf(0.95))


class Forecaster:
    name = "base"
    native_intervals = False

    def forecast(self, frame: pd.DataFrame, pos: int, horizons) -> dict:
        raise NotImplementedError


class NaiveA(Forecaster):
    """h times the last observed monthly inflation rate."""
    name = "naive_a"

    def forecast(self, frame, pos, horizons):
        m = float(frame["m0"].iloc[pos])
        return {h: (h * m, None, None) for h in horizons}


class NaiveB(Forecaster):
    """Last observed cumulative h-month growth (equals YoY growth at h = 12)."""
    name = "naive_b"

    def forecast(self, frame, pos, horizons):
        lc = np.log(frame["cpi"].iloc[: pos + 1].values)
        out = {}
        for h in horizons:
            out[h] = (float(100 * (lc[pos] - lc[pos - h])) if pos - h >= 0 else np.nan, None, None)
        return out


def _monthly(frame, pos):
    m = frame["m0"].iloc[1: pos + 1].astype(float)
    return m.values, frame.index[1: pos + 1]


class ETS(Forecaster):
    name = "ets"
    native_intervals = True

    def __init__(self, reps: int = 400):
        self.reps = reps

    def forecast(self, frame, pos, horizons):
        from statsmodels.tsa.exponential_smoothing.ets import ETSModel
        y, _ = _monthly(frame, pos)
        H = max(horizons)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                res = ETSModel(y, error="add", trend=None, seasonal="add", seasonal_periods=12,
                               initialization_method="heuristic").fit(disp=False, maxiter=200)
                mean = np.asarray(res.forecast(H))
                sims = np.asarray(res.simulate(nsimulations=H, repetitions=self.reps,
                                               anchor="end", rng=np.random.default_rng(pos)))
            cs = np.cumsum(sims, axis=0)
            out = {}
            for h in horizons:
                lo, hi = np.quantile(cs[h - 1], [0.05, 0.95])
                out[h] = (float(mean[:h].sum()), float(lo), float(hi))
            return out
        except Exception:
            return {h: (np.nan, None, None) for h in horizons}


def _aicc(res, n):
    k = len(res.params)
    return res.aic + 2 * k * (k + 1) / max(n - k - 1, 1)


def _harmonics(months):
    a = 2 * np.pi * np.asarray(months) / 12
    return np.column_stack([np.sin(a), np.cos(a), np.sin(2 * a), np.cos(2 * a)])


class ARIMA(Forecaster):
    name = "arima"
    native_intervals = True
    GRID = [(p, q) for p in (0, 1, 2) for q in (0, 1, 2)]

    def __init__(self, select_every: int = 12):
        self.select_every = select_every
        self._order = {}     # id(frame) -> (pos_selected, order)

    def _fit(self, y, X, order):
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return SARIMAX(y, exog=X, order=(order[0], 0, order[1]), trend="c",
                           enforce_stationarity=True, enforce_invertibility=True).fit(disp=False, maxiter=100)

    def forecast(self, frame, pos, horizons):
        from statsmodels.tsa.arima_process import arma2ma
        y, idx = _monthly(frame, pos)
        X = _harmonics(idx.month.values)
        H = max(horizons)
        fut_months = ((idx[-1].month - 1 + np.arange(1, H + 1)) % 12) + 1
        Xf = _harmonics(fut_months)
        key = id(frame)
        sel = self._order.get(key)
        try:
            if sel is None or pos - sel[0] >= self.select_every or pos < sel[0]:
                best = None
                for order in self.GRID:
                    try:
                        r = self._fit(y, X, order)
                    except Exception:
                        continue
                    a = _aicc(r, len(y))
                    if np.isfinite(a) and (best is None or a < best[0]):
                        best = (a, order, r)
                if best is None:
                    raise RuntimeError("no ARIMA fit")
                self._order[key] = (pos, best[1])
                res, order = best[2], best[1]
            else:
                order = sel[1]
                res = self._fit(y, X, order)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                mean = np.asarray(res.forecast(H, exog=Xf))
            par = dict(zip(list(res.param_names), np.asarray(res.params)))
            ar = np.r_[1.0, -np.array([par[f"ar.L{i}"] for i in range(1, order[0] + 1)])]
            ma = np.r_[1.0, np.array([par[f"ma.L{i}"] for i in range(1, order[1] + 1)])]
            Psi = np.cumsum(arma2ma(ar, ma, H))
            s2 = par["sigma2"]
            out = {}
            for h in horizons:
                pt = float(mean[:h].sum())
                sd = float(np.sqrt(s2 * np.sum(Psi[:h] ** 2)))   # sd of the h-step cumulative error
                out[h] = (pt, pt - Z90 * sd, pt + Z90 * sd)
            return out
        except Exception:
            return {h: (np.nan, None, None) for h in horizons}


class LGBM(Forecaster):
    name = "lgbm"
    PARAMS = dict(n_estimators=200, learning_rate=0.05, num_leaves=8, min_child_samples=20,
                  subsample=0.8, subsample_freq=1, colsample_bytree=0.8, random_state=42,
                  verbose=-1, n_jobs=1)

    def __init__(self, refit_every: int = 3, min_rows: int = 36):
        self.refit_every = refit_every
        self.min_rows = min_rows
        self._models = {}   # (id(frame), h) -> (pos_fit, model)

    def forecast(self, frame, pos, horizons):
        import lightgbm as lgb
        X = frame[FEATURE_COLS]
        out = {}
        for h in horizons:
            key = (id(frame), h)
            cached = self._models.get(key)
            if cached is None or pos - cached[0] >= self.refit_every or pos < cached[0]:
                last = pos - h                    # rows s <= pos-h have observable y{h}
                if last < 0:
                    out[h] = (np.nan, None, None)
                    continue
                Xtr = X.iloc[: last + 1]
                ytr = frame[f"y{h}"].iloc[: last + 1]
                ok = ytr.notna().values & Xtr["m11"].notna().values   # drop rows without 12 lags
                if ok.sum() < self.min_rows:
                    out[h] = (np.nan, None, None)
                    continue
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    mdl = lgb.LGBMRegressor(**self.PARAMS).fit(Xtr.values[ok], ytr.values[ok])
                cached = (pos, mdl)
                self._models[key] = cached
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                out[h] = (float(cached[1].predict(X.iloc[[pos]].values)[0]), None, None)
        return out


CHRONOS_MODEL_ID = "amazon/chronos-bolt-tiny"   # smallest of the Bolt family that installs (tiny, mini, small tried in this order)
CHRONOS_FALLBACK_ID = "amazon/chronos-t5-small"
CHRONOS_MAX_CONTEXT = 2048                      # context_length of the Bolt models
CHRONOS_SEEN_BEFORE = pd.Period("2025-01", "M")  # target months before this are flagged possibly_seen


class Chronos(Forecaster):
    """Zero-shot Chronos(-Bolt) on the monthly inflation series 100*ln(CPI_t/CPI_{t-1}).

    Point forecast of the cumulative h-month growth = sum of the h median (0.5-quantile) forecasts.
    No native interval.  Chronos-Bolt is a direct quantile model: no sampling, so it is deterministic
    (seeds are set anyway).  Only m0 of rows 1..pos is read.  ``prepare`` batches many origins at once;
    each origin's context is still its own history, left-padded with NaN (masked by the model).
    """
    name = "chronos"
    model_id = CHRONOS_MODEL_ID

    def __init__(self, pipeline=None, model_id: str | None = None, batch_size: int = 64,
                 max_context: int = CHRONOS_MAX_CONTEXT, seed: int = 0):
        self._pipe = pipeline
        if model_id:
            self.model_id = model_id
        self.batch_size = batch_size
        self.max_context = max_context
        self.seed = seed
        self._cache = {}     # (id(frame), pos) -> median path (np.ndarray, len >= H prepared)
        self.seconds = 0.0
        self.n_forecasts = 0

    def _pipeline(self):
        if self._pipe is None:
            import torch
            from chronos import BaseChronosPipeline
            torch.manual_seed(self.seed)
            self._pipe = BaseChronosPipeline.from_pretrained(self.model_id, device_map="cpu",
                                                             torch_dtype=torch.float32)
        return self._pipe

    def _medians(self, contexts, H):
        import time
        import torch
        torch.manual_seed(self.seed)
        t0 = time.time()
        out = []
        pipe = self._pipeline()
        for i in range(0, len(contexts), self.batch_size):
            ctx = [torch.as_tensor(np.asarray(c, dtype=np.float32)) for c in contexts[i: i + self.batch_size]]
            q, _ = pipe.predict_quantiles(ctx, prediction_length=H, quantile_levels=[0.5])
            out.append(np.asarray(q)[:, :H, 0])
        self.seconds += time.time() - t0
        self.n_forecasts += len(contexts)
        return np.vstack(out)

    def _context(self, frame, pos):
        y, _ = _monthly(frame, pos)
        return y[-self.max_context:]

    def prepare(self, frame, positions, horizons):
        """Batch-forecast all ``positions`` (origins) for max(horizons) steps; reads rows <= each pos only."""
        H = max(horizons)
        todo = [p for p in positions if (id(frame), p) not in self._cache or len(self._cache[(id(frame), p)]) < H]
        if not todo:
            return
        med = self._medians([self._context(frame, p) for p in todo], H)
        for p, m in zip(todo, med):
            self._cache[(id(frame), p)] = m

    def forecast(self, frame, pos, horizons):
        H = max(horizons)
        key = (id(frame), pos)
        if key not in self._cache or len(self._cache[key]) < H:
            self.prepare(frame, [pos], horizons)
        m = self._cache[key]
        return {h: (float(np.sum(m[:h])), None, None) for h in horizons}


def make_forecasters(names, **kw) -> dict:
    reg = {"naive_a": lambda: NaiveA(), "naive_b": lambda: NaiveB(), "ets": lambda: ETS(),
           "arima": lambda: ARIMA(), "lgbm": lambda: LGBM(**kw.get("lgbm", {})),
           "chronos": lambda: Chronos(**kw.get("chronos", {}))}
    return {n: reg[n]() for n in names}
