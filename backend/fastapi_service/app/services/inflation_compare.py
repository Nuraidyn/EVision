"""Live rolling-origin comparison of three interval methods for one country and horizon.

Methods (all on the same point forecast and the same origins, outcome of origin s revealed
only at origin s + h, absolute residuals as scores):

* ``split``   one-shot calibration: the first ``warmup`` revealed residuals, then frozen
* ``rolling`` rolling-window conformal: quantile of the last ``window`` revealed residuals
* ``aci``     adaptive conformal inference: the existing ``aci_backtest`` (unchanged)

``warmup`` is the number of revealed residuals needed before the first interval (default 48, as in
the thesis; the older calibrated-forecast endpoint uses 30, which is ``MIN_CAL``). With
``warmup=MIN_CAL`` the ACI numbers equal those of ``/inflation/calibrated-forecast``.
"""
from __future__ import annotations

import math

import numpy as np

from app.services.inflation_calibration import (
    CAL_WINDOW,
    COUNTRY_NAMES,
    GAMMA,
    HORIZONS,
    MIN_CAL,
    InflationError,
    _conformal_quantile,
    aci_backtest,
    build_targets,
    int_to_month,
    load_cpi,
    point_forecasts,
)

DEFAULT_WARMUP = 48
ROLLING_COV_WINDOW = 24  # origins in the running-coverage curve
METHODS = ("split", "rolling", "aci")


def static_backtest(
    origins: list[int],
    points: dict[int, float],
    targets: dict[int, float],
    h: int,
    alpha: float,
    mode: str,
    window: int = CAL_WINDOW,
    warmup: int = DEFAULT_WARMUP,
) -> tuple[list[int], list[float], list[float], list[bool]]:
    """Split ('split') or rolling-window ('rolling') conformal with delayed feedback.

    Same revealing rule as ``aci_backtest``: at origin t only origins s <= t - h are revealed.
    Returns (origins with interval and observed target, lower, upper, covered).
    """
    if mode not in ("split", "rolling"):
        raise ValueError(mode)
    scores: list[float] = []
    frozen: np.ndarray | None = None
    pending = [s for s in origins if s in points]
    ptr = 0
    o_out: list[int] = []
    lo_out: list[float] = []
    hi_out: list[float] = []
    cov_out: list[bool] = []
    for t in origins:
        if t not in points:
            continue
        while ptr < len(pending) and pending[ptr] <= t - h:
            s = pending[ptr]
            ptr += 1
            if s in targets:
                scores.append(abs(targets[s] - points[s]))
        if len(scores) < warmup:
            continue
        if mode == "split":
            if frozen is None:
                frozen = np.asarray(scores[:warmup], dtype=float)
            cal = frozen
        else:
            cal = np.asarray(scores[-window:], dtype=float)
        q = _conformal_quantile(cal, alpha)
        lo, hi = points[t] - q, points[t] + q
        if t in targets:
            o_out.append(t)
            lo_out.append(lo)
            hi_out.append(hi)
            cov_out.append(lo <= targets[t] <= hi)
    return o_out, lo_out, hi_out, cov_out


def _summarize(origins, lower, upper, covered, points, targets, h, level, n_last, max_points):
    n = len(covered)
    cov = float(np.mean(covered)) if n else None
    widths = [u - l for l, u in zip(lower, upper)]
    # running coverage over the last ROLLING_COV_WINDOW origins (computed before down-sampling)
    cov_arr = np.asarray(covered, dtype=float)
    series = []
    start = max(0, n - n_last)
    idx = list(range(start, n))
    stride = max(1, math.ceil(len(idx) / max_points))
    keep = idx[::-1][::stride][::-1]  # always keep the latest origin
    for i in keep:
        lo_i = max(0, i - ROLLING_COV_WINDOW + 1)
        series.append(
            {
                "origin": int_to_month(origins[i]),
                "date": int_to_month(origins[i] + h),
                "point": float(points[origins[i]]),
                "lower": float(lower[i]),
                "upper": float(upper[i]),
                "actual": float(targets[origins[i]]),
                "covered": bool(covered[i]),
                "running_coverage": float(cov_arr[lo_i : i + 1].mean()),
            }
        )
    return {
        "coverage": cov,
        "calibration_error": abs(cov - level) if cov is not None else None,
        "mean_width": float(np.mean(widths)) if widths else None,
        "n_eval": n,
        "series": series,
    }


def compare_methods(
    country: str,
    horizon: int,
    level: float = 0.9,
    warmup: int = DEFAULT_WARMUP,
    n_last: int = 120,
    max_points: int = 60,
    path: str | None = None,
) -> dict:
    code = country.upper()
    if code not in COUNTRY_NAMES:
        raise InflationError(f"Unknown country '{country}'")
    if horizon not in HORIZONS:
        raise InflationError(f"horizon must be one of {list(HORIZONS)}")
    if not (0.0 < level < 1.0):
        raise InflationError("level must be strictly between 0 and 1")
    if not (10 <= warmup <= CAL_WINDOW):
        raise InflationError(f"warmup must be between 10 and {CAL_WINDOW}")
    if not (10 <= n_last <= 400) or not (10 <= max_points <= 400):
        raise InflationError("n_last and max_points must be between 10 and 400")
    cpi = load_cpi(code, path)
    if not cpi:
        raise InflationError(f"No CPI data for '{code}'")

    alpha = 1.0 - level
    targets = build_targets(cpi, horizon)
    points = point_forecasts(cpi, horizon)
    origins = sorted(points)

    res = aci_backtest(origins, points, targets, horizon, alpha, min_cal=warmup)
    runs = {
        "aci": (res.origins, res.lower, res.upper, res.covered),
        "split": static_backtest(origins, points, targets, horizon, alpha, "split", warmup=warmup),
        "rolling": static_backtest(origins, points, targets, horizon, alpha, "rolling", warmup=warmup),
    }
    if not res.covered:
        raise InflationError(
            f"Not enough history to backtest '{code}' at horizon {horizon} with warmup {warmup}"
        )
    methods = {
        m: _summarize(*runs[m], points, targets, horizon, level, n_last, max_points) for m in METHODS
    }
    return {
        "country": code,
        "horizon": horizon,
        "level": level,
        "warmup": warmup,
        "window": CAL_WINDOW,
        "gamma": GAMMA,
        "as_of": int_to_month(max(cpi)),
        "first_origin": int_to_month(res.origins[0]),
        "n_eval": len(res.covered),
        "methods": methods,
        "notes": [
            "Rolling-origin backtest with delayed feedback: the outcome of an origin is revealed "
            f"{horizon} month(s) later. Warm-up = {warmup} revealed residuals before the first interval "
            f"(thesis default 48; the forecast page uses {MIN_CAL}).",
            "Point forecast: horizon x EWMA(0.2) of past monthly log growth, the same for all methods.",
            "A 90% interval should contain the outcome about 9 times in 10; calibration error is the "
            "absolute gap between measured coverage and the nominal level.",
            "Descriptive single-country backtest; it is not a test of which method is better.",
        ],
    }
