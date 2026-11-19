"""Tests of the paper asset pipeline.

Spot checks recompute values independently from the CSV files with the csv module (not with
the pipeline code) and compare them with the macros in numbers.tex.
"""
import csv
import re
from pathlib import Path

import pytest

from common import RESULTS, is_inconclusive, num, pval, verdict

EXPECTED_FIGURES = [
    "fig_pipeline.pdf", "fig_coverage_h.pdf", "fig_ce_bars.pdf", "fig_contrasts_forest.pdf",
    "fig_width_winkler.pdf", "fig_chronos_accuracy.pdf", "fig_country_coverage.pdf", "fig_warmup_sensitivity.pdf",
]
EXPECTED_TABLES = [
    "tab_panels.tex", "tab_methods.tex", "tab_ce_exploratory.tex", "tab_ce_holdout1.tex", "tab_ce_holdout2.tex",
    "tab_contrasts_primary.tex", "tab_tost.tex", "tab_winkler_width.tex", "tab_ablation_basemodel.tex",
    "tab_ablation_warmup.tex", "tab_feedback_delay.tex", "tab_native_vs_aci.tex", "tab_chronos_mae.tex", "tab_rules.tex",
]


# ---------- helpers (independent of the pipeline code) --------------------------------------
def rd(rel):
    with open(RESULTS / rel, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def macro_values(out: Path) -> dict:
    txt = (out / "numbers.tex").read_text(encoding="utf-8")
    vals = {}
    for m in re.finditer(r"^\\newcommand\{\\([A-Za-z]+)\}\{(.*?)\}( %.*)?$", txt, flags=re.M):
        vals[m.group(1)] = m.group(2)
    return vals


def plain(v: str) -> str:
    return v.replace("\\ensuremath{-}", "-").replace("\\ensuremath{<}", "<")


def split_cells(line: str):
    cells, depth, cur, i = [], 0, "", 0
    while i < len(line):
        c = line[i]
        if c == "\\" and i + 1 < len(line):
            cur += line[i:i + 2]
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        if c == "&" and depth == 0:
            cells.append(cur.strip())
            cur = ""
        else:
            cur += c
        i += 1
    cells.append(cur.strip())
    return cells


def ncols(spec: str) -> int:
    return len(re.findall(r"p\{[^}]*\}|[lcr]", spec))


# ---------- existence ------------------------------------------------------------------------
def test_all_outputs_exist_and_nonempty(built):
    out, made = built
    for f in EXPECTED_FIGURES:
        p = out / "figures" / f
        assert p.exists() and p.stat().st_size > 2000, f
    for t in EXPECTED_TABLES:
        p = out / "tables" / t
        assert p.exists() and p.stat().st_size > 100, t
    assert (out / "numbers.tex").stat().st_size > 1000


def test_figures_are_vector_pdfs(built):
    out, _ = built
    for f in EXPECTED_FIGURES:
        b = (out / "figures" / f).read_bytes()
        assert b.startswith(b"%PDF"), f
        assert b"/Subtype /Image" not in b and b"/Subtype/Image" not in b, f"{f} contains a raster image"


def test_repository_paper_dir_is_populated():
    """After running build_paper_assets.py the committed paper/ directory has every file."""
    from common import DEFAULT_OUT

    for f in EXPECTED_FIGURES:
        assert (DEFAULT_OUT / "figures" / f).stat().st_size > 2000, f
    for t in EXPECTED_TABLES:
        assert (DEFAULT_OUT / "tables" / t).stat().st_size > 100, t
    assert (DEFAULT_OUT / "numbers.tex").stat().st_size > 1000


def test_build_is_deterministic(built, tmp_path):
    from build_paper_assets import build

    out, _ = built
    build(tmp_path)
    for p in sorted(out.rglob("*")):
        if p.is_file():
            q = tmp_path / p.relative_to(out)
            assert q.read_bytes() == p.read_bytes(), f"{p.name} differs between two builds"


# ---------- table syntax ---------------------------------------------------------------------
@pytest.mark.parametrize("name", EXPECTED_TABLES)
def test_table_is_balanced_tabular(built, name):
    out, _ = built
    txt = (out / "tables" / name).read_text(encoding="utf-8")
    assert txt.count("\\begin{tabular}") == 1 and txt.count("\\end{tabular}") == 1
    assert "\\begin{table" not in txt and "\\caption" not in txt
    assert txt.replace("\\{", "").count("{") == txt.replace("\\}", "").count("}")
    lines = txt.strip().splitlines()
    assert lines[0].startswith("\\begin{tabular}{") and lines[-1] == "\\end{tabular}"
    assert "\\toprule" in txt and "\\bottomrule" in txt
    spec = re.match(r"\\begin\{tabular\}\{(.*)\}$", lines[0]).group(1)
    n = ncols(spec)
    for ln in lines[1:-1]:
        if ln.startswith(("\\toprule", "\\midrule", "\\bottomrule", "\\cmidrule")):
            continue
        assert ln.endswith("\\\\"), (name, ln)
        cells = split_cells(ln[:-2])
        total = 0
        for c in cells:
            m = re.match(r"\\multicolumn\{(\d+)\}", c)
            total += int(m.group(1)) if m else 1
        assert total == n, (name, n, total, ln)
        no_math = re.sub(r"\$[^$]*\$", "", ln)  # subscripts are legitimate inside math
        assert "_" not in no_math.replace("\\_", ""), (name, "unescaped underscore", ln)


# ---------- undefined MDE and rule E5 ---------------------------------------------------------
def test_undefined_mde_renders_as_dashes(built):
    out, _ = built
    txt = (out / "tables" / "tab_contrasts_primary.tex").read_text(encoding="utf-8")
    rows = [ln for ln in txt.splitlines() if "ACI $-$" in ln or "DRACP $-$" in ln]
    assert len(rows) == 40
    undefined = 0
    for ln in rows:
        cells = split_cells(ln[:-2])
        mde, ver = cells[-2], cells[-1]
        if mde == "--":
            undefined += 1
            assert ver == "Inconclusive", ln  # never 'no effect' for an undefined MDE
        else:
            assert float(mde) <= 7.0
            assert ver in ("Met", "Not met")
    assert undefined > 0
    # Chronos h=3 ACI - rolling on hold-out 2: Holm p 0.036 but MDE undefined
    chron = [ln for ln in rows if "Chronos" in ln and "Hold-out 2" in ln][0]
    cells = split_cells(chron[:-2])
    assert cells[2] == "3" and cells[6] == "0.036" and cells[7] == "--" and cells[8] == "Inconclusive"
    # every DRACP - ACI cell has an undefined MDE
    for ln in rows:
        if "DRACP $-$ ACI" in ln:
            assert split_cells(ln[:-2])[7] == "--"


def test_e5_rule_logic():
    nan = float("nan")
    assert is_inconclusive(nan) and is_inconclusive(7.01) and is_inconclusive(10.0)
    assert not is_inconclusive(7.0) and not is_inconclusive(1.2)
    assert verdict("aci-rolling", -3.7, 0.008, 3.2) == "Met"
    assert verdict("aci-rolling", -3.7, 0.008, nan) == "Inconclusive"  # significant but MDE undefined
    assert verdict("aci-rolling", -3.7, 0.008, 7.5) == "Inconclusive"
    assert verdict("aci-rolling", -3.5, 0.159, 6.1) == "Not met"
    assert verdict("aci-rolling", +1.0, 0.01, 3.0) == "Not met"  # wrong direction is not a success
    assert verdict("aci-rolling", -3.0, 0.01, nan, mde_computed=False) == "Not assessed"


def test_formatting_helpers():
    assert num(float("nan")) == "--"
    assert num(-0.04, 1) == "0.0"  # no negative zero
    assert num(-3.66, 1, True) == "$-$3.7" and num(0.2, 1, True) == "+0.2"
    assert pval(0.0004) == "$<$0.001" and pval(float("nan")) == "--"


# ---------- numbers.tex -------------------------------------------------------------------------
def test_macro_names_are_letters_only_and_unique(built):
    out, _ = built
    txt = (out / "numbers.tex").read_text(encoding="utf-8")
    names = re.findall(r"^\\newcommand\{\\([^}]*)\}", txt, flags=re.M)
    assert len(names) == len(set(names)) > 500
    assert all(re.fullmatch(r"[A-Za-z]+", n) for n in names)
    for key in ("NCountries", "NDesign", "NHoldoutOne", "NHoldoutTwo"):
        assert key in names


def test_numbers_manuscript_crosschecks(built):
    out, _ = built
    v = {k: plain(x) for k, x in macro_values(out).items()}
    models = ("Lgbm", "Arima", "NaiveB", "Chronos")
    assert [v[f"TppHoldTwo{m}AciRollThree"] for m in models] == ["-3.7", "-3.2", "-4.1", "-3.3"]
    assert [v[f"TppHoldTwo{m}DracpAciThree"] for m in models] == ["-1.0", "-1.5", "-1.2", "-0.5"]
    assert [v[f"RelMaeCleanChronos{h}"] for h in ("One", "Three", "Six", "Twelve")] == ["0.774", "0.699", "0.654", "0.895"]
    assert [v[f"RelMaeAllChronos{h}"] for h in ("One", "Three", "Six", "Twelve")] == ["0.737", "0.586", "0.581", "0.934"]
    assert v["NCountries"] == "30" and v["NDesign"] == "13" and v["NHoldoutOne"] == "7" and v["NHoldoutTwo"] == "10"
    assert v["NMonthsHoldTwoThree"] == "89" and v["NMonthsHoldTwoSix"] == "83"
    assert v["NMonthsWuNinetySixHoldTwoThree"] == "41" and v["NMonthsWuNinetySixHoldTwoSix"] == "35"
    assert v["RFourDiff"] == "2.4"


def test_numbers_match_independent_recomputation(built):
    """More than ten spot checks, computed straight from the CSV files with the csv module."""
    out, _ = built
    v = {k: plain(x) for k, x in macro_values(out).items()}
    checks = 0

    # calibration error from per-country coverage
    cases = [
        ("holdout2_ncal48", "lgbm", "aci", 3, "CEHoldTwoLgbmAciThree"),
        ("holdout2_ncal48", "arima", "native", 6, "CEHoldTwoArimaNativeSix"),
        ("explore_v1", "lgbm", "rolling", 3, "CEExplLgbmRollThree"),
        ("holdout_ncal48", "naive_b", "dracp", 12, "CEHoldOneNaiveBDracpTwelve"),
        ("holdout2_ncal96", "chronos", "split", 6, "CEWuNinetySixHoldTwoChronosSplitSix"),
    ]
    for rel, model, method, h, name in cases:
        rows = [r for r in rd(f"{rel}/interval_summary.csv")
                if r["model"] == model and r["method"] == method and r["h"] == str(h) and r["unit"] != "ALL"]
        want = sum(abs(float(r["coverage"]) - 0.9) for r in rows) / len(rows)
        assert v[name] == f"{want:.3f}", (name, v[name], want)
        checks += 1

    # pooled coverage
    for rel, model, method, h, name in [("explore_v1", "lgbm", "aci", 3, "CovExplLgbmAciThree"),
                                         ("holdout_ncal48", "lgbm", "split", 1, "CovHoldOneLgbmSplitOne")]:
        r = [r for r in rd(f"{rel}/interval_summary.csv")
             if r["unit"] == "ALL" and r["model"] == model and r["method"] == method and r["h"] == str(h)][0]
        assert v[name] == f"{float(r['coverage']):.3f}"
        checks += 1

    # contrasts, Holm, MDE
    c = {(r["h"], r["contrast"]): r for r in rd("holdout2_ncal48/ce_chronos/calibration_contrasts.csv")}
    assert v["TppHoldTwoChronosAciRollThree"] == f"{float(c[('3', 'aci-rolling')]['T']) * 100:.1f}"
    assert v["HolmHoldTwoChronosAciRollThree"] == f"{float(c[('3', 'aci-rolling')]['p_holm']):.3f}"
    checks += 2
    mde = {(r["h"], r["contrast"]): r["mde_pp"] for r in rd("holdout2_ncal48/ce_chronos/power_mde_ce.csv")}
    assert mde[("3", "aci-rolling")] == "" and v["MdeHoldTwoChronosAciRollThree"] == "--"
    assert v["MdeHoldTwoChronosAciRollSix"] == f"{float(mde[('6', 'aci-rolling')]):.1f}"
    checks += 2
    pl = {(r["h"], r["contrast"]): r for r in rd("explore_v1/calibration_contrasts.csv")}
    assert v["HolmExplLgbmAciRollThree"] == f"{float(pl[('3', 'aci-rolling')]['p_holm']):.3f}"
    checks += 1

    # Chronos clean-month MAE difference with CI
    e = {(r["h"], r["comparison"]): r for r in rd("extension_accuracy/e3_e4_clean_months.csv")}
    r = e[("12", "chronos - lgbm")]
    assert v["MaeDiffLgbmTwelve"] == f"{float(r['mean_abs_error_diff']):.3f}"
    assert v["MaeDiffLoLgbmTwelve"] == f"{float(r['ci_lo']):.3f}" and v["MaeDiffHiLgbmTwelve"] == f"{float(r['ci_hi']):.3f}"
    checks += 3

    # feedback delay, R4
    r = [r for r in rd("holdout_ncal48/robust/s3_feedback_diff.csv") if r["unit"] == "ALL" and r["method"] == "aci"][0]
    assert v["FbDelayedHoldOneAci"] == f"{float(r['cov_delayed']):.3f}"
    assert v["FbDiffHoldOneAci"] == f"{float(r['diff']) * 100:.1f}" == v["RFourDiff"]
    checks += 2

    # S4 and S7
    s4 = [r for r in rd("explore_v1/robust/s4_compact.csv") if r["method"] == "dracp"][0]
    assert v["WinklerRatioExplDracpThree"] == f"{float(s4['winkler_ratio_h3']):.2f}"
    s7 = [r for r in rd("extra_descriptive/s7_aci_vs_native_arima.csv") if r["sample"] == "holdout" and r["h"] == "6"][0]
    assert v["NatTppHoldOneSix"] == f"{float(s7['T']) * 100:.1f}" and v["NatPvalHoldOneSix"] == f"{float(s7['p']):.3f}"
    checks += 3

    # TOST
    t = [r for r in rd("holdout2_ncal48/ce_chronos/calibration_tost.csv") if r["h"] == "3"][0]
    assert v["TostPHoldTwoChronosDracpAciThree"] == f"{float(t['p_tost']):.3f}"
    checks += 1
    assert checks >= 10

    # verdict macros follow the rule
    assert v["VerdictHoldTwoLgbmAciRollThree"] == "Met"
    assert v["VerdictHoldTwoChronosAciRollThree"] == "Inconclusive"
    assert v["VerdictHoldTwoLgbmAciRollSix"] == "Not met"
    assert v["VerdictExplLgbmAciRollThree"] == "Inconclusive"
    assert int(v["NMet"]) + int(v["NNotMet"]) + int(v["NInconclusive"]) == int(v["NPrimaryContrasts"]) == 40


def test_ce_tables_match_ce_macros(built):
    """tab_ce_holdout2 cells equal the numbers.tex values and the manuscript's Table 14 (h=3)."""
    out, _ = built
    v = {k: plain(x) for k, x in macro_values(out).items()}
    txt = (out / "tables" / "tab_ce_holdout2.tex").read_text(encoding="utf-8")
    first = [ln for ln in txt.splitlines() if ln.startswith("LightGBM & Split")][0]
    assert split_cells(first[:-2])[3] == v["CEHoldTwoLgbmSplitThree"] == "0.104"
    aci = [ln for ln in txt.splitlines() if ln.startswith(" & ACI")]
    assert split_cells(aci[0][:-2])[3] == "0.033"  # LightGBM ACI h=3 (manuscript Table 14)


def test_tables_do_not_invent_cells(built):
    out, _ = built
    # hold-out 2 has no ETS and no contrast file for native: those cells are '--'
    txt = (out / "tables" / "tab_native_vs_aci.tex").read_text(encoding="utf-8")
    h2 = txt.split("Hold-out 2 (10)")[1]
    for ln in h2.splitlines():
        if ln.endswith("\\\\") and "&" in ln:
            cells = split_cells(ln[:-2])
            assert cells[4] == "--" and cells[5] == "--" and cells[6] == "--"
