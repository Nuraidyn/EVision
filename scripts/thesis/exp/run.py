"""CLI.  From scripts/thesis:

    .venv/Scripts/python.exe -m exp.run smoke
    .venv/Scripts/python.exe -m exp.run full [--countries BR,MX] [--horizons 1,3,6,12] [--resume]

Outputs (CSV) go to scripts/thesis/results/<smoke|full>/ .
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

THESIS = Path(__file__).resolve().parent.parent
if str(THESIS) not in sys.path:
    sys.path.insert(0, str(THESIS))

import pandas as pd  # noqa: E402

from exp.data import COUNTRIES, country_units, load_raw  # noqa: E402
from exp.evaluate import (Config, coverage_by_stress_decile, interval_summary,  # noqa: E402
                          point_metrics, primary_contrasts, run_unit)
from exp.power import mde_table  # noqa: E402

RESULTS = THESIS / "results"


def execute(units: dict, cfg: Config, out: Path, resume: bool = False, primary_model: str = "lgbm",
            power_kw: dict | None = None):
    out.mkdir(parents=True, exist_ok=True)
    (out / "units").mkdir(exist_ok=True)
    pts_all, iv_all = [], []
    for name, frame in units.items():
        fp, fi = out / "units" / f"{name}_points.csv", out / "units" / f"{name}_intervals.csv"
        t0 = time.time()
        if resume and fp.exists() and fi.exists():
            p, i = pd.read_csv(fp), pd.read_csv(fi)
        else:
            p, i = run_unit(name, frame, cfg)
            p.to_csv(fp, index=False)
            i.to_csv(fi, index=False)
        print(f"  {name}: {len(frame)} months, {len(p)} point rows, {len(i)} interval rows, {time.time() - t0:.1f}s", flush=True)
        pts_all.append(p)
        iv_all.append(i)
    pts = pd.concat([x for x in pts_all if len(x)], ignore_index=True)
    iv = pd.concat([x for x in iv_all if len(x)], ignore_index=True)
    pts.to_csv(out / "points_all.csv", index=False)
    iv.to_csv(out / "intervals_all.csv", index=False)
    pm = point_metrics(pts)
    pm.to_csv(out / "point_metrics.csv", index=False)
    summ = interval_summary(iv, B=cfg.boot_B, seed=cfg.seed)
    summ.to_csv(out / "interval_summary.csv", index=False)
    stress = pd.concat([coverage_by_stress_decile(iv, m, h) for m in iv.model.unique() for h in sorted(iv.h.unique())],
                       ignore_index=True)
    stress.to_csv(out / "stress_deciles.csv", index=False)
    res = dict(points=pts, intervals=iv, point_metrics=pm, summary=summ)
    pm_model = primary_model if primary_model in set(iv.model) else iv.model.iloc[0]
    if {"split", "aci", "dracp"} <= set(iv.method) and set(iv.h) >= {3, 6}:
        con = pd.concat([primary_contrasts(iv, pm_model, s, B=cfg.boot_B, seed=cfg.seed)
                         for s in sorted(iv["sample"].unique())], ignore_index=True)
        con.to_csv(out / "primary_contrasts.csv", index=False)
        mde = mde_table(iv, pm_model, "exploratory", **(power_kw or {}))
        mde.to_csv(out / "power_mde.csv", index=False)
        res.update(contrasts=con, mde=mde)
    return res


def show(res: dict):
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)
    s = res["summary"]
    s = s[s.unit == "ALL"]
    print("\nPooled interval summary (nominal 0.90):")
    print(s[["model", "method", "h", "sample", "n", "coverage", "cov_lo", "cov_hi", "mean_width", "winkler"]]
          .round(3).to_string(index=False))
    pm = res["point_metrics"]
    print("\nPooled point metrics (relative to naive A / B):")
    print(pm[pm.unit == "ALL"][["model", "h", "sample", "n", "mae", "rel_mae_naive_a", "rel_mae_naive_b"]]
          .round(3).to_string(index=False))
    if "contrasts" in res:
        print("\nPrimary contrasts:")
        print(res["contrasts"].round(4).to_string(index=False))
        print("\nMDE (exploratory):")
        print(res["mde"].round(2).to_string(index=False))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="exp.run")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("smoke")
    f = sub.add_parser("full")
    f.add_argument("--countries", default=",".join(COUNTRIES))
    f.add_argument("--horizons", default="1,3,6,12")
    f.add_argument("--models", default="naive_a,naive_b,ets,arima,lgbm")
    f.add_argument("--conformal-models", default="naive_b,arima,lgbm")
    f.add_argument("--boot", type=int, default=1000)
    f.add_argument("--resume", action="store_true")
    f.add_argument("--data-dir", default=None)
    f.add_argument("--start", default=None, help="common start month, e.g. 2000-01 (default: all history)")
    f.add_argument("--end", default=None,
                   help="last month of data, e.g. 2025-06; cuts every series so that no confirmatory "
                        "target month (>= 2025-07) can enter the run")
    f.add_argument("--out", default="full", help="results sub-directory under results/")
    a = ap.parse_args(argv)
    t0 = time.time()
    if a.cmd == "smoke":
        raw = load_raw()
        cfg = Config(models=("naive_a", "naive_b", "ets", "arima", "lgbm"), conformal_models=("lgbm", "arima"),
                     horizons=(3, 6), n_cal=40, n_eval_last=24, boot_B=200)
        units = {}
        for c in ("BR", "MX"):
            units.update(country_units(raw, c, horizons=cfg.horizons, start="2000-01"))
        res = execute(units, cfg, RESULTS / "smoke", primary_model="lgbm",
                      power_kw=dict(n_outer=40, B_inner=99))
    else:
        raw = load_raw(a.data_dir)
        print("data files:", raw["files"])
        if a.end:
            end = pd.Period(a.end, "M")
            for key in ("cpi", "fx"):
                raw[key] = {c: s[s.index <= end] for c, s in raw[key].items()}
            if raw["brent"] is not None:
                raw["brent"] = raw["brent"][raw["brent"].index <= end]
            print("data cut at", end)
        cfg = Config(models=tuple(a.models.split(",")), conformal_models=tuple(a.conformal_models.split(",")),
                     horizons=tuple(int(x) for x in a.horizons.split(",")), boot_B=a.boot)
        units = {}
        for c in a.countries.split(","):
            units.update(country_units(raw, c, horizons=cfg.horizons, start=a.start))
        res = execute(units, cfg, RESULTS / a.out, resume=a.resume)
    show(res)
    print(f"\ndone in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
