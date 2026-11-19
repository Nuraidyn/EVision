"""LaTeX tables (tabular environments only, booktabs) built from the committed CSV results."""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import (
    COUNTRIES, CONTRAST_SETS, CONTRAST_SETS_96, HORIZONS, METHOD_LABEL, METHODS, MODEL_LABEL,
    PANEL_LABEL, PANEL_UNITS, PANEL_WINDOW, RUNS, UNDEF, ce_table, ci, contrasts, cpi_series, load,
    num, per_unit, pooled, pval, row, tabular, tex_escape, tost, verdict, is_inconclusive,
)

HLAB = {1: "$h{=}1$", 3: "$h{=}3$", 6: "$h{=}6$", 12: "$h{=}12$"}
CONTRAST_LABEL = {"aci-rolling": "ACI $-$ rolling", "dracp-aci": "DRACP $-$ ACI", "aci-split": "ACI $-$ split"}


# --------------------------------------------------------------------------------------------
def tab_panels() -> str:
    lines = []
    first_panel = True
    for panel in ("expl", "hold1", "hold2"):
        run = {"expl": "expl48", "hold1": "hold48", "hold2": "h2_48"}[panel]
        pu = per_unit(run)
        pu = pu[(pu.model == "lgbm") & (pu.method == "aci") & (pu.h == 3)].set_index("unit")["n"]
        lo, hi = PANEL_WINDOW[panel]
        if not first_panel:
            lines.append("\\midrule")
        first_panel = False
        lines.append(f"\\multicolumn{{6}}{{l}}{{\\emph{{{PANEL_LABEL[panel]}}}}} \\\\")
        for u in PANEL_UNITS[panel]:
            months = sorted(m for m in cpi_series(u) if lo <= m <= hi)
            n = pu.get(u, np.nan)
            lines.append(
                row([u, COUNTRIES[u].replace("'", "'"), months[0], months[-1], str(len(months)),
                     UNDEF if pd.isna(n) else str(int(n))])
            )
    hdr = ["Code", "Country", "CPI from", "CPI to", "Months", "Origins ($h{=}3$)"]
    return tabular("llllrr", hdr, lines)


# --------------------------------------------------------------------------------------------
def tab_methods() -> str:
    P = lambda s: s  # noqa: E731  (text is written LaTeX-safe)
    rows = [
        "\\multicolumn{3}{l}{\\emph{Interval methods (nominal level 0.90, $\\alpha=0.10$)}} \\\\",
        row(["Split", "Quantile of absolute residuals on the warm-up window; fixed, never updated",
             "Warm-up $n_{\\mathrm{cal}}=48$ (primary) or 96"]),
        row(["Rolling", "Quantile of the most recent absolute residuals",
             "Window 120 residuals"]),
        row(["ACI", "Rolling window; quantile level moved online after each released outcome",
             "Step 0.02, window 120"]),
        row(["FACI", "Aggregation of ACI experts with several step sizes", "Package defaults (\\texttt{dracp})"]),
        row(["Conformal PID", "Error-integrator and scorecaster control of the quantile", "Package defaults (\\texttt{dracp})"]),
        row(["DRACP", "Regime-aware calibration with FACI control of the level",
             "Calibration window 120, target window 24, decay 0.985, adaptive bandwidth (grid), 3 regimes"]),
        row(["Native", "Parametric intervals of the base model (ARIMA: Gaussian from $\\psi$-weights; ETS: simulation)",
             "ETS: 400 simulated paths"]),
        "\\midrule",
        "\\multicolumn{3}{l}{\\emph{Base point forecasters (cumulative $h$-month log growth)}} \\\\",
        row(["Naive B", "Last observed cumulative $h$-month growth", "No parameters"]),
        row(["ARIMA", "ARMA$(p,q)$ with constant and two annual harmonics on monthly inflation; $h$ forecasts summed",
             "$p,q\\in\\{0,1,2\\}$ by AICc every 12 origins"]),
        row(["LightGBM", "Direct forecast, one model per horizon",
             "200 trees, learning rate 0.05, 8 leaves, subsample 0.8, column sample 0.8, refit every 3 origins"]),
        row(["Chronos", "Pretrained model used zero-shot on monthly inflation; $h$ median forecasts summed",
             "\\texttt{chronos-bolt-tiny}, context 2048, no covariates"]),
        "\\midrule",
        "\\multicolumn{3}{l}{\\emph{Evaluation}} \\\\",
        row(["Rolling origin", "One origin per month, expanding training window; outcome released $h$ months after the origin",
             "Minimum 60 months of history; horizons 1, 3, 6, 12"]),
        row(["Calibration error", "Mean over countries of $|\\mathrm{coverage}-0.90|$", "Equal weight per country"]),
        row(["Bootstrap", "Moving blocks of calendar months, resampled jointly across countries",
             "Block length $\\max(h,12)$, 2000 replicates, 95\\% percentile interval"]),
        row(["Multiplicity", "Holm over the primary family of four contrasts per base model",
             "ACI $-$ rolling and DRACP $-$ ACI at $h=3,6$"]),
        row(["TOST", "Equivalence of DRACP and ACI", "Margin 2 pp of CE"]),
        row(["MDE (R5, E5)", "Simulated minimum detectable difference at power 0.80",
             "Undefined or above 7 pp: inconclusive"]),
    ]
    spec = "p{0.15\\linewidth}p{0.45\\linewidth}p{0.32\\linewidth}"
    return tabular(spec, ["Item", "Description", "Key settings"], rows)


# --------------------------------------------------------------------------------------------
def _ce_block(run: str, models: list[str], ets_native: bool) -> str:
    t = ce_table(run).set_index(["model", "method", "h"])["ce"]
    lines: list[str] = []
    for i, m in enumerate(models):
        if i:
            lines.append("\\midrule")
        meths = METHODS + (["native"] if (m, "native", 3) in t.index else [])
        for j, me in enumerate(meths):
            cells = [MODEL_LABEL[m] if j == 0 else "", METHOD_LABEL[me]]
            cells += [num(t.get((m, me, h), np.nan), 3) for h in HORIZONS]
            lines.append(row(cells))
    if ets_native and ("ets", "native", 3) in t.index:
        lines.append("\\midrule")
        lines.append(row([MODEL_LABEL["ets"], METHOD_LABEL["native"]] + [num(t.get(("ets", "native", h), np.nan), 3) for h in HORIZONS]))
    return tabular("llrrrr", ["Base model", "Interval"] + [HLAB[h] for h in HORIZONS], lines)


def tab_ce_exploratory() -> str:
    return _ce_block("expl48", ["lgbm", "arima", "naive_b"], True)


def tab_ce_holdout1() -> str:
    return _ce_block("hold48", ["lgbm", "arima", "naive_b"], True)


def tab_ce_holdout2() -> str:
    return _ce_block("h2_48", ["lgbm", "arima", "naive_b", "chronos"], False)


# --------------------------------------------------------------------------------------------
def contrast_rows(sets=CONTRAST_SETS) -> list[dict]:
    out = []
    for run, model in sets:
        c = contrasts(run, model)
        c = c[c.family == "primary"].copy()
        c["order"] = c["contrast"].map({"aci-rolling": 0, "dracp-aci": 1})
        c = c.sort_values(["order", "h"])
        for r in c.itertuples():
            out.append(dict(run=run, model=model, panel=RUNS[run]["panel"], h=int(r.h), contrast=r.contrast,
                            T=r.T_pp, lo=r.ci_lo_pp, hi=r.ci_hi_pp, holm=r.p_holm, p=r.p, mde=r.mde_pp,
                            mde_computed=bool(r.mde_computed),
                            verdict=verdict(r.contrast, r.T_pp, r.p_holm, r.mde_pp, bool(r.mde_computed)),
                            n_months=int(r.n_months), n_units=int(r.n_units)))
    return out


def tab_contrasts_primary() -> str:
    rows = contrast_rows()
    lines: list[str] = []
    prev = None
    for r in rows:
        key = (r["run"], r["model"])
        if key != prev:
            if prev is not None:
                lines.append("\\midrule")
            first = True
            prev = key
        else:
            first = False
        lines.append(row([
            PANEL_LABEL[r["panel"]] if first else "",
            MODEL_LABEL[r["model"]] if first else "",
            str(r["h"]), CONTRAST_LABEL[r["contrast"]], num(r["T"], 1, True),
            ci(r["lo"], r["hi"], 1), pval(r["holm"]), num(r["mde"], 1), r["verdict"],
        ]))
    hdr = ["Panel", "Base", "$h$", "Contrast", "$T$ (pp)", "95\\% CI", "Holm $p$", "MDE (pp)", "Verdict"]
    return tabular("llcllrrrl", hdr, lines)


# --------------------------------------------------------------------------------------------
def tab_tost() -> str:
    sets = [("expl48", "lgbm"), ("expl96", "lgbm"), ("hold48", "lgbm"), ("hold96", "lgbm"),
            ("d13r", "lgbm"), ("d13r", "chronos"), ("h1r", "lgbm"), ("h1r", "chronos")]
    sets += [("h2_48", m) for m in ("lgbm", "arima", "naive_b", "chronos")]
    sets += [("h2_96", m) for m in ("lgbm", "arima", "naive_b", "chronos")]
    lines: list[str] = []
    prev = None
    for run, model in sets:
        t = tost(run, model).sort_values("h")
        c = contrasts(run, model)
        c = c[c.contrast == "dracp-aci"].set_index("h")
        key = (RUNS[run]["panel"], run)
        for k, r in enumerate(t.itertuples()):
            first_of_panel = prev != key
            if first_of_panel and prev is not None:
                lines.append("\\midrule")
            prev = key
            mde = c.loc[r.h, "mde_pp"] if r.h in c.index else np.nan
            computed = bool(c.loc[r.h, "mde_computed"]) if r.h in c.index else False
            raw = "Equivalent" if r.verdict == "equivalent" else "Not shown"
            if not computed:
                e5 = "Not assessed"
            elif is_inconclusive(mde):
                e5 = "Inconclusive"
            else:
                e5 = raw
            lines.append(row([
                PANEL_LABEL[RUNS[run]["panel"]] if (first_of_panel and k == 0) else "",
                str(RUNS[run]["warm"]) if k == 0 else "", MODEL_LABEL[model] if k == 0 else "", str(int(r.h)),
                num(r.T_pp, 1, True), pval(r.p_tost), raw, e5,
            ]))
    hdr = ["Panel", "Warm-up", "Base", "$h$", "$T$ (pp)", "TOST $p$", "TOST verdict", "Under E5"]
    return tabular("lcclrrll", hdr, lines)


# --------------------------------------------------------------------------------------------
def tab_winkler_width() -> str:
    lines: list[str] = []
    for i, (title, rel) in enumerate((("Design (13), warm-up 48", "explore_v1"), ("Hold-out 1 (7), warm-up 48", "holdout_ncal48"))):
        s4 = load(f"{rel}/robust/s4_compact.csv")
        s4 = s4[s4.n_cal == 48].set_index("method")
        if i:
            lines.append("\\midrule")
        lines.append(f"\\multicolumn{{5}}{{l}}{{\\emph{{{title}}}}} \\\\")
        for me in ("aci", "dracp", "faci", "pid", "rolling", "split"):
            cells = [METHOD_LABEL[me]]
            for h in HORIZONS:
                r = s4.loc[me]
                cells.append(f"{num(r[f'ce_h{h}'], 3)} / {num(r[f'winkler_ratio_h{h}'], 2)} / {num(r[f'width_ratio_h{h}'], 2)}")
            lines.append(row(cells))
    return tabular("lcccc", ["Method"] + [HLAB[h] for h in HORIZONS], lines)


# --------------------------------------------------------------------------------------------
def rel_mae_all(model: str, h: int) -> float:
    pm = load("holdout2_ncal48/point_metrics.csv")
    r = pm[(pm.unit == "ALL") & (pm.model == model) & (pm.h == h)]
    return float(r["rel_mae_naive_b"].iloc[0])


def tab_ablation_basemodel() -> str:
    lines = []
    models = ["naive_b", "arima", "lgbm", "chronos"]
    for m in models:
        c = contrasts("h2_48", m)
        c = c[(c.contrast == "aci-rolling") & (c.family == "primary")].set_index("h")
        cells = [MODEL_LABEL[m]]
        cells += [num(rel_mae_all(m, h), 3) for h in (3, 6)]
        cells += [num(ce_table_val("h2_48", m, "aci", h), 3) for h in (3, 6)]
        cells += [num(ce_table_val("h2_48", m, "rolling", h), 3) for h in (3, 6)]
        for h in (3, 6):
            cells.append(f"{num(c.loc[h, 'T_pp'], 1, True)} ({pval(c.loc[h, 'p_holm'])})")
        lines.append(row(cells))
    head1 = ("& \\multicolumn{2}{c}{Rel. MAE} & \\multicolumn{2}{c}{CE, ACI} & \\multicolumn{2}{c}{CE, rolling} "
             "& \\multicolumn{2}{c}{ACI $-$ rolling, pp (Holm $p$)} \\\\\n"
             "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\\cmidrule(lr){8-9}")
    hdr = ["Base model"] + ["$h{=}3$", "$h{=}6$"] * 4
    body = [head1.split("\n")[0], head1.split("\n")[1], row(hdr), "\\midrule"] + lines
    return tabular("lrrrrrrrr", None, body)


def ce_table_val(run, model, method, h):
    t = ce_table(run)
    r = t[(t.model == model) & (t.method == method) & (t.h == h)]
    return float(r["ce"].iloc[0]) if len(r) else float("nan")


# --------------------------------------------------------------------------------------------
def warmup_configs():
    return [("expl48", "expl96", "lgbm"), ("hold48", "hold96", "lgbm"),
            ("h2_48", "h2_96", "lgbm"), ("h2_48", "h2_96", "arima"),
            ("h2_48", "h2_96", "naive_b"), ("h2_48", "h2_96", "chronos")]


def tab_ablation_warmup() -> str:
    lines = []
    prev = None
    for r48, r96, m in warmup_configs():
        c48 = contrasts(r48, m)
        c96 = contrasts(r96, m)
        c48 = c48[(c48.contrast == "aci-rolling") & (c48.family == "primary")].set_index("h")
        c96 = c96[(c96.contrast == "aci-rolling") & (c96.family == "primary")].set_index("h")
        if prev is not None:
            lines.append("\\midrule")
        prev = 1
        for k, h in enumerate((3, 6)):
            cells = [PANEL_LABEL[RUNS[r48]["panel"]] if k == 0 else "", MODEL_LABEL[m] if k == 0 else "", str(h)]
            for me in ("aci", "rolling"):
                cells += [num(ce_table_val(r48, m, me, h), 3), num(ce_table_val(r96, m, me, h), 3)]
            cells += [num(c48.loc[h, "T_pp"], 1, True), num(c96.loc[h, "T_pp"], 1, True)]
            cells += [pval(c48.loc[h, "p_holm"]), pval(c96.loc[h, "p_holm"])]
            lines.append(row(cells))
    head1 = ("\\multicolumn{3}{c}{} & \\multicolumn{2}{c}{CE, ACI} & \\multicolumn{2}{c}{CE, rolling} "
             "& \\multicolumn{2}{c}{ACI $-$ rolling (pp)} & \\multicolumn{2}{c}{Holm $p$} \\\\\n"
             "\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\\cmidrule(lr){8-9}\\cmidrule(lr){10-11}")
    hdr = ["Panel", "Base", "$h$"] + ["48", "96"] * 4
    body = head1.split("\n") + [row(hdr), "\\midrule"] + lines
    return tabular("llcrrrrrrrr", None, body)


# --------------------------------------------------------------------------------------------
def feedback_frame(rel: str) -> pd.DataFrame:
    d = load(f"{rel}/robust/s3_feedback_diff.csv")
    d = d[(d.unit == "ALL") & (d.h == 12) & (d.n_cal == 48)]
    return d.set_index("method")


def tab_feedback_delay() -> str:
    ex = feedback_frame("explore_v1")
    ho = feedback_frame("holdout_ncal48")
    lines = []
    for me in METHODS:
        cells = [METHOD_LABEL[me]]
        for d in (ex, ho):
            r = d.loc[me]
            cells += [num(r.cov_delayed, 3), num(r.cov_instant, 3),
                      f"{num(r['diff'] * 100, 1, True)} {ci(r.ci_lo * 100, r.ci_hi * 100, 1)}"]
        lines.append(row(cells))
    head1 = ("& \\multicolumn{3}{c}{Design (13), %d cells} & \\multicolumn{3}{c}{Hold-out 1 (7), %d cells} \\\\\n"
             "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}") % (int(ex.loc["aci", "cells_paired"]), int(ho.loc["aci", "cells_paired"]))
    hdr = ["Method"] + ["Delayed", "Instant", "Diff. (pp) [95\\% CI]"] * 2
    body = head1.split("\n") + [row(hdr), "\\midrule"] + lines
    return tabular("lrrcrrc", None, body)


# --------------------------------------------------------------------------------------------
def tab_native_vs_aci() -> str:
    vs = load("extra_descriptive/s7_aci_vs_native_arima.csv").set_index(["sample", "h"])
    lines = []
    blocks = [("Design (13)", "expl48", "exploratory"), ("Hold-out 1 (7)", "hold48", "holdout"), ("Hold-out 2 (10)", "h2_48", None)]
    for bi, (label, run, s7sample) in enumerate(blocks):
        if bi:
            lines.append("\\midrule")
        for k, h in enumerate(HORIZONS):
            en = ce_table_val(run, "arima", "native", h)
            ea = ce_table_val(run, "arima", "aci", h)
            ets = ce_table_val(run, "ets", "native", h)
            if s7sample is not None:
                r = vs.loc[(s7sample, h)]
                contr = f"{num(r['T'] * 100, 1, True)} {ci(r.ci_lo * 100, r.ci_hi * 100, 1)}"
                p = pval(r.p)
            else:
                contr, p = UNDEF, UNDEF
            lines.append(row([label if k == 0 else "", str(h), num(en, 3), num(ea, 3), num(ets, 3), contr, p]))
    hdr = ["Panel", "$h$", "ARIMA native", "ARIMA + ACI", "ETS native", "ACI $-$ native, pp [95\\% CI]", "$p$"]
    return tabular("lcrrrcr", hdr, lines)


# --------------------------------------------------------------------------------------------
def accuracy_frame() -> pd.DataFrame:
    return load("extension_accuracy/e3_e4_clean_months.csv")


def tab_chronos_mae() -> str:
    a = accuracy_frame()
    lines = []
    for h in HORIZONS:
        s = a[a.h == h].set_index("comparison")
        cells = [str(h), num(s.loc["chronos - lgbm", "rel_mae_chronos"], 3), num(s.loc["chronos - lgbm", "rel_mae_other"], 3),
                 num(s.loc["chronos - arima", "rel_mae_other"], 3)]
        for cmp in ("chronos - lgbm", "chronos - arima", "chronos - naive_b"):
            r = s.loc[cmp]
            cells.append(f"{num(r.mean_abs_error_diff, 3, True)} {ci(r.ci_lo, r.ci_hi, 3)}")
        lines.append(row(cells))
    head1 = ("& \\multicolumn{3}{c}{Relative MAE (naive B $=1$)} & \\multicolumn{3}{c}{MAE difference, Chronos $-$ other (pp)} \\\\\n"
             "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}")
    hdr = ["$h$", "Chronos", "LightGBM", "ARIMA", "vs LightGBM", "vs ARIMA", "vs naive B"]
    body = head1.split("\n") + [row(hdr), "\\midrule"] + lines
    return tabular("crrrccc", None, body)


# --------------------------------------------------------------------------------------------
def r4_numbers() -> dict:
    d = feedback_frame("holdout_ncal48").loc["aci"]
    return dict(delayed=float(d.cov_delayed), instant=float(d.cov_instant), diff_pp=float(d["diff"] * 100),
                lo_pp=float(d.ci_lo * 100), hi_pp=float(d.ci_hi * 100))


def e5_range() -> dict:
    """MDE range (pp) of ACI - rolling at warm-up 48 on the second hold-out panel and undefined cells."""
    vals, undefined = [], []
    for m in ("lgbm", "arima", "naive_b", "chronos"):
        c = contrasts("h2_48", m)
        c = c[(c.contrast == "aci-rolling") & (c.family == "primary")]
        for r in c.itertuples():
            if np.isnan(r.mde_pp):
                undefined.append((m, int(r.h)))
            else:
                vals.append(float(r.mde_pp))
    return dict(lo=min(vals), hi=max(vals), undefined=undefined)


def tab_rules() -> str:
    r4 = r4_numbers()
    e5 = e5_range()
    a = accuracy_frame()
    rel = a[a.comparison == "chronos - lgbm"].sort_values("h")["rel_mae_chronos"].tolist()
    n_months = int(a["months"].iloc[0])
    n_cells = int(a["cells"].iloc[0])
    und = "; ".join(f"{MODEL_LABEL[m]} at $h={h}$" for m, h in e5["undefined"])
    rows = [
        "\\multicolumn{4}{l}{\\emph{First hold-out panel (7 countries, LightGBM, Holm over four tests)}} \\\\",
        row(["R1", "ACI better calibrated than split: ACI $-$ split negative with Holm $p<0.05$ at $h=3$ and $h=6$",
             "Not met", "Not met in the primary run (warm-up 48); met at warm-up 96 (sensitivity run, not promoted)"]),
        row(["R2", "ACI improves on rolling: ACI $-$ rolling negative with Holm $p<0.05$",
             "Not shown", "Not shown (MDE undefined, inconclusive); Holm $p$ 0.35 and 1.0 at warm-up 48"]),
        row(["R3", "DRACP versus ACI: equivalence within 2 pp at both warm-ups, or DRACP better with Holm $p<0.05$ at both",
             "Inconclusive", "Equivalent at warm-up 48, not shown at 96; the verdict is not stable"]),
        row(["R4", "Delayed feedback explains the $h=12$ shortfall: ACI coverage with instant feedback higher by at least 3 pp",
             "Not met", f"Not met: {num(r4['diff_pp'], 1, True)} pp against the 3 pp threshold "
                        f"(coverage {num(r4['delayed'], 3)} delayed, {num(r4['instant'], 3)} instant)"]),
        row(["R5", "Power: MDE undefined or above 7 pp is inconclusive regardless of $p$",
             "Inconclusive", "All four primary contrasts inconclusive (MDE undefined on the full hold-out sample)"]),
        "\\midrule",
        "\\multicolumn{4}{l}{\\emph{Extension, second hold-out panel (10 countries, four base models, warm-up 48 primary)}} \\\\",
        row(["E1", "Replication of R1, R2, R3 on new countries, same rule and direction",
             "Partly",
             "R1 met for all four base models at both horizons (not met at warm-up 96); R2 met at $h=3$ for LightGBM, ARIMA and "
             "naive B and at $h=6$ for ARIMA and naive B (Chronos at $h=3$ inconclusive under E5); R3 inconclusive"]),
        row(["E2", "Dependence on the base model: contrasts side by side, no threshold",
             "Descriptive", "R1 and R3 do not depend on the base model; R2 at $h=6$ does (ARIMA, naive B met; LightGBM, Chronos not met)"]),
        row(["E3", "Point accuracy of Chronos: relative MAE with bootstrap interval, descriptive",
             "Descriptive",
             "Relative MAE of Chronos on clean months " + ", ".join(num(v, 3) for v in rel) + " at $h=1,3,6,12$; "
             "no interval favours LightGBM or ARIMA"]),
        row(["E4", "Leakage: accuracy claims only from target months from 2025-01",
             "Applied", f"{n_months} months, {n_cells} country-month cells per horizon, 30 countries; the 2025-01 cutoff is an assumption, not verified"]),
        row(["E5", "Power: MDE undefined or above 7 pp is inconclusive",
             "Applied",
             f"MDE of ACI $-$ rolling {num(e5['lo'], 1)} to {num(e5['hi'], 1)} pp at warm-up 48, undefined for {und}; "
             "undefined for every DRACP $-$ ACI contrast and for all contrasts at warm-up 96"]),
    ]
    spec = "p{0.05\\linewidth}p{0.36\\linewidth}p{0.11\\linewidth}p{0.38\\linewidth}"
    return tabular(spec, ["Rule", "Statement", "Status", "Outcome as recorded"], rows)


TABLES = {
    "tab_panels.tex": tab_panels,
    "tab_methods.tex": tab_methods,
    "tab_ce_exploratory.tex": tab_ce_exploratory,
    "tab_ce_holdout1.tex": tab_ce_holdout1,
    "tab_ce_holdout2.tex": tab_ce_holdout2,
    "tab_contrasts_primary.tex": tab_contrasts_primary,
    "tab_tost.tex": tab_tost,
    "tab_winkler_width.tex": tab_winkler_width,
    "tab_ablation_basemodel.tex": tab_ablation_basemodel,
    "tab_ablation_warmup.tex": tab_ablation_warmup,
    "tab_feedback_delay.tex": tab_feedback_delay,
    "tab_native_vs_aci.tex": tab_native_vs_aci,
    "tab_chronos_mae.tex": tab_chronos_mae,
    "tab_rules.tex": tab_rules,
}
