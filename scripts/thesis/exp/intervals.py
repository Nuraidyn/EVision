"""Conformal / adaptive interval wrappers on top of point forecasts.

All six methods run through the released ``dracp`` streaming API (fit / predict_one / update_one)
with a *pass-through* base model: the first column of the feature matrix X is the point forecast
produced by our own forecaster, so the "model" that dracp sees is the identity on column 0.
The remaining columns are extra features that only DRACP uses (regimes, scale model).

Multi-step feedback (delayed release)
-------------------------------------
The stream is indexed by consecutive forecast origins k = 0..n-1 (one per month). The target of
origin j is observed at month j+h, so when predicting origin k the outcome of j is available iff
j + h <= k.  ``run_method`` therefore calls ``update_one(x_j, y_j, result_j)`` for j only when
k >= j + h (h-1 rows later than in the h=1 case); the result dict stored at prediction time is
passed back, so the miss indicator that drives ACI/PID/DRACP is the miss of the interval that was
actually issued.  ``on_release`` lets tests assert this.

Warm-up: rows [0, n_cal) are the initial calibration set.  The first evaluated origin is
e = n_cal + h - 1 (all rows of the calibration set have been released by then).  Rows
n_cal..e-1 get no interval and no feedback (documented loss of h-1 rows).
DRACP uses the first half of the warm-up rows as "train" (scale/regime models) and the second
half as calibration; the other methods use all n_cal rows as calibration scores.

Infinite radii (too few scores for the requested level) are capped at ``cap_mult`` times the
largest absolute calibration score seen so far; ``n_capped`` is returned.
"""
from __future__ import annotations

import warnings

import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin

from dracp import (AdaptiveConformalRegressor, ConformalPIDRegressor, DRACPConfig,
                   DRACPRegressor, FACIRegressor, RollingConformalRegressor,
                   SplitConformalRegressor)
from dracp.quantiles import ordinary_conformal_quantile

METHODS = ["split", "rolling", "aci", "faci", "pid", "dracp"]
ALPHA = 0.10
WINDOW = 120
ACI_STEP = 0.02
DRACP_CFG = dict(calibration_window=120, target_window=24, temporal_decay=0.985,
                 bandwidth=2.0, adaptive_bandwidth=True, bandwidth_grid=[0.5, 1.0, 2.0, 4.0],
                 min_ess=20, max_weight=0.30, ratio_clip_min=0.1, ratio_clip_max=10.0,
                 n_regimes=3, regime_beta=1.0, alpha_step=0.02, fallback="global")
SEED = 42


class PassThrough(BaseEstimator, RegressorMixin):
    """Identity on column 0: the point forecast is supplied by our forecasters."""

    def fit(self, X, y=None):
        return self

    def predict(self, X):
        return np.asarray(X, float)[:, 0]


def make_method(name: str, alpha: float = ALPHA, window: int = WINDOW):
    base = PassThrough()
    if name == "split":
        return SplitConformalRegressor(alpha, base)
    if name == "rolling":
        return RollingConformalRegressor(alpha, window, base)
    if name == "aci":
        return AdaptiveConformalRegressor(alpha, window, ACI_STEP, base)
    if name == "faci":
        return FACIRegressor(alpha, window, model=base)
    if name == "pid":
        return ConformalPIDRegressor(alpha, window, model=base)
    if name == "dracp":
        cfg = DRACPConfig(alpha=alpha, random_state=SEED, **{**DRACP_CFG, "use_faci_control": True})
        return DRACPRegressor(cfg, base_model=base)
    raise ValueError(name)


class OwnACI:
    """Independent re-implementation of ACI (Gibbs & Candes 2021) on absolute residuals with a
    rolling window, used only to cross-check the package (tests/test_intervals.py)."""

    def __init__(self, alpha=ALPHA, window=WINDOW, step=ACI_STEP):
        self.alpha, self.window, self.step = alpha, window, step

    def fit(self, scores):
        self.scores = list(np.asarray(scores, float))
        self.a_t = self.alpha
        return self

    def predict_radius(self):
        a = min(max(self.a_t, 1e-6), 1 - 1e-6)
        return ordinary_conformal_quantile(np.array(self.scores), a)

    def update(self, point, y, lo, hi):
        err = int(not (lo <= y <= hi))
        self.scores = (self.scores + [abs(y - point)])[-self.window:]
        self.a_t += self.step * (self.alpha - err)


def _finite(res, cap):
    """Replace infinite bounds by a capped radius; returns (lo, hi, capped)."""
    p, lo, hi = res["prediction"], res["lower"], res["upper"]
    if np.isfinite(lo) and np.isfinite(hi):
        return lo, hi, False
    return p - cap, p + cap, True


def run_method(method: str, X: np.ndarray, y: np.ndarray, h: int, n_cal: int,
               alpha: float = ALPHA, window: int = WINDOW, cap_mult: float = 10.0,
               on_release=None, instant_feedback: bool = False):
    """Run one interval method over a stream of origins.

    X : (n, d) features, column 0 = point forecast.  y : (n,) realised target of each origin
    (entry j is only READ once k >= j + h).  Returns dict(lo, hi, n_capped) with NaN for
    rows k < e = n_cal + h - 1.

    instant_feedback (DIAGNOSTIC ONLY): the outcome of origin j is released at k = j + 1 as if the
    horizon were 1, although in reality it is only observable at j + h.  Used to isolate the effect
    of delayed feedback; never a valid forecasting setup.
    """
    n = len(y)
    e = n_cal + h - 1
    lo = np.full(n, np.nan)
    hi = np.full(n, np.nan)
    if n <= e:
        return dict(lo=lo, hi=hi, n_capped=0)
    m = make_method(method, alpha, window)
    ntr = n_cal // 2 if method == "dracp" else n_cal
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if method == "dracp":
            m.fit(X[:ntr], y[:ntr], X[ntr:n_cal], y[ntr:n_cal])
        else:
            m.fit(X[:n_cal], y[:n_cal], X[:n_cal], y[:n_cal])
    cap = cap_mult * float(np.max(np.abs(y[:n_cal] - X[:n_cal, 0])))
    results = {}
    next_release = e  # first stream row whose outcome has not yet been fed back
    n_capped = 0
    lag = 1 if instant_feedback else h
    for k in range(e, n):
        while next_release + lag <= k:             # outcome of next_release is observable at origin k
            j = next_release
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m.update_one(X[j], float(y[j]), results[j])
            cap = max(cap, cap_mult * abs(float(y[j]) - X[j, 0]))
            if on_release:
                on_release(k, j)
            del results[j]
            next_release += 1
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = m.predict_one(X[k])
        l, u, capped = _finite(r, cap)
        n_capped += capped
        r = dict(r, lower=l, upper=u)
        results[k] = r
        lo[k], hi[k] = l, u
    return dict(lo=lo, hi=hi, n_capped=n_capped)
