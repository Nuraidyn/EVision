"""Shared paths, loaders and formatting helpers for the paper asset pipeline.

Everything is read from the committed CSV/JSON files (no network, no randomness).
"""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
RESULTS = REPO / "docs" / "thesis" / "results"
DATA = REPO / "scripts" / "thesis" / "data"
DEFAULT_OUT = REPO / "paper"

NOMINAL = 0.90
MDE_LIMIT_PP = 7.0  # rules R5 / E5: undefined or above 7 pp -> inconclusive

HORIZONS = [1, 3, 6, 12]
METHODS = ["split", "rolling", "aci", "faci", "pid", "dracp"]  # conformal, in table order
METHOD_LABEL = {
    "split": "Split",
    "rolling": "Rolling",
    "aci": "ACI",
    "faci": "FACI",
    "pid": "Conformal PID",
    "dracp": "DRACP",
    "native": "Native",
}
MODEL_LABEL = {
    "naive_b": "Naive B",
    "arima": "ARIMA",
    "lgbm": "LightGBM",
    "chronos": "Chronos",
    "ets": "ETS",
}

# Okabe-Ito (colourblind safe)
METHOD_COLOR = {
    "split": "#7f7f7f",
    "rolling": "#E69F00",
    "aci": "#0072B2",
    "faci": "#56B4E9",
    "pid": "#009E73",
    "dracp": "#D55E00",
    "native": "#CC79A7",
}
METHOD_MARKER = {"split": "s", "rolling": "D", "aci": "o", "faci": "^", "pid": "v", "dracp": "P", "native": "X"}

# --- panels -----------------------------------------------------------------------------

PANEL_LABEL = {
    "expl": "Design (13)",
    "hold1": "Hold-out 1 (7)",
    "hold2": "Hold-out 2 (10)",
    "d13r": "Design (13), from 2010",
    "h1r": "Hold-out 1 (7), from 2010",
}

# run id -> (directory, sample label in the CSV, warm-up)
RUNS = {
    "expl48": dict(panel="expl", dir="explore_v1", sample="exploratory", warm=48),
    "expl96": dict(panel="expl", dir="explore_v2_ncal96", sample="exploratory", warm=96),
    "hold48": dict(panel="hold1", dir="holdout_ncal48", sample="holdout", warm=48),
    "hold96": dict(panel="hold1", dir="holdout_ncal96", sample="holdout", warm=96),
    "h2_48": dict(panel="hold2", dir="holdout2_ncal48", sample="holdout2", warm=48),
    "h2_96": dict(panel="hold2", dir="holdout2_ncal96", sample="holdout2", warm=96),
    "d13r": dict(panel="d13r", dir="ext_design13", sample="exploratory", warm=48),
    "h1r": dict(panel="h1r", dir="ext_holdout1", sample="holdout", warm=48),
}

# (run id, base model) pairs for which calibration contrasts (with Holm p) exist.
# 'ce_dir' is the directory with calibration_contrasts.csv / calibration_tost.csv / power_mde_ce.csv
CONTRAST_SETS = [
    ("expl48", "lgbm"),
    ("hold48", "lgbm"),
    ("d13r", "lgbm"),
    ("d13r", "chronos"),
    ("h1r", "lgbm"),
    ("h1r", "chronos"),
    ("h2_48", "lgbm"),
    ("h2_48", "arima"),
    ("h2_48", "naive_b"),
    ("h2_48", "chronos"),
]
# warm-up 96 sets (sensitivity; used by TOST and warm-up ablation)
CONTRAST_SETS_96 = [
    ("expl96", "lgbm"),
    ("hold96", "lgbm"),
    ("h2_96", "lgbm"),
    ("h2_96", "arima"),
    ("h2_96", "naive_b"),
    ("h2_96", "chronos"),
]

COUNTRIES = {
    # design (13)
    "BR": "Brazil", "MX": "Mexico", "CL": "Chile", "CO": "Colombia", "PE": "Peru",
    "ZA": "South Africa", "ID": "Indonesia", "KZ": "Kazakhstan", "RU": "Russia",
    "AZ": "Azerbaijan", "UZ": "Uzbekistan", "NG": "Nigeria", "MN": "Mongolia",
    # hold-out 1 (7)
    "BO": "Bolivia", "PY": "Paraguay", "UY": "Uruguay", "GH": "Ghana", "GE": "Georgia",
    "KG": "Kyrgyzstan", "AO": "Angola",
    # hold-out 2 (10)
    "ZM": "Zambia", "AM": "Armenia", "TZ": "Tanzania", "UG": "Uganda", "KE": "Kenya",
    "IQ": "Iraq", "BW": "Botswana", "NA": "Namibia", "MZ": "Mozambique", "CI": "Cote d'Ivoire",
}
PANEL_UNITS = {
    "expl": ["BR", "MX", "CL", "CO", "PE", "ZA", "ID", "KZ", "RU", "AZ", "UZ", "NG", "MN"],
    "hold1": ["BO", "PY", "UY", "GH", "GE", "KG", "AO"],
    "hold2": ["ZM", "AM", "TZ", "UG", "KE", "IQ", "BW", "NA", "MZ", "CI"],
}
PANEL_JSON = {"expl": ["snapshot", "confirmatory"], "hold1": ["holdout"], "hold2": ["holdout2"]}
# analysis window (first origin cannot precede start; last target month of the labelled sample)
PANEL_WINDOW = {"expl": ("2000-01", "2025-06"), "hold1": ("2000-01", "2026-06"), "hold2": ("2010-01", "2026-06")}


# --- loading ----------------------------------------------------------------------------

def read_csv(path: Path) -> pd.DataFrame:
    """CSV reader that does not turn the country code NA (Namibia) into a missing value."""
    return pd.read_csv(path, keep_default_na=False, na_values=[""])


@lru_cache(maxsize=None)
def _cached(path: str) -> pd.DataFrame:
    return read_csv(Path(path))


def load(rel: str) -> pd.DataFrame:
    """Load a CSV below docs/thesis/results (cached; callers must not mutate)."""
    return _cached(str(RESULTS / rel)).copy()


def exists(rel: str) -> bool:
    return (RESULTS / rel).exists()


def summary(run: str) -> pd.DataFrame:
    s = load(f"{RUNS[run]['dir']}/interval_summary.csv")
    return s[s["sample"] == RUNS[run]["sample"]].copy()


def ce_dir(run: str, model: str) -> str:
    """Directory holding the calibration-error analysis of a (run, base model)."""
    d = RUNS[run]["dir"]
    if run in ("expl48", "expl96", "hold48", "hold96"):
        return d  # LightGBM analysis sits in the run root
    return f"{d}/ce_{model}"


def contrasts(run: str, model: str) -> pd.DataFrame:
    """Calibration contrasts with MDE merged in (mde_pp NaN = undefined or not computed)."""
    d = ce_dir(run, model)
    c = load(f"{d}/calibration_contrasts.csv")
    c = c[c["model"] == model].copy()
    c["T_pp"] = c["T"] * 100
    c["ci_lo_pp"] = c["ci_lo"] * 100
    c["ci_hi_pp"] = c["ci_hi"] * 100
    if exists(f"{d}/power_mde_ce.csv"):
        m = load(f"{d}/power_mde_ce.csv")
        m = m[m["model"] == model][["h", "contrast", "mde_pp"]]
        c = c.merge(m, on=["h", "contrast"], how="left")
        c["mde_computed"] = True
    else:
        c["mde_pp"] = np.nan
        c["mde_computed"] = False
    c["run"] = run
    c["panel"] = RUNS[run]["panel"]
    c["warm"] = RUNS[run]["warm"]
    return c


def tost(run: str, model: str) -> pd.DataFrame:
    d = ce_dir(run, model)
    t = load(f"{d}/calibration_tost.csv")
    t = t[t["model"] == model].copy()
    t["T_pp"] = t["T"] * 100
    t["run"] = run
    t["panel"] = RUNS[run]["panel"]
    t["warm"] = RUNS[run]["warm"]
    return t


# --- derived statistics -------------------------------------------------------------------

def per_unit(run: str) -> pd.DataFrame:
    s = summary(run)
    return s[s["unit"] != "ALL"].copy()


def pooled(run: str) -> pd.DataFrame:
    s = summary(run)
    return s[s["unit"] == "ALL"].copy()


def ce_table(run: str) -> pd.DataFrame:
    """CE (mean over units of |coverage - 0.90|), SD and SE across units, per (model, method, h)."""
    u = per_unit(run)
    u["ce"] = (u["coverage"] - NOMINAL).abs()
    g = u.groupby(["model", "method", "h"])["ce"]
    out = g.agg(ce="mean", sd="std", n_units="count").reset_index()
    out["se"] = out["sd"] / np.sqrt(out["n_units"])
    return out


def ce_value(run: str, model: str, method: str, h: int) -> float:
    t = ce_table(run)
    r = t[(t.model == model) & (t.method == method) & (t.h == h)]
    return float(r["ce"].iloc[0]) if len(r) else float("nan")


def is_inconclusive(mde_pp: float) -> bool:
    """Rules R5/E5: MDE undefined (NaN) or above 7 pp -> inconclusive."""
    return (mde_pp is None) or (isinstance(mde_pp, float) and math.isnan(mde_pp)) or mde_pp > MDE_LIMIT_PP


def verdict(contrast: str, t_pp: float, p_holm: float, mde_pp: float, mde_computed: bool = True) -> str:
    """Verdict of a primary contrast under R5/E5. Undefined or >7 pp MDE is INCONCLUSIVE, never 'no effect'."""
    if not mde_computed:
        return "Not assessed"
    if is_inconclusive(mde_pp):
        return "Inconclusive"
    if p_holm < 0.05 and t_pp < 0:
        return "Met"
    return "Not met"


# --- LaTeX formatting ---------------------------------------------------------------------

UNDEF = "--"


def _isnan(x) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x)) or (isinstance(x, (np.floating,)) and np.isnan(x))


def num(x, d: int = 3, signed: bool = False, macro: bool = False) -> str:
    """Fixed-decimal number; '--' for undefined. Negative values use a math minus.

    macro=True uses \\ensuremath{-} (usable in text and math), otherwise $-$ (tables).
    """
    if _isnan(x):
        return UNDEF
    r = round(float(x), d)
    if r == 0:
        r = 0.0
    s = f"{abs(r):.{d}f}"
    if r < 0:
        return ("\\ensuremath{-}" if macro else "$-$") + s
    return ("+" if signed else "") + s


def pval(p, macro: bool = False) -> str:
    if _isnan(p):
        return UNDEF
    if p < 0.001:
        return "\\ensuremath{<}0.001" if macro else "$<$0.001"
    return f"{p:.3f}"


def ci(lo, hi, d: int = 1, macro: bool = False) -> str:
    if _isnan(lo) or _isnan(hi):
        return UNDEF
    return f"[{num(lo, d, True, macro)}, {num(hi, d, True, macro)}]"


def tex_escape(s: str) -> str:
    for a, b in (("\\", "\\textbackslash{}"), ("&", "\\&"), ("%", "\\%"), ("_", "\\_"), ("#", "\\#")):
        s = s.replace(a, b)
    return s


def tabular(colspec: str, header: list[str] | None, body_lines: list[str]) -> str:
    """Assemble a booktabs tabular (no table float). body_lines are complete lines incl. \\\\ or rules."""
    out = [f"\\begin{{tabular}}{{{colspec}}}", "\\toprule"]
    if header:
        out.append(" & ".join(header) + " \\\\")
        out.append("\\midrule")
    out.extend(body_lines)
    out.append("\\bottomrule")
    out.append("\\end{tabular}")
    return "\n".join(out) + "\n"


def row(cells: list[str]) -> str:
    return " & ".join(cells) + " \\\\"


# --- panel data ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def cpi_series(unit: str) -> dict:
    """Merged CPI months of a unit from the committed snapshots (earlier snapshot wins on overlap)."""
    for panel, files in PANEL_JSON.items():
        if unit in PANEL_UNITS[panel]:
            merged: dict = {}
            for f in files:
                d = json.loads((DATA / f"{f}.json").read_text(encoding="utf-8"))
                for k, v in d["cpi"].get(unit, {}).items():
                    if v is not None and k not in merged:
                        merged[k] = v
            return merged
    raise KeyError(unit)


def panel_of(unit: str) -> str:
    for p, us in PANEL_UNITS.items():
        if unit in us:
            return p
    raise KeyError(unit)


def apply_style():
    import matplotlib as mpl

    mpl.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "font.family": "DejaVu Sans",
            "font.size": 8,
            "axes.titlesize": 8.5,
            "axes.labelsize": 8,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "legend.fontsize": 7.5,
            "legend.frameon": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.6,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "grid.color": "#dddddd",
            "grid.linewidth": 0.5,
            "lines.linewidth": 1.2,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.hashsalt": "evision",
        }
    )


def save_pdf(fig, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    # no creation date / producer string -> byte-reproducible output
    fig.savefig(path, format="pdf", bbox_inches="tight", metadata={"CreationDate": None, "Creator": "EVision paper pipeline", "Producer": "matplotlib"})
