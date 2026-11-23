"""Commodity-dependence classification of the 30 thesis countries (protocol, tenth Changes entry).

Post hoc, descriptive.  Offline: reads only data/commodity/unctad_scd2025_profiles.csv (extracted from
UNCTAD, The State of Commodity Dependence 2025, see extract_unctad_profiles.py) and the committed
interval_summary.csv files.  No forecast is recomputed and no hypothesis test is run.

Criterion (fixed before running): share of commodity exports in allocated merchandise exports,
3-year average; primary window 2021-2023, second window 2012-2014.
  share >= 60  -> 'strong' (UNCTAD rule), 40 <= share < 60 -> 'moderate', share < 40 -> 'not'.

Usage: python commodity_criterion.py   (from scripts/thesis; writes docs/thesis/results/commodity_criterion/
and docs/thesis/results-commodity-v1.md)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROFILES = HERE / "data" / "commodity" / "unctad_scd2025_profiles.csv"
RES = ROOT / "docs" / "thesis" / "results"
OUT = RES / "commodity_criterion"
MD = ROOT / "docs" / "thesis" / "results-commodity-v1.md"

SOURCE = ("UNCTAD, The State of Commodity Dependence 2025 (UNCTAD/DITC/COM/2025/3), country profiles; "
          "https://unctad.org/system/files/official-document/ditccom2025d3_en.pdf; retrieved 2026-11-23; "
          "PDF sha256 e0799b129601d5c1dd5182cdc7110d2a313cd344a4d0ccad9b1573565a7c3122")
T_STRONG, T_MOD = 60.0, 40.0
WINDOWS = {"2021-2023": "share_2021_2023", "2012-2014": "share_2012_2014"}
PRIMARY = "2021-2023"

PANELS = {
    "design13": ["KZ", "RU", "AZ", "UZ", "CO", "CL", "PE", "BR", "MX", "NG", "MN", "ID", "ZA"],
    "holdout1": ["BO", "PY", "UY", "GH", "GE", "KG", "AO"],
    "holdout2": ["ZM", "AM", "TZ", "UG", "KE", "IQ", "BW", "NA", "MZ", "CI"],
}
# ISO-2 code (as used in the result tables) -> name in the UNCTAD profile pages
NAMES = {
    "KZ": "Kazakhstan", "RU": "Russian Federation (the)", "AZ": "Azerbaijan", "UZ": "Uzbekistan",
    "CO": "Colombia", "CL": "Chile", "PE": "Peru", "BR": "Brazil", "MX": "Mexico", "NG": "Nigeria",
    "MN": "Mongolia", "ID": "Indonesia", "ZA": "South Africa", "BO": "Bolivia (Plurinational State of)",
    "PY": "Paraguay", "UY": "Uruguay", "GH": "Ghana", "GE": "Georgia", "KG": "Kyrgyzstan", "AO": "Angola",
    "ZM": "Zambia", "AM": "Armenia", "TZ": "United Republic of Tanzania (the)", "UG": "Uganda",
    "KE": "Kenya", "IQ": "Iraq", "BW": "Botswana", "NA": "Namibia", "MZ": "Mozambique",
    "CI": "Côte d’Ivoire",
}
# cut -> (results dir, sample label); primary configuration (LightGBM base, warm-up 48)
CE_SOURCES = {
    "design13_exploratory": ("explore_v1", "exploratory"),
    "design13_confirmatory": ("confirm13", "confirmatory"),
    "holdout1": ("holdout_ncal48", "holdout"),
    "holdout2": ("holdout2_ncal48", "holdout2"),
}
POOLED_30 = ["design13_exploratory", "holdout1", "holdout2"]   # each country once, main sample
NOMINAL = 0.90
HS = (1, 3, 6, 12)


def classify(share) -> str:
    if share is None or pd.isna(share):
        return "missing"
    if share >= T_STRONG:
        return "strong"
    if share >= T_MOD:
        return "moderate"
    return "not"


def classification(profiles: pd.DataFrame | None = None) -> pd.DataFrame:
    p = pd.read_csv(PROFILES, keep_default_na=False, na_values=[""]) if profiles is None else profiles
    p = p.set_index("country_name_pdf")
    rows = []
    for panel, codes in PANELS.items():
        for c in codes:
            for w, col in WINDOWS.items():
                share = p.loc[NAMES[c], col] if NAMES[c] in p.index else np.nan
                rows.append({"country": c, "name": NAMES[c], "panel": panel, "share": share, "window": w,
                             "class": classify(share), "source": SOURCE})
    return pd.DataFrame(rows)


def wide(cl: pd.DataFrame) -> pd.DataFrame:
    a = cl[cl.window == PRIMARY].set_index("country")
    b = cl[cl.window != PRIMARY].set_index("country")
    w = a[["name", "panel", "share", "class"]].rename(columns={"share": "share_2021_2023", "class": "class_2021_2023"})
    w["share_2012_2014"] = b["share"]
    w["class_2012_2014"] = b["class"]
    return w.reset_index()


def counts(w: pd.DataFrame, col: str = "class_2021_2023") -> pd.DataFrame:
    rows = []
    for panel in list(PANELS) + ["all30"]:
        g = w if panel == "all30" else w[w.panel == panel]
        rows.append({"panel": panel, "n": len(g), "ge60": int((g[col] == "strong").sum()),
                     "ge40": int(g[col].isin(["strong", "moderate"]).sum()),
                     "moderate": int((g[col] == "moderate").sum()), "below40": int((g[col] == "not").sum()),
                     "missing": int((g[col] == "missing").sum())})
    return pd.DataFrame(rows)


def per_country_ce(res_root: Path = RES) -> pd.DataFrame:
    """Per-country coverage and CE of the primary configuration (lgbm) from committed interval_summary.csv."""
    out = []
    for key, (d, sample) in CE_SOURCES.items():
        x = pd.read_csv(res_root / d / "interval_summary.csv", keep_default_na=False)
        x = x[(x.model == "lgbm") & (x["sample"] == sample) & (x.unit != "ALL") & x.h.isin(HS)]
        x = x[["method", "h", "unit", "n", "coverage"]].copy()
        x["panel_sample"] = key
        x["ce"] = (x.coverage - NOMINAL).abs()
        out.append(x)
    return pd.concat(out, ignore_index=True)


def ce_by_class(ce: pd.DataFrame, w: pd.DataFrame, level: int) -> pd.DataFrame:
    ok = ["strong"] if level == 60 else ["strong", "moderate"]
    cls = w.set_index("country")["class_2021_2023"]
    d = ce.copy()
    c = d.unit.map(cls)
    d["qualifies"] = c.isin(ok)
    d = d[c.notna() & (c != "missing")]
    parts = {k: d[d.panel_sample == k] for k in CE_SOURCES}
    parts["pooled30"] = d[d.panel_sample.isin(POOLED_30)]
    rows = []
    for k, g in parts.items():
        for (m, h, q), gg in g.groupby(["method", "h", "qualifies"]):
            rows.append({"cut": k, "level": level, "group": "qualify" if q else "not_qualify", "method": m, "h": h,
                         "n_countries": gg.unit.nunique(), "mean_ce": gg.ce.mean(), "mean_coverage": gg.coverage.mean()})
    return pd.DataFrame(rows)


def _fmt_table(df, cols):
    s = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    for _, r in df.iterrows():
        s += "| " + " | ".join(str(r[c]) for c in cols) + " |\n"
    return s


def _cell(t, cut, level, method, h):
    out = []
    for grp in ("qualify", "not_qualify"):
        r = t[(t.cut == cut) & (t.level == level) & (t.method == method) & (t.h == h) & (t.group == grp)]
        out.append("-" if r.empty else f"{100 * r.mean_ce.iloc[0]:.1f} (n={int(r.n_countries.iloc[0])})")
    return out


def ce_table_md(t, level, cuts, methods, hs):
    s = ("| Method | h | " + " | ".join(f"{c}: qualify / not" for c in cuts) + " |\n|---|---|"
         + "---|" * len(cuts) + "\n")
    for m in methods:
        for h in hs:
            cells = []
            for c in cuts:
                a, b = _cell(t, c, level, m, h)
                cells.append(f"{a} / {b}")
            s += f"| {m} | {h} | " + " | ".join(cells) + " |\n"
    return s


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cl = classification()
    cl.to_csv(OUT / "country_classification.csv", index=False, encoding="utf-8")
    w = wide(cl)
    w.to_csv(OUT / "country_classification_wide.csv", index=False, encoding="utf-8")
    c1, c2 = counts(w), counts(w, "class_2012_2014")
    ce = per_country_ce()
    t60, t40 = ce_by_class(ce, w, 60), ce_by_class(ce, w, 40)
    pd.concat([t60, t40]).to_csv(OUT / "ce_by_class.csv", index=False, encoding="utf-8")

    wm = w.copy()
    wm["share_2021_2023"] = wm["share_2021_2023"].map(lambda v: f"{v:.1f}")
    wm["share_2012_2014"] = wm["share_2012_2014"].map(lambda v: f"{v:.1f}")
    fails60 = w[w.class_2021_2023 != "strong"]
    changed = w[w.class_2021_2023 != w.class_2012_2014]
    exact60 = w[(w.share_2021_2023 == 60.0) | (w.share_2012_2014 == 60.0)]
    cuts = ["design13_exploratory", "holdout1", "holdout2", "pooled30"]
    methods = ["split", "rolling", "aci", "dracp"]
    exact_txt = ("no country has a share of exactly 60.0, so >= and > coincide.\n" if exact60.empty else
                 "countries with a share of exactly 60.0: " + ", ".join(exact60.country) + ".\n")
    md = ["# Commodity-dependence classification of the 30 countries (post hoc, descriptive), v1 (2026-11-23)\n",
          "Status: **post hoc, descriptive**. Criterion fixed in the tenth entry of `experiment-protocol.md`"
          " before the classification was run. No forecast was recomputed; no hypothesis test is reported.\n",
          "Reproduce: `scripts/thesis/.venv/Scripts/python.exe scripts/thesis/commodity_criterion.py`"
          " (offline; tests in `scripts/thesis/tests/test_commodity_criterion.py`). Tables: "
          "`results/commodity_criterion/`.\n",
          "## Source and definition\n",
          f"- {SOURCE}.",
          "- Indicator: commodity exports as a share of all allocated product exports (UNCTAD definition of"
          " commodities: primary commodities incl. energy, ores, metals, precious stones and non-monetary gold),"
          " 3-year average. Primary window 2021-2023; second window 2012-2014. The average over each country's"
          " own sample is not available from this source and is not computed.",
          "- Extraction check: the extracted profile table reproduces the report's headline counts exactly"
          " (103 dependent economies at 2021-2023, 106 at 2012-2014).",
          "- Vintage: report of July 2025 on UNCTADstat data of November 2024, i.e. a pre-2026 vintage; the"
          " export structure of 2024-2025 is not covered. A machine-readable UNCTADstat table was not found; the"
          " numbers come from the PDF profile pages through `scripts/thesis/extract_unctad_profiles.py`"
          " (needs `pdftotext`).",
          "- Class: share >= 60 strong (UNCTAD rule), 40-60 moderate, < 40 not. The report states the rule as"
          " 'more than 60'; " + exact_txt,
          "## Classification\n",
          _fmt_table(wm, ["country", "name", "panel", "share_2021_2023", "class_2021_2023",
                          "share_2012_2014", "class_2012_2014"]),
          "## Counts (primary window 2021-2023)\n", _fmt_table(c1, list(c1.columns)),
          "Second window 2012-2014:\n", _fmt_table(c2, list(c2.columns)),
          "Not qualifying at 60% (2021-2023): "
          + ", ".join(f"{r.country} ({r.share_2021_2023:.1f})" for r in fails60.itertuples()) + ".\n",
          "Countries whose class differs between the two windows: "
          + (", ".join(f"{r.country} ({r.class_2012_2014} -> {r.class_2021_2023})" for r in changed.itertuples())
             or "none") + ".\n",
          "Missing in the source: " + (", ".join(w[w.class_2021_2023 == "missing"].country) or "none")
          + ". Nothing is imputed.\n",
          "## Descriptive cut of existing results (calibration error by class)\n",
          "Source: committed `interval_summary.csv` of `explore_v1` (design 13, exploratory sample), `holdout_ncal48`,"
          " `holdout2_ncal48`; LightGBM base, warm-up 48, nominal 0.90. Cell = mean over countries of"
          " |coverage - 0.90| in percentage points (CE), with the number of countries n (qualify / not). `pooled30` ="
          " design exploratory + hold-out 1 + hold-out 2 (each country once). The design-panel confirmatory months"
          " (`confirm13`, at most 16 per unit) are in the CSV only. Nothing is tested: subsets of 1-9 countries"
          " with dependent errors have no power calculation here, the block bootstrap of `exp/calibration.py`"
          " tests contrasts between methods, not differences between subsets, and is not reused (E5/R5 rule:"
          " undefined power means inconclusive). Differences are descriptive and inconclusive; no"
          " 'no difference' conclusion is drawn.\n",
          "### Qualify = share >= 60%\n", ce_table_md(t60, 60, cuts, methods, (3, 6)),
          "### Qualify = share >= 40%\n", ce_table_md(t40, 40, cuts, methods, (3, 6)),
          "Full table (all 7 methods, h = 1, 3, 6, 12, mean coverage, confirmatory design months):"
          " `results/commodity_criterion/ce_by_class.csv`.\n"]
    extra = OUT / "consequences.md"
    if extra.exists():
        md.append(extra.read_text(encoding="utf-8"))
    MD.write_text("\n".join(md), encoding="utf-8")
    print(c1.to_string())
    print(c2.to_string())
    print(w.drop(columns=["name"]).to_string())


if __name__ == "__main__":
    main()
