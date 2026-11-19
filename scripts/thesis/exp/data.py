"""Data loading and feature construction.

Conventions
-----------
* A *row* t of a country frame is a forecast ORIGIN: everything in the feature columns uses
  information dated <= t only.  Targets y{h} are the only columns that look forward.
* Target: y{h}(t) = 100 * ln(CPI_{t+h} / CPI_t), NaN when CPI_{t+h} is not in the same
  consecutive stretch.
* Gaps (Russia): the CPI series is cut into maximal runs of consecutive months ("stretches");
  every stretch is a separate evaluation unit named e.g. ``RU#2``.  Nothing is imputed.
* Stress (secondary analysis) replicates scripts/thesis/common.mjs exactly: z-score of the FX
  one-month log change over the preceding 60 *listed* observations (median/MAD, MAD floor 0.005),
  stress(t) = max |z| over t-3..t (available values only).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data"
COUNTRIES = ["KZ", "RU", "AZ", "UZ", "CO", "CL", "PE", "BR", "MX", "NG", "MN", "ID", "ZA"]
HORIZONS = (1, 3, 6, 12)
CONFIRMATORY_START = pd.Period("2025-07", "M")   # target months >= this are confirmatory
FEATURE_COLS = ["m0", "m1", "m2", "m5", "m11", "roll3", "roll12",
                "fx0", "fx1", "br0", "br1", "msin", "mcos"]


def _to_series(d: dict) -> pd.Series:
    s = pd.Series({pd.Period(k, "M"): float(v) for k, v in d.items() if v is not None})
    return s.sort_index()


# First month of a CPI methodology change by the national statistics office. A level chained
# across such a break is not comparable, so months from here on are not appended (the series
# of that country ends the month before). Nigeria: 2025-01 (see docs/thesis/experiment-protocol.md).
METHOD_BREAKS = {"NG": pd.Period("2025-01", "M")}


def chain_cpi(country: str, old: pd.Series, new: pd.Series) -> pd.Series:
    """Append the months of ``new`` that ``old`` lacks, rescaled at their last common month.

    The two IMF snapshots use different index bases (a constant factor, e.g. 0.477 for KZ and
    0.131 for NG), so the level is chained where both exist; growth rates are untouched. The
    earlier snapshot wins on overlap. Months at or after a known methodology break are dropped.
    """
    common = old.index.intersection(new.index)
    if len(common) == 0:
        return old
    m = common.max()
    factor = old[m] / new[m]
    extra = new[~new.index.isin(old.index)]
    brk = METHOD_BREAKS.get(country)
    if brk is not None:
        extra = extra[extra.index < brk]
    return pd.concat([old, extra * factor]).sort_index()


def load_raw(data_dir: Path | str | None = None) -> dict:
    """Load snapshot and (if present) confirmatory.json.  Snapshot values win on overlap."""
    data_dir = Path(data_dir) if data_dir else DATA_DIR
    files = [data_dir / "snapshot.json", data_dir / "confirmatory.json"]
    raw = {"cpi": {}, "fx": {}, "brent": None, "files": []}
    for f in files:
        if not f.exists():
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        raw["files"].append(f.name)
        for key in ("cpi", "fx"):
            for c, v in d.get(key, {}).items():
                new = _to_series(v)
                old = raw[key].get(c)
                if old is None:
                    raw[key][c] = new
                elif key == "cpi":
                    raw[key][c] = chain_cpi(c, old, new)
                else:
                    raw[key][c] = old.combine_first(new)  # earlier file wins; FX levels are identical
        if d.get("brent"):
            new = _to_series(d["brent"])
            raw["brent"] = new if raw["brent"] is None else raw["brent"].combine_first(new)
    if not raw["files"]:
        raise FileNotFoundError(f"no snapshot.json in {data_dir}")
    return raw


def stretches(index: pd.PeriodIndex) -> list[tuple[pd.Period, pd.Period]]:
    """Maximal runs of consecutive months."""
    out, start, prev = [], None, None
    for p in index:
        if start is None:
            start = prev = p
        elif (p - prev).n == 1:
            prev = p
        else:
            out.append((start, prev))
            start = prev = p
    if start is not None:
        out.append((start, prev))
    return out


def fx_z_scores(fx: pd.Series, floor: float = 0.005, lookback: int = 60) -> pd.Series:
    """Causal robust z of the FX 1-month log change; mirrors zScores() in common.mjs
    (differences are taken between consecutive LISTED observations, as in the JS code)."""
    fx = fx[fx > 0].sort_index()
    d = np.log(fx.values[1:] / fx.values[:-1])
    periods = fx.index[1:]
    z = {}
    for i in range(lookback, len(d)):
        w = d[i - lookback:i]
        m = np.median(w)
        s = max(1.4826 * np.median(np.abs(w - m)), floor)
        z[periods[i]] = (d[i] - m) / s
    return pd.Series(z, dtype=float)


def stress_series(fx: pd.Series | None, index: pd.PeriodIndex) -> pd.Series:
    """stress(t) = max |z| over t-3..t, using only z values that exist; NaN if none."""
    out = pd.Series(np.nan, index=index)
    if fx is None or len(fx) == 0:
        return out
    az = fx_z_scores(fx).abs()
    if az.empty:
        return out
    full = az.reindex(pd.period_range(az.index.min() - 3, max(az.index.max(), index.max()), freq="M"))
    st = pd.concat([full.shift(k) for k in range(4)], axis=1).max(axis=1)  # NaN-skipping max
    return st.reindex(index)


def build_frame(cpi: pd.Series, fx: pd.Series | None, brent: pd.Series | None,
                horizons=HORIZONS) -> pd.DataFrame:
    """Frame for ONE consecutive stretch of CPI (index must be consecutive months)."""
    cpi = cpi.sort_index()
    idx = cpi.index
    assert len(idx) == 0 or (idx[-1] - idx[0]).n == len(idx) - 1, "CPI stretch is not consecutive"
    lc = np.log(cpi)
    df = pd.DataFrame(index=idx)
    df["cpi"] = cpi
    df["m0"] = 100 * lc.diff()
    for k in (1, 2, 5, 11):
        df[f"m{k}"] = df["m0"].shift(k)
    df["roll3"] = df["m0"].rolling(3).mean()
    df["roll12"] = df["m0"].rolling(12).mean()
    for name, ser in (("fx", fx), ("br", brent)):
        if ser is None:
            d = pd.Series(np.nan, index=idx)
        else:
            full = ser.reindex(pd.period_range(min(ser.index.min(), idx.min()), max(ser.index.max(), idx.max()), freq="M"))
            d = np.log(full).diff().reindex(idx)          # NaN if either month missing
        df[f"{name}0"] = d
        df[f"{name}1"] = d.shift(1)
    mon = idx.month.values
    df["msin"] = np.sin(2 * np.pi * mon / 12)
    df["mcos"] = np.cos(2 * np.pi * mon / 12)
    for h in horizons:
        df[f"y{h}"] = 100 * (lc.shift(-h) - lc)
    df["stress"] = stress_series(fx, idx)
    return df


def country_units(raw: dict, country: str, min_len: int = 60, horizons=HORIZONS, start: str | None = None) -> dict[str, pd.DataFrame]:
    """One frame per consecutive stretch with at least ``min_len`` months. Keys: 'KZ' or 'RU#2'."""
    cpi = raw["cpi"][country]
    if start:
        cpi = cpi[cpi.index >= pd.Period(start, "M")]   # optional common start date (e.g. drop hyperinflation era)
    runs = [r for r in stretches(cpi.index) if (r[1] - r[0]).n + 1 >= min_len]
    units = {}
    for i, (a, b) in enumerate(runs, 1):
        name = country if len(runs) == 1 else f"{country}#{i}"
        fr = build_frame(cpi.loc[a:b], raw["fx"].get(country), raw["brent"], horizons)
        # stress should see the whole FX history, not only this stretch (already the case)
        fr.attrs["country"] = country
        units[name] = fr
    return units


def load_holdout(path: Path | str | None = None, data_dir: Path | str | None = None) -> dict:
    """Hold-out panel: CPI and FX per country from holdout.json, Brent from the main snapshot files
    (the hold-out file's own brent, if any, is ignored).  Same structure as load_raw."""
    path = Path(path) if path else DATA_DIR / "holdout.json"
    raw = load_raw(data_dir)
    d = json.loads(path.read_text(encoding="utf-8"))
    return {"cpi": {c: _to_series(v) for c, v in d["cpi"].items()},
            "fx": {c: _to_series(v) for c, v in d["fx"].items()},
            "brent": raw["brent"], "files": [path.name] + raw["files"]}


def sample_label(target_month: pd.Period) -> str:
    return "confirmatory" if target_month >= CONFIRMATORY_START else "exploratory"
