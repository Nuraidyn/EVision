"""E3/E4 of docs/thesis/experiment-protocol.md (eighth entry): point accuracy of Chronos against
ARIMA, LightGBM and naive B on the target months that cannot have been seen in pretraining
(2025-01 onwards), pooled over the 30 countries of the three runs, with a paired moving-block
bootstrap over calendar months (months resampled jointly across countries).

Block length: 3 months (the clean sample has only 22 calendar months; the 12-month rule of the
calibration contrasts would leave at most one block). Reads existing outputs only.
Usage (from scripts/thesis): .venv/Scripts/python.exe -I extension_accuracy.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

RES = Path(__file__).resolve().parent / "results"
RUNS = ("holdout2_ncal48", "ext_design13", "ext_holdout1")
MODELS = ("chronos", "lgbm", "arima", "naive_b")
BLOCK, B, SEED, CUT = 3, 2000, 12345, "2025-01"


def load():
    parts = []
    for run in RUNS:
        p = pd.read_csv(RES / run / "points_all.csv", keep_default_na=False, na_values=[""],
                        usecols=["unit", "model", "h", "origin", "target", "y", "point"])
        p["ae"] = (p.y - p.point).abs()
        parts.append(p[p.model.isin(MODELS) & (p.target >= CUT)])
    return pd.concat(parts, ignore_index=True)


def main():
    P = load()
    months = sorted(P.target.unique())
    rng = np.random.default_rng(SEED)
    rows = []
    for h in (1, 3, 6, 12):
        x = P[P.h == h].pivot_table(index=["unit", "target"], columns="model", values="ae").dropna()
        x = x.reset_index()
        # per-month sums so that months can be resampled jointly across units
        g = x.groupby("target")[list(MODELS)].agg(["sum", "count"])
        n = g[("chronos", "count")].to_numpy(float)
        S = {m: g[(m, "sum")].to_numpy(float) for m in MODELS}
        T = len(n)

        def stat(idx, a, b):
            return (S[a][idx].sum() - S[b][idx].sum()) / n[idx].sum()

        def ratio(idx, a):
            return S[a][idx].sum() / S["naive_b"][idx].sum()

        full = np.arange(T)
        for other in ("lgbm", "arima", "naive_b"):
            est = stat(full, "chronos", other)
            reps = []
            for _ in range(B):
                nb = int(np.ceil(T / BLOCK))
                starts = rng.integers(0, T - BLOCK + 1, nb)
                idx = np.concatenate([np.arange(s, s + BLOCK) for s in starts])[:T]
                reps.append(stat(idx, "chronos", other))
            lo, hi = np.percentile(reps, [2.5, 97.5])
            rows.append(dict(h=h, comparison=f"chronos - {other}", months=T, cells=int(n.sum()),
                             mean_abs_error_diff=est, ci_lo=lo, ci_hi=hi,
                             rel_mae_chronos=ratio(full, "chronos"), rel_mae_other=ratio(full, other)))
    out = pd.DataFrame(rows)
    d = RES / "extension_accuracy"
    d.mkdir(exist_ok=True)
    out.to_csv(d / "e3_e4_clean_months.csv", index=False)
    pd.set_option("display.width", 200)
    print(out.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
