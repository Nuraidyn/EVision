"""Calibrated prediction intervals for monthly inflation (adaptive conformal inference).

Offline and deterministic: reads monthly CPI from a JSON snapshot
(``{"cpi": {country: {"YYYY-MM": index}}}``). Target at origin t and horizon h is the
cumulative log growth ``y = 100 * ln(CPI_{t+h} / CPI_t)``. The point forecast is
``h * EWMA`` of past monthly log growth; intervals use ACI (Gibbs & Candes, 2021) on
absolute residuals over a rolling calibration window, with delayed feedback: the outcome
of an origin becomes available only h months later.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

from app.core.config import INFLATION_CONFIRMATORY_PATH, INFLATION_SNAPSHOT_PATH

COUNTRY_NAMES = {
    "KZ": "Kazakhstan",
    "RU": "Russia",
    "AZ": "Azerbaijan",
    "UZ": "Uzbekistan",
    "CO": "Colombia",
    "CL": "Chile",
    "PE": "Peru",
    "BR": "Brazil",
    "MX": "Mexico",
    "NG": "Nigeria",
    "MN": "Mongolia",
    "ID": "Indonesia",
    "ZA": "South Africa",
}
HORIZONS = (1, 3, 6, 12)
GAMMA = 0.02
CAL_WINDOW = 120
MIN_CAL = 30  # minimum revealed residuals before an interval is issued
MIN_GROWTHS = 12  # minimum monthly growth observations before forecasting
EWMA_LAMBDA = 0.2


# ----------------------------------------------------------------------------- data
def _month_to_int(label: str) -> int:
    year, month = label.split("-")
    return int(year) * 12 + int(month) - 1


def int_to_month(n: int) -> str:
    return f"{n // 12:04d}-{n % 12 + 1:02d}"


@lru_cache(maxsize=4)
def _load_snapshot(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh).get("cpi", {})


def _series(raw: dict, country: str) -> dict[int, float]:
    series = raw.get(country.upper(), {})
    return {_month_to_int(k): float(v) for k, v in series.items() if v is not None and float(v) > 0}


# Months from which the national statistics office changed the CPI methodology, so a level
# chained across the break is not comparable (see docs/thesis/experiment-protocol.md).
METHOD_BREAKS = {"NG": _month_to_int("2025-01")}


def _chain(country: str, base: dict[int, float], new: dict[int, float]) -> dict[int, float]:
    """Append months of ``new`` that are missing in ``base``, rescaled at the last overlap.

    The two snapshots use different index bases (a constant factor), so the level is chained at
    the latest month present in both; growth rates are unchanged. Months at or after a known
    methodology break are not appended.
    """
    overlap = sorted(set(base) & set(new))
    if not overlap:
        return base
    factor = base[overlap[-1]] / new[overlap[-1]]
    brk = METHOD_BREAKS.get(country.upper())
    out = dict(base)
    for t, v in new.items():
        if t in base or (brk is not None and t >= brk):
            continue
        out[t] = v * factor
    return out


def load_cpi(country: str, path: str | None = None, confirmatory_path: str | None = None) -> dict[int, float]:
    """Monthly CPI as {month_int: index} (positive values only).

    With the default ``path`` the later IMF snapshot is chained on (``confirmatory_path``, if the
    file exists). An explicit ``path`` is used alone unless ``confirmatory_path`` is also given.
    """
    code = country.upper()
    base = _series(_load_snapshot(str(Path(path or INFLATION_SNAPSHOT_PATH))), code)
    extra_path = confirmatory_path or (INFLATION_CONFIRMATORY_PATH if path is None else None)
    if extra_path and Path(extra_path).exists():
        base = _chain(code, base, _series(_load_snapshot(str(Path(extra_path))), code))
    return base


def list_countries(path: str | None = None) -> list[dict]:
    rows = []
    for code, name in COUNTRY_NAMES.items():
        cpi = load_cpi(code, path)
        if not cpi:
            continue
        rows.append(
            {
                "code": code,
                "name": name,
                "n_months": len(cpi),
                "first": int_to_month(min(cpi)),
                "last": int_to_month(max(cpi)),
            }
        )
    return rows


def build_targets(cpi: dict[int, float], h: int) -> dict[int, float]:
    """y_t = 100*ln(CPI_{t+h}/CPI_t) for every origin t where both months exist."""
    return {
        t: 100.0 * math.log(cpi[t + h] / cpi[t]) for t in cpi if (t + h) in cpi
    }


def point_forecasts(cpi: dict[int, float], h: int, lam: float = EWMA_LAMBDA) -> dict[int, float]:
    """Point forecast issued at origin t using only data up to t: h * EWMA(monthly growth)."""
    out: dict[int, float] = {}
    ewma = None
    n_growth = 0
    for t in range(min(cpi), max(cpi) + 1):
        if t in cpi and (t - 1) in cpi:
            g = 100.0 * math.log(cpi[t] / cpi[t - 1])
            ewma = g if ewma is None else lam * g + (1 - lam) * ewma
            n_growth += 1
        if t in cpi and ewma is not None and n_growth >= MIN_GROWTHS:
            out[t] = h * ewma
    return out


# ----------------------------------------------------------------------------- ACI
def _conformal_quantile(scores: np.ndarray, alpha: float) -> float:
    n = len(scores)
    level = 1.0 - alpha
    if level <= 0:
        return 0.0
    k = math.ceil((n + 1) * level)
    if k > n:
        # Finite-sample cap: the exact quantile is +inf; use the largest score so the
        # interval stays finite (JSON-safe). ACI then adapts alpha_t as usual.
        return float(np.max(scores))
    return float(np.partition(scores, k - 1)[k - 1])


@dataclass
class AciResult:
    origins: list[int]  # origins with an issued interval AND an observed target
    lower: list[float]
    upper: list[float]
    covered: list[bool]
    alpha_final: float
    last_origin: int | None  # last origin an interval was issued for
    last_interval: tuple[float, float] | None


def aci_backtest(
    origins: list[int],
    points: dict[int, float],
    targets: dict[int, float],
    h: int,
    alpha: float,
    gamma: float = GAMMA,
    window: int = CAL_WINDOW,
    min_cal: int = MIN_CAL,
) -> AciResult:
    """Rolling-origin ACI with delayed feedback (Gibbs & Candes, 2021).

    At origin t only origins s <= t - h are revealed (their target month s+h <= t is
    observed). Each revealed origin contributes its absolute residual to the rolling
    calibration set; if an interval had been issued for it, it also updates
    alpha_{t+1} = alpha_t + gamma * (alpha - err). ``targets`` is never read for s > t - h.
    """
    a_t = alpha
    scores: list[float] = []
    issued: dict[int, tuple[float, float]] = {}
    pending = [s for s in origins if s in points]  # chronological
    ptr = 0
    out_o: list[int] = []
    out_lo: list[float] = []
    out_hi: list[float] = []
    out_cov: list[bool] = []
    last_o = None
    last_iv = None

    for t in origins:
        if t not in points:
            continue
        while ptr < len(pending) and pending[ptr] <= t - h:
            s = pending[ptr]
            ptr += 1
            if s not in targets:
                continue
            y = targets[s]
            scores.append(abs(y - points[s]))
            if s in issued:
                lo, hi = issued[s]
                err = 0.0 if lo <= y <= hi else 1.0
                a_t += gamma * (alpha - err)
        cal = np.asarray(scores[-window:], dtype=float)
        if len(cal) < min_cal:
            continue
        q = _conformal_quantile(cal, a_t)
        lo, hi = points[t] - q, points[t] + q
        issued[t] = (lo, hi)
        last_o, last_iv = t, (lo, hi)
        if t in targets:
            out_o.append(t)
            out_lo.append(lo)
            out_hi.append(hi)
            out_cov.append(lo <= targets[t] <= hi)
    return AciResult(out_o, out_lo, out_hi, out_cov, a_t, last_o, last_iv)


# ----------------------------------------------------------------------------- API
class InflationError(ValueError):
    """Invalid request (unknown country, bad horizon or level)."""


def calibrated_forecast(country: str, horizon: int, level: float, path: str | None = None) -> dict:
    code = country.upper()
    if code not in COUNTRY_NAMES:
        raise InflationError(f"Unknown country '{country}'")
    if horizon not in HORIZONS:
        raise InflationError(f"horizon must be one of {list(HORIZONS)}")
    if not (0.0 < level < 1.0):
        raise InflationError("level must be strictly between 0 and 1")
    cpi = load_cpi(code, path)
    if not cpi:
        raise InflationError(f"No CPI data for '{code}'")

    alpha = 1.0 - level
    last = max(cpi)
    targets = build_targets(cpi, horizon)
    points = point_forecasts(cpi, horizon)
    res = aci_backtest(sorted(points), points, targets, horizon, alpha)
    if last not in points or res.last_origin != last or res.last_interval is None:
        raise InflationError(
            f"Not enough history to calibrate an interval for '{code}' at horizon {horizon}"
        )

    notes = [
        "Point forecast: horizon x EWMA(lambda=0.2) of past monthly log growth.",
        f"Intervals: adaptive conformal inference (gamma={GAMMA}, rolling calibration window "
        f"{CAL_WINDOW}); outcomes are revealed {horizon} month(s) after each origin.",
        "Forecast values are cumulative log growth in percent from the last observed month.",
    ]
    missing = (last - min(cpi) + 1) - len(cpi)
    if missing:
        notes.append(f"CPI history has {missing} missing month(s); gaps are skipped.")
    if code in METHOD_BREAKS:
        notes.append(
            f"The series ends at {int_to_month(METHOD_BREAKS[code] - 1)}: the statistics office "
            "changed the CPI methodology after that month, so later values are not chained."
        )

    lo, hi = res.last_interval
    n_eval = len(res.covered)
    widths = [u - l for l, u in zip(res.lower, res.upper)]
    return {
        "country": code,
        "horizon": horizon,
        "level": level,
        "method": "aci",
        "as_of": int_to_month(last),
        "history": [{"date": int_to_month(m), "value": cpi[m]} for m in sorted(cpi)[-60:]],
        "forecast": {
            "date": int_to_month(last + horizon),
            "point": float(points[last]),
            "lower": float(lo),
            "upper": float(hi),
        },
        "calibration": {
            "empirical_coverage": float(np.mean(res.covered)) if n_eval else None,
            "nominal": level,
            "n_eval": n_eval,
            "mean_width": float(np.mean(widths)) if widths else None,
        },
        "notes": notes,
    }
