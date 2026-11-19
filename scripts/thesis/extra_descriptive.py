"""Post hoc descriptive additions S6 (Kazakhstan alone) and S7 (native intervals), see the
seventh entry of docs/thesis/experiment-protocol.md. Reads existing interval files only.

Usage (from scripts/thesis): .venv/Scripts/python.exe -I extra_descriptive.py
Writes results/extra_descriptive/*.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from exp.calibration import block_len_ce, boot_stat, ce_arrays, ce_contrast_test  # noqa: E402

RES = HERE / "results"
OUT = RES / "extra_descriptive"
OUT.mkdir(exist_ok=True)
HS = (1, 3, 6, 12)
USE = ["unit", "country", "model", "h", "method", "covered", "width", "winkler", "origin", "target", "sample"]


def kazakhstan():
    iv = pd.read_csv(RES / "explore_v1" / "intervals_all.csv", usecols=USE)
    k = iv[(iv.country == "KZ") & (iv.model == "lgbm")]
    g = k.groupby(["method", "h"]).agg(n_origins=("covered", "size"), coverage=("covered", "mean"),
                                        median_width=("width", "median"), mean_winkler=("winkler", "mean")).reset_index()
    g["calibration_error"] = (g.coverage - 0.90).abs()
    g.to_csv(OUT / "s6_kazakhstan.csv", index=False)
    return g


def native():
    rows, contrasts = [], []
    for run, sample in (("explore_v1", "exploratory"), ("holdout_ncal48", "holdout")):
        iv = pd.read_csv(RES / run / "intervals_all.csv", usecols=USE)
        pu = iv.groupby(["model", "method", "h", "unit"]).covered.mean().reset_index()
        pu["ce"] = (pu.covered - 0.90).abs()
        s = pu.groupby(["model", "method", "h"]).agg(mean_coverage=("covered", "mean"), mean_ce=("ce", "mean")).reset_index()
        s.insert(0, "sample", sample)
        rows.append(s[s.model.isin(["arima", "ets"]) | (s.model == "lgbm")])
        for h in HS:
            arrs = ce_arrays(iv, "arima", h, "aci", "native", sample)
            r = ce_contrast_test(arrs, h, 2000, 12345, 12)
            contrasts.append(dict(sample=sample, model="arima", h=h, contrast="aci-native",
                                  block_len=block_len_ce(h, 12), **r))
    pd.concat(rows).to_csv(OUT / "s7_native_ce.csv", index=False)
    c = pd.DataFrame(contrasts)
    c.to_csv(OUT / "s7_aci_vs_native_arima.csv", index=False)
    return c


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    k = kazakhstan()
    print("S6 Kazakhstan (lgbm, exploratory design panel): coverage / CE")
    print(k.pivot(index="method", columns="h", values="coverage").round(3))
    print(k.pivot(index="method", columns="h", values="calibration_error").round(3))
    print("origins per horizon:", k[k.method == "aci"].set_index("h").n_origins.to_dict())
    c = native()
    print("\nS7 ACI - native (ARIMA base), CE contrast in pp")
    print(c.assign(T_pp=lambda d: d["T"] * 100, lo=lambda d: d.ci_lo * 100, hi=lambda d: d.ci_hi * 100)
           [["sample", "h", "T_pp", "lo", "hi", "p"]].round(3).to_string(index=False))
