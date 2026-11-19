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

from exp.data import COUNTRIES, DATA_DIR, country_units, load_holdout, load_raw  # noqa: E402
from exp.evaluate import (Config, coverage_by_stress_decile, interval_summary,  # noqa: E402
                          point_metrics, primary_contrasts, run_unit)
from exp.calibration import (ce_contrasts, null_ce_bias, per_unit_coverage, sd_coverage,  # noqa: E402
                             tost_table, winkler_contrasts)
from exp.power import mde_ce_table, mde_ce_windows, mde_table  # noqa: E402

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
    if cfg.instant_feedback:
        (out / "DIAGNOSTIC_instant_feedback.txt").write_text(
            "DIAGNOSTIC RUN: every interval method received each origin's outcome at origin+1 (as if h=1),\n"
            "although the real outcome arrives at origin+h.  Not a valid forecasting setup; not a primary "
            "result.\n", encoding="utf-8")
    pm_model = primary_model if primary_model in set(iv.model) else iv.model.iloc[0]
    if {"split", "aci", "dracp"} <= set(iv.method) and set(iv.h) >= {3, 6}:
        con = pd.concat([primary_contrasts(iv, pm_model, s, B=cfg.boot_B, seed=cfg.seed)
                         for s in sorted(iv["sample"].unique())], ignore_index=True)
        con.to_csv(out / "primary_contrasts.csv", index=False)
        smp_mde = "exploratory" if "exploratory" in set(iv["sample"]) else sorted(iv["sample"].unique())[0]
        mde = mde_table(iv, pm_model, smp_mde, **(power_kw or {}))
        mde.to_csv(out / "power_mde.csv", index=False)
        res.update(contrasts=con, mde=mde)
    if {"rolling", "aci", "dracp", "split"} <= set(iv.method) and set(iv.h) >= {3, 6}:
        samples = sorted(iv["sample"].unique())
        parts = dict(
            calibration_contrasts=[ce_contrasts(iv, pm_model, s, B=cfg.boot_B, seed=cfg.seed) for s in samples],
            calibration_tost=[tost_table(iv, pm_model, s, B=cfg.boot_B, seed=cfg.seed) for s in samples],
            winkler_contrasts=[winkler_contrasts(iv, pm_model, s, B=cfg.boot_B, seed=cfg.seed) for s in samples],
            sd_coverage=[sd_coverage(iv, sample=s) for s in samples])
        for name, lst in parts.items():
            pd.concat(lst, ignore_index=True).to_csv(out / f"{name}.csv", index=False)
    return res


def run_ce(inp: Path, out: Path, model: str = "lgbm", B: int = 2000, n_outer: int = 100,
           sample: str = "exploratory", block_len: int = 12, window_mde: bool = False,
           window: int = 15, n_windows: int = 60):
    """Calibration-error analysis from an existing intervals_all.csv, rows of one sample only
    ('exploratory' by default; 'holdout' / 'confirmatory' pool the units the same way)."""
    iv = pd.read_csv(inp / "intervals_all.csv")
    iv = iv[iv["sample"] == sample]
    if iv.empty:
        raise SystemExit(f"no rows with sample={sample!r} in {inp}")
    out.mkdir(parents=True, exist_ok=True)
    con = ce_contrasts(iv, model, sample, B=B, block_len=block_len)
    tost = tost_table(iv, model, sample, B=B, block_len=block_len)
    wk = winkler_contrasts(iv, model, sample, B=B, block_len=block_len)
    sd = sd_coverage(iv, (1, 3, 6, 12), sample)
    pu = per_unit_coverage(iv, (1, 3, 6, 12), sample)
    mde = mde_ce_table(iv, model, sample, n_outer=n_outer, block_len=block_len)
    con.to_csv(out / "calibration_contrasts.csv", index=False)
    tost.to_csv(out / "calibration_tost.csv", index=False)
    wk.to_csv(out / "winkler_contrasts.csv", index=False)
    sd.to_csv(out / "sd_coverage.csv", index=False)
    pu.to_csv(out / "per_unit_coverage.csv", index=False)
    mde.to_csv(out / "power_mde_ce.csv", index=False)
    nb = pd.DataFrame([null_ce_bias(n) for n in (15, 190)])
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)
    print(f"\nCalibration-error contrasts, sample={sample}, block length max(h,{block_len}) "
          "(T = mean_u CE_m1 - CE_m2; negative = m1 better calibrated; Holm over the 4 primary):")
    print(con.round(4).to_string(index=False))
    print("\nTOST equivalence of dracp-aci in CE (margin 2 pp):")
    print(tost.round(4).to_string(index=False))
    print("\nWinkler contrast (relative difference of per-unit mean Winkler, equal unit weights; unadjusted p):")
    print(wk.round(4).to_string(index=False))
    print("\nCross-unit SD of coverage:")
    print(sd[sd.model == model].pivot_table(index="method", columns="h", values="sd_coverage").round(3).to_string())
    print("\nMean coverage by method and h:")
    print(sd[sd.model == model].pivot_table(index="method", columns="h", values="mean_coverage").round(3).to_string())
    print("\nMDE for CE contrast (pp of mean |cov-0.90|, power 0.80, alpha 0.05/4):")
    print(mde.round(2).to_string(index=False))
    res = dict(contrasts=con, tost=tost, winkler=wk, sd=sd, per_unit=pu, mde=mde, null_bias=nb)
    if window_mde:
        wm = mde_ce_windows(iv, model, sample, window=window, n_windows=n_windows, block_len=block_len)
        wm.to_csv(out / f"power_mde_ce_windows{window}.csv", index=False)
        print(f"\nMDE for CE contrast on random {window}-month windows ({n_windows} windows):")
        print(wm.round(2).to_string(index=False))
        res["mde_windows"] = wm
    return res


def run_robust(inp: Path, out: Path, sample: str, instant: Path | None, delayed: Path | None, n_cal: int,
               B: int, B_loo: int, model: str, only: set):
    """Robustness analyses S1-S4 from existing intervals_all.csv files (see exp/robust.py)."""
    from exp import robust as R
    iv = pd.read_csv(inp / "intervals_all.csv")
    iv = iv[iv["sample"] != "confirmatory"]
    out.mkdir(parents=True, exist_ok=True)
    role = "primary" if n_cal == 48 else "sensitivity"
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 40)
    res = {}

    def save(name, df):
        df.insert(0, "n_cal", n_cal)
        df.insert(1, "role", role)
        df.to_csv(out / name, index=False)
        res[name] = df

    if "s1" in only:
        save("s1_leave_one_out.csv", R.s1_leave_one_out(iv, model, sample, B=B_loo))
    if "s2" in only:
        save("s2_other_models.csv", R.s2_other_models(iv, sample=sample, B=B))
    if "s3" in only and instant is not None:
        dl = pd.read_csv((delayed or inp) / "intervals_all.csv")
        ins = pd.read_csv(instant / "intervals_all.csv")
        save("s3_feedback_diff.csv", R.s3_feedback(ins, dl, model, sample, B=B))
    if "s4" in only:
        s4 = R.s4_width_efficiency(iv, model, sample)
        save("s4_width_efficiency.csv", s4)
        save("s4_compact.csv", R.s4_compact(s4))
    for k, v in res.items():
        print(f"\n== {k} (sample={sample}, n_cal={n_cal}, {role}) ==")
        if k.startswith("s1"):
            print(v[v.removed_unit.isin(["NONE(full)", "SUMMARY"])].dropna(axis=1, how="all").round(4).to_string(index=False))
        elif k.startswith("s3"):
            print(v[v.unit == "ALL"].round(4).to_string(index=False))
        elif k.startswith("s4_w"):
            print(v[v.unit == "POOLED"].round(3).to_string(index=False))
        else:
            print(v.round(4).to_string(index=False))
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
    f.add_argument("--n-cal", type=int, default=48, help="warm-up (calibration) months")
    f.add_argument("--instant-feedback", action="store_true",
                   help="DIAGNOSTIC: release every outcome at origin+1 as if h=1; requires a separate --out")
    f.add_argument("--holdout2", action="store_true",
                   help="use data/holdout2.json (all rows labelled sample=holdout2; default --start 2010-01)")
    f.add_argument("--max-origins", type=int, default=None,
                   help="SMOKE: evaluate only the last N origins per unit (after the warm-up)")
    f.add_argument("--holdout", action="store_true",
                   help="use data/holdout.json (all rows labelled sample=holdout) instead of the 13 countries")
    c = sub.add_parser("ce", help="calibration-error contrasts from intervals_all.csv")
    c.add_argument("--in", dest="inp", default="results/explore_v1")
    c.add_argument("--out", default="results/explore_v1")
    c.add_argument("--model", default="lgbm")
    c.add_argument("--boot", type=int, default=2000)
    c.add_argument("--n-outer", type=int, default=100)
    c.add_argument("--sample", default="exploratory", choices=["exploratory", "confirmatory", "holdout", "holdout2"])
    c.add_argument("--block-len", type=int, default=12)
    c.add_argument("--window-mde", action="store_true", help="MDE on random short windows")
    c.add_argument("--window", type=int, default=15)
    c.add_argument("--n-windows", type=int, default=60)
    r = sub.add_parser("robust", help="robustness analyses S1-S4 from existing intervals_all.csv (secondary)")
    r.add_argument("--in", dest="inp", required=True)
    r.add_argument("--instant", default=None, help="diagnostic instant-feedback h=12 run (S3)")
    r.add_argument("--delayed", default=None, help="delayed side of S3 (default: --in)")
    r.add_argument("--out", default=None, help="default: <in>/robust")
    r.add_argument("--sample", required=True, choices=["exploratory", "holdout", "holdout2"])
    r.add_argument("--n-cal", type=int, default=48)
    r.add_argument("--boot", type=int, default=2000)
    r.add_argument("--boot-loo", type=int, default=500)
    r.add_argument("--model", default="lgbm")
    r.add_argument("--only", default="s1,s2,s3,s4")
    a = ap.parse_args(argv)
    t0 = time.time()
    if a.cmd == "robust":
        def _q(x):
            x = Path(x)
            return x if x.is_absolute() else (THESIS / x)
        run_robust(_q(a.inp), _q(a.out) if a.out else _q(a.inp) / "robust", a.sample,
                   _q(a.instant) if a.instant else None, _q(a.delayed) if a.delayed else None, a.n_cal,
                   a.boot, a.boot_loo, a.model, set(a.only.split(",")))
        print(f"\ndone in {time.time() - t0:.1f}s")
        return
    if a.cmd == "ce":
        def _p(x):
            x = Path(x)
            return x if x.is_absolute() else (THESIS / x)
        run_ce(_p(a.inp), _p(a.out), a.model, a.boot, a.n_outer, a.sample, a.block_len, a.window_mde,
               a.window, a.n_windows)
        print(f"\ndone in {time.time() - t0:.1f}s")
        return
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
        if a.instant_feedback and a.out in ("full", "explore_v1", "smoke"):
            raise SystemExit("--instant-feedback is a diagnostic: choose a separate --out directory")
        if a.holdout and a.holdout2:
            raise SystemExit("--holdout and --holdout2 are mutually exclusive")
        if a.holdout2:
            raw = load_holdout(path=(Path(a.data_dir) / "holdout2.json") if a.data_dir else DATA_DIR / "holdout2.json",
                               data_dir=a.data_dir)
        elif a.holdout:
            raw = load_holdout(data_dir=a.data_dir)
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
                     horizons=tuple(int(x) for x in a.horizons.split(",")), boot_B=a.boot,
                     n_cal=a.n_cal, instant_feedback=a.instant_feedback,
                     n_eval_last=a.max_origins,
                     sample="holdout2" if a.holdout2 else ("holdout" if a.holdout else None))
        a.holdout = a.holdout or a.holdout2
        countries = list(raw["cpi"]) if a.holdout and a.countries == ",".join(COUNTRIES) else a.countries.split(",")
        start = a.start or ("2010-01" if a.holdout2 else "2000-01" if a.holdout else None)
        units = {}
        for c in countries:
            units.update(country_units(raw, c, horizons=cfg.horizons, start=start))
        res = execute(units, cfg, RESULTS / a.out, resume=a.resume)
    show(res)
    print(f"\ndone in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
