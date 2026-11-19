"""paper/numbers.tex: \\newcommand macros for every number the text quotes.

LaTeX control sequences cannot contain digits, so names spell them out:
  prefix + [Wu<Warm>] + Panel + Model + Method/Contrast + Horizon
e.g. \\CEHoldTwoLgbmAciThree = calibration error of ACI (LightGBM, second hold-out, h=3, warm-up 48).
"""
from __future__ import annotations

import numpy as np

import paper_tables as T
from common import (
    CONTRAST_SETS, CONTRAST_SETS_96, HORIZONS, METHODS, NOMINAL, MDE_LIMIT_PP, PANEL_UNITS, RUNS,
    ce_table, contrasts, ci, load, num, pooled, pval, tost, verdict,
)

HW = {1: "One", 3: "Three", 6: "Six", 12: "Twelve"}
PW = {"expl": "Expl", "hold1": "HoldOne", "hold2": "HoldTwo", "d13r": "DesignRerun", "h1r": "HoldOneRerun"}
MW = {"lgbm": "Lgbm", "arima": "Arima", "naive_b": "NaiveB", "chronos": "Chronos", "ets": "Ets"}
ME_W = {"split": "Split", "rolling": "Roll", "aci": "Aci", "faci": "Faci", "pid": "Pid", "dracp": "Dracp", "native": "Native"}
CW = {"aci-rolling": "AciRoll", "dracp-aci": "DracpAci", "aci-split": "AciSplit"}
WU = {48: "", 96: "WuNinetySix"}


def macros() -> dict[str, tuple[str, str]]:
    """name -> (value, description). Insertion order is preserved."""
    M: dict[str, tuple[str, str]] = {}

    def add(name, value, desc):
        assert name.isalpha(), name
        assert name not in M, f"duplicate macro {name}"
        M[name] = (value, desc)

    # --- sizes -------------------------------------------------------------------------------
    n_design, n_h1, n_h2 = (len(PANEL_UNITS[p]) for p in ("expl", "hold1", "hold2"))
    add("NCountries", str(n_design + n_h1 + n_h2), "countries in the three panels")
    add("NDesign", str(n_design), "design panel countries")
    add("NHoldoutOne", str(n_h1), "first hold-out panel countries")
    add("NHoldoutTwo", str(n_h2), "second hold-out panel countries")
    add("NBaseModels", "4", "base forecasters in the extension (naive B, ARIMA, LightGBM, Chronos)")
    add("NominalLevel", f"{NOMINAL:.2f}", "nominal coverage level")
    add("MdeLimit", f"{MDE_LIMIT_PP:.0f}", "MDE limit in pp (rules R5, E5)")

    for run, info in RUNS.items():
        c = contrasts(run, "lgbm") if run != "h2_48" else contrasts(run, "lgbm")
        for h in (3, 6):
            r = c[(c.h == h) & (c.family == "primary")].iloc[0]
            add(f"NMonths{WU[info['warm']]}{PW[info['panel']]}{HW[h]}", str(int(r.n_months)),
                f"pooled calendar months in the bootstrap, {run}, h={h}")
        add(f"NUnits{WU[info['warm']]}{PW[info['panel']]}", str(int(r.n_units)), f"units in {run}")

    # --- calibration error and pooled coverage ----------------------------------------------------
    for run, info in RUNS.items():
        w, p = WU[info["warm"]], PW[info["panel"]]
        ct = ce_table(run)
        pl = pooled(run)
        for r in ct.itertuples():
            if np.isnan(r.ce):
                continue
            base = f"{w}{p}{MW[r.model]}{ME_W[r.method]}{HW[r.h]}"
            add(f"CE{base}", num(r.ce, 3, macro=True), f"CE {run} {r.model} {r.method} h={r.h}")
            add(f"CESd{base}", num(r.sd, 3, macro=True), f"SD across countries of per-country CE, {run} {r.model} {r.method} h={r.h}")
        for r in pl.itertuples():
            base = f"{w}{p}{MW[r.model]}{ME_W[r.method]}{HW[r.h]}"
            add(f"Cov{base}", num(r.coverage, 3, macro=True), f"pooled coverage {run} {r.model} {r.method} h={r.h}")
            if not np.isnan(r.cov_lo):
                add(f"CovLo{base}", num(r.cov_lo, 3, macro=True), "pooled coverage, bootstrap 95% lower")
                add(f"CovHi{base}", num(r.cov_hi, 3, macro=True), "pooled coverage, bootstrap 95% upper")

    # --- contrasts -----------------------------------------------------------------------------
    for sets in (CONTRAST_SETS, CONTRAST_SETS_96):
        for run, model in sets:
            info = RUNS[run]
            c = contrasts(run, model)
            for r in c.itertuples():
                base = f"{WU[info['warm']]}{PW[info['panel']]}{MW[model]}{CW[r.contrast]}{HW[r.h]}"
                add(f"Tpp{base}", num(r.T_pp, 1, macro=True), f"contrast T in pp, {run} {model} {r.contrast} h={r.h}")
                add(f"TppLo{base}", num(r.ci_lo_pp, 1, macro=True), "95% bootstrap CI lower, pp")
                add(f"TppHi{base}", num(r.ci_hi_pp, 1, macro=True), "95% bootstrap CI upper, pp")
                add(f"Pval{base}", pval(r.p, macro=True), "unadjusted bootstrap p")
                if r.family == "primary":
                    add(f"Holm{base}", pval(r.p_holm, macro=True), "Holm-adjusted p")
                    add(f"Mde{base}", num(r.mde_pp, 1, macro=True), "minimum detectable difference, pp ('--' undefined)")
                    add(f"Verdict{base}", verdict(r.contrast, r.T_pp, r.p_holm, r.mde_pp, bool(r.mde_computed)), "verdict under R5/E5: Met, Not met or Inconclusive")
    for run, model in CONTRAST_SETS + CONTRAST_SETS_96:
        t = tost(run, model)
        info = RUNS[run]
        for r in t.itertuples():
            base = f"{WU[info['warm']]}{PW[info['panel']]}{MW[model]}DracpAci{HW[r.h]}"
            add(f"TostP{base}", pval(r.p_tost, macro=True), f"TOST p, {run} {model} h={r.h}")
    rows = T.contrast_rows()
    add("NPrimaryContrasts", str(len(rows)), "primary contrast cells in tab_contrasts_primary")
    for v, name in (("Met", "NMet"), ("Not met", "NNotMet"), ("Inconclusive", "NInconclusive")):
        add(name, str(sum(r["verdict"] == v for r in rows)), f"primary contrast cells with verdict {v}")

    # --- point accuracy -------------------------------------------------------------------------
    for m in ("naive_b", "arima", "lgbm", "chronos"):
        for h in HORIZONS:
            add(f"RelMaeAll{MW[m]}{HW[h]}", num(T.rel_mae_all(m, h), 3, macro=True),
                f"MAE relative to naive B, all months, second hold-out, h={h}")
    a = T.accuracy_frame()
    add("NCleanMonths", str(int(a["months"].iloc[0])), "calendar months from 2025-01 (clean sample)")
    add("NCleanCells", str(int(a["cells"].iloc[0])), "country-month cells per horizon, clean sample")
    for h in HORIZONS:
        s = a[a.h == h].set_index("comparison")
        add(f"RelMaeCleanChronos{HW[h]}", num(s.loc["chronos - lgbm", "rel_mae_chronos"], 3, macro=True), "clean-month relative MAE of Chronos")
        add(f"RelMaeCleanLgbm{HW[h]}", num(s.loc["chronos - lgbm", "rel_mae_other"], 3, macro=True), "clean-month relative MAE of LightGBM")
        add(f"RelMaeCleanArima{HW[h]}", num(s.loc["chronos - arima", "rel_mae_other"], 3, macro=True), "clean-month relative MAE of ARIMA")
        for key, nm in (("lgbm", "Lgbm"), ("arima", "Arima"), ("naive_b", "NaiveB")):
            r = s.loc[f"chronos - {key}"]
            add(f"MaeDiff{nm}{HW[h]}", num(r.mean_abs_error_diff, 3, macro=True), f"Chronos minus {key}, clean MAE difference, h={h}")
            add(f"MaeDiffLo{nm}{HW[h]}", num(r.ci_lo, 3, macro=True), "95% CI lower")
            add(f"MaeDiffHi{nm}{HW[h]}", num(r.ci_hi, 3, macro=True), "95% CI upper")

    # --- feedback delay (S3, R4) -----------------------------------------------------------------
    for tag, rel in (("Expl", "explore_v1"), ("HoldOne", "holdout_ncal48")):
        f = T.feedback_frame(rel)
        for me in METHODS:
            r = f.loc[me]
            b = f"{tag}{ME_W[me]}"
            add(f"FbDelayed{b}", num(r.cov_delayed, 3, macro=True), f"h=12 coverage, delayed feedback, {rel}")
            add(f"FbInstant{b}", num(r.cov_instant, 3, macro=True), f"h=12 coverage, instant feedback, {rel}")
            add(f"FbDiff{b}", num(r["diff"] * 100, 1, macro=True), "instant minus delayed coverage, pp")
            add(f"FbDiffLo{b}", num(r.ci_lo * 100, 1, macro=True), "95% CI lower, pp")
            add(f"FbDiffHi{b}", num(r.ci_hi * 100, 1, macro=True), "95% CI upper, pp")
        add(f"FbCells{tag}", str(int(f.loc["aci", "cells_paired"])), f"paired cells, {rel}")

    # --- width and Winkler (S4) -----------------------------------------------------------------------
    for tag, rel in (("Expl", "explore_v1"), ("HoldOne", "holdout_ncal48")):
        s4 = load(f"{rel}/robust/s4_compact.csv")
        s4 = s4[s4.n_cal == 48].set_index("method")
        for me in ("aci", "dracp", "faci", "pid", "rolling", "split"):
            for h in HORIZONS:
                b = f"{tag}{ME_W[me]}{HW[h]}"
                add(f"WinklerRatio{b}", num(s4.loc[me, f"winkler_ratio_h{h}"], 2, macro=True), "Winkler score ratio to rolling")
                add(f"WidthRatio{b}", num(s4.loc[me, f"width_ratio_h{h}"], 2, macro=True), "median width ratio to rolling")

    # --- native intervals (S7) ---------------------------------------------------------------------
    vs = load("extra_descriptive/s7_aci_vs_native_arima.csv")
    for r in vs.itertuples():
        tag = {"exploratory": "Expl", "holdout": "HoldOne"}[r.sample]
        add(f"NatTpp{tag}{HW[r.h]}", num(r.T * 100, 1, macro=True), "ACI minus native (ARIMA), pp of CE")
        add(f"NatTppLo{tag}{HW[r.h]}", num(r.ci_lo * 100, 1, macro=True), "95% CI lower")
        add(f"NatTppHi{tag}{HW[r.h]}", num(r.ci_hi * 100, 1, macro=True), "95% CI upper")
        add(f"NatPval{tag}{HW[r.h]}", pval(r.p, macro=True), "unadjusted p")

    # --- R4 and E5 summary ------------------------------------------------------------------------
    r4 = T.r4_numbers()
    add("RFourDiff", num(r4["diff_pp"], 1, macro=True), "R4: instant minus delayed ACI coverage at h=12, hold-out 1, pp")
    e5 = T.e5_range()
    add("EFiveMdeMin", num(e5["lo"], 1, macro=True), "smallest defined MDE of ACI-rolling, hold-out 2, warm-up 48, pp")
    add("EFiveMdeMax", num(e5["hi"], 1, macro=True), "largest defined MDE of ACI-rolling, hold-out 2, warm-up 48, pp")
    return M


def render() -> str:
    M = macros()
    out = ["% Generated by scripts/thesis/paper/build_paper_assets.py -- do not edit.",
           "% Every number quoted in the text should come from here. '--' marks an undefined value.",
           "% Names spell digits as words (LaTeX control sequences cannot contain digits)."]
    for name, (val, desc) in M.items():
        out.append(f"\\newcommand{{\\{name}}}{{{val}}} % {desc}")
    return "\n".join(out) + "\n"
