"""Build the compact, precomputed benchmark JSON served by GET /api/v1/inflation/benchmark.

Offline and deterministic: reads only committed result files (docs/thesis/results/**) through
the paper pipeline helpers (scripts/thesis/paper/common.py, which also holds the E5/R5 rule),
and writes backend/fastapi_service/app/data/thesis_benchmark.json. No timestamp is written, so
re-running produces a byte-identical file.

Run from scripts/thesis with the venv interpreter:

    .venv/Scripts/python.exe build_demo_data.py            # write the file
    .venv/Scripts/python.exe build_demo_data.py --check    # fail if the committed file is stale

Every entry carries an honesty tag:
  status   'pre-specified' (written in the protocol before the computation), 'exploratory'
           (design panel), or 'post hoc' (added after results were seen)
  verdict  'shown' / 'not shown' / 'inconclusive' for primary contrasts. Rule R5/E5: an MDE that
           is undefined or above 7 pp is 'inconclusive' regardless of the p value.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "paper"))

import common as c  # noqa: E402  (paper pipeline helpers)

OUT = c.REPO / "backend" / "fastapi_service" / "app" / "data" / "thesis_benchmark.json"
SCHEMA_VERSION = 1
GENERATED = "scripts/thesis/build_demo_data.py (deterministic; no timestamp)"

# run id -> (panel key, status tag)
CE_RUNS = {
    "expl48": ("expl", "exploratory"),
    "hold48": ("hold1", "pre-specified"),
    "h2_48": ("hold2", "pre-specified"),
}
RUN_STATUS = {
    "expl48": "exploratory",
    "hold48": "pre-specified",
    "d13r": "pre-specified (secondary)",
    "h1r": "pre-specified (secondary)",
    "h2_48": "pre-specified",
}
VERDICT_MAP = {"Met": "shown", "Not met": "not shown", "Inconclusive": "inconclusive", "Not assessed": "not assessed"}
CONTRAST_TEXT = {
    "aci-rolling": "ACI minus rolling window (negative = ACI better calibrated)",
    "dracp-aci": "DRACP minus ACI (negative = DRACP better calibrated)",
    "aci-split": "ACI minus one-shot split calibration (negative = ACI better calibrated)",
}
PANEL_INFO = {
    "expl": {"label": "Design panel (13 countries)", "n_countries": 13, "status": "exploratory",
             "note": "Used to design the study; target months up to 2025-05."},
    "hold1": {"label": "Hold-out 1 (7 countries)", "n_countries": 7, "status": "pre-specified",
              "note": "Untouched countries; rules R1-R5 applied as written."},
    "hold2": {"label": "Hold-out 2 (10 countries)", "n_countries": 10, "status": "pre-specified",
              "note": "Second hold-out; extension rules E1-E5 (specified before any forecast)."},
    "d13r": {"label": "Design (13), from 2010", "n_countries": 13, "status": "pre-specified (secondary)",
             "note": "Re-run from 2010 for the base-model comparison."},
    "h1r": {"label": "Hold-out 1 (7), from 2010", "n_countries": 7, "status": "pre-specified (secondary)",
            "note": "Re-run from 2010 for the base-model comparison."},
}
SOURCES: set[str] = set()


def rel(p: str) -> str:
    SOURCES.add(f"docs/thesis/results/{p}")
    return p


def f(x, d: int = 4):
    """Round to d decimals; NaN/None -> None (JSON null)."""
    if x is None:
        return None
    x = float(x)
    if math.isnan(x) or math.isinf(x):
        return None
    r = round(x, d)
    return 0.0 if r == 0 else r


def build_ce() -> list[dict]:
    rows = []
    for run, (panel, status) in CE_RUNS.items():
        rel(f"{c.RUNS[run]['dir']}/interval_summary.csv")
        t = c.ce_table(run)
        cov = c.per_unit(run).groupby(["model", "method", "h"])["coverage"].mean().reset_index()
        t = t.merge(cov, on=["model", "method", "h"])
        for r in t.sort_values(["model", "method", "h"]).itertuples():
            rows.append({
                "panel": panel, "base_model": r.model, "method": r.method, "h": int(r.h),
                "ce_pp": f(r.ce * 100, 3), "mean_coverage": f(r.coverage, 4), "n_units": int(r.n_units),
                "status": "post hoc" if r.method == "native" else status,
            })
    return rows


def build_contrasts() -> list[dict]:
    out = []
    for run, model in c.CONTRAST_SETS:
        d = c.ce_dir(run, model)
        rel(f"{d}/calibration_contrasts.csv")
        if c.exists(f"{d}/power_mde_ce.csv"):
            rel(f"{d}/power_mde_ce.csv")
        x = c.contrasts(run, model)
        for r in x.sort_values(["family", "contrast", "h"]).itertuples():
            primary = r.family == "primary"
            if primary:
                v = VERDICT_MAP[c.verdict(r.contrast, r.T_pp, r.p_holm, r.mde_pp, bool(r.mde_computed))]
            else:
                v = "descriptive"  # secondary: no Holm adjustment and no MDE
            out.append({
                "panel": c.RUNS[run]["panel"], "run": run, "base_model": model, "h": int(r.h),
                "contrast": r.contrast, "family": r.family, "status": RUN_STATUS[run],
                "diff_pp": f(r.T_pp, 2), "ci_lo_pp": f(r.ci_lo_pp, 2), "ci_hi_pp": f(r.ci_hi_pp, 2),
                "p": f(r.p, 4), "p_holm": f(r.p_holm, 4) if primary else None,
                "mde_pp": f(r.mde_pp, 2),
                "mde_over_limit": bool(c.is_inconclusive(r.mde_pp)) if primary else None,
                "verdict": v, "n_units": int(r.n_units), "n_months": int(r.n_months),
                "ci_excludes_zero": bool(r.ci_lo_pp > 0 or r.ci_hi_pp < 0),
            })
    # Panel dependence: the same (contrast, base model, h) gets different verdicts on different panels.
    groups: dict[tuple, set] = {}
    for e in out:
        if e["family"] == "primary":
            groups.setdefault((e["contrast"], e["base_model"], e["h"]), set()).add(e["verdict"])
    for e in out:
        e["panel_dependent"] = bool(e["family"] == "primary" and len(groups[(e["contrast"], e["base_model"], e["h"])]) > 1)
    return out


def build_chronos() -> list[dict]:
    a = c.load(rel("extension_accuracy/e3_e4_clean_months.csv"))
    return [{
        "h": int(r.h), "comparison": r.comparison, "months": int(r.months), "cells": int(r.cells),
        "mae_diff": f(r.mean_abs_error_diff, 4), "ci_lo": f(r.ci_lo, 4), "ci_hi": f(r.ci_hi, 4),
        "rel_mae_chronos": f(r.rel_mae_chronos, 3), "rel_mae_other": f(r.rel_mae_other, 3),
        "status": "pre-specified",
    } for r in a.sort_values(["h", "comparison"]).itertuples()]


def build_feedback() -> list[dict]:
    out = []
    for panel, d in (("expl", "explore_v1"), ("hold1", "holdout_ncal48")):
        x = c.load(rel(f"{d}/robust/s3_feedback_diff.csv"))
        x = x[(x.unit == "ALL") & (x.h == 12) & (x.n_cal == 48) & (x.model == "lgbm")]
        for r in x.sort_values("method").itertuples():
            out.append({
                "panel": panel, "method": r.method, "h": 12, "cov_delayed": f(r.cov_delayed, 4),
                "cov_instant": f(r.cov_instant, 4), "diff_pp": f(r.diff * 100, 2),
                "ci_lo_pp": f(r.ci_lo * 100, 2), "ci_hi_pp": f(r.ci_hi * 100, 2),
                "cells": int(r.cells_paired), "status": "pre-specified (secondary S3)",
            })
    return out


def build_native() -> dict:
    ce = c.load(rel("extra_descriptive/s7_native_ce.csv"))
    ce = ce[(ce.model == "arima") & (ce.method.isin(["aci", "native"]))]
    vs = c.load(rel("extra_descriptive/s7_aci_vs_native_arima.csv"))
    return {
        "status": "post hoc",
        "ce": [{"sample": r.sample, "method": r.method, "h": int(r.h), "mean_coverage": f(r.mean_coverage, 4),
                "ce_pp": f(r.mean_ce * 100, 3)} for r in ce.sort_values(["sample", "method", "h"]).itertuples()],
        "aci_minus_native": [{"sample": r.sample, "h": int(r.h), "diff_pp": f(r.T * 100, 2),
                              "ci_lo_pp": f(r.ci_lo * 100, 2), "ci_hi_pp": f(r.ci_hi * 100, 2), "p": f(r.p, 4)}
                             for r in vs.sort_values(["sample", "h"]).itertuples()],
        "note": "ARIMA base model. Native = Gaussian model-based interval; ACI = conformal. Secondary, unadjusted, post hoc.",
    }


def build_commodity() -> dict:
    w = c.load(rel("commodity_criterion/country_classification_wide.csv"))
    countries = []
    for r in w.sort_values("country").itertuples():
        share = None if r.share_2021_2023 != r.share_2021_2023 else float(r.share_2021_2023)
        countries.append({
            "code": r.country, "name": r.name, "panel": r.panel, "share_2021_2023": f(share, 1),
            "qualifies_60": bool(share is not None and share >= 60.0),
            "class": r.class_2021_2023,
        })
    cb = c.load(rel("commodity_criterion/ce_by_class.csv"))
    cb = cb[(cb.cut == "pooled30") & (cb.level == 60) & (cb.method.isin(["aci", "rolling", "split"]))]
    return {
        "status": "post hoc",
        "criterion": "UNCTAD: commodities >= 60% of allocated merchandise exports (3-year mean 2021-2023)",
        "source": "UNCTAD, The State of Commodity Dependence 2025 (UNCTAD/DITC/COM/2025/3)",
        "n_qualifying": sum(1 for x in countries if x["qualifies_60"]),
        "n_countries": len(countries),
        "countries": countries,
        "ce_by_class": [{"group": r.group, "method": r.method, "h": int(r.h), "n_countries": int(r.n_countries),
                         "ce_pp": f(r.mean_ce * 100, 3)} for r in cb.sort_values(["group", "method", "h"]).itertuples()],
        "note": ("Descriptive and post hoc. Three countries (Mexico, Indonesia, Georgia) do not reach 60%; "
                 "with so few non-qualifying countries any comparison of the two groups is inconclusive."),
    }


def build_llm() -> dict:
    out = {}
    for ver, d, cond, lang, status in (
        ("v1", "llm_eval_qwen", "summary_condition.csv", "summary_condition_language.csv", "pre-specified"),
        ("v2", "llm_eval_qwen_v2", "summary_v2_condition.csv", "summary_v2_condition_language.csv", "post hoc"),
    ):
        rows = []
        for fn, by in ((cond, "condition"), (lang, "condition_language")):
            x = c.load(rel(f"{d}/{fn}"))
            for r in x.itertuples():
                rows.append({
                    "by": by, "condition": r.condition, "language": getattr(r, "language", None) if by != "condition" else None,
                    "n": int(r.n),
                    "faithful": int(r.faithful), "faithful_rate": f(r.faithful_rate, 4),
                    "faithful_lo": f(r.faithful_lo, 4), "faithful_hi": f(r.faithful_hi, 4),
                    "omission_rate": f(r.omission_rate, 4), "overstatement": int(r.overstatement),
                    "overstatement_rate": f(r.overstatement_rate, 4),
                })
        out[ver] = {
            "status": status,
            "metrics": ("Pre-specified metrics (sign handling and keyword rules as first written)" if ver == "v1"
                        else "Post hoc corrected metrics (two metric defects fixed after the v1 results were seen)"),
            "rows": rows,
        }
    out["model_note"] = "One open-weight model (Qwen via the project proxy), 468 answers per condition, 13 countries x 4 horizons x 3 question types x 3 languages."
    return out


def build() -> dict:
    data = {
        "schema_version": SCHEMA_VERSION,
        "generated": GENERATED,
        "nominal": c.NOMINAL,
        "mde_limit_pp": c.MDE_LIMIT_PP,
        "rule_note": "R5/E5: a contrast whose minimum detectable difference is undefined or above 7 pp is inconclusive regardless of its p value.",
        "panels": PANEL_INFO,
        "methods": {m: c.METHOD_LABEL[m] for m in [*c.METHODS, "native"]},
        "base_models": {m: c.MODEL_LABEL[m] for m in ("lgbm", "arima", "naive_b", "chronos")},
        "contrast_text": CONTRAST_TEXT,
        "headline": [
            "ACI is better calibrated than one-shot split calibration, consistently across panels and base models (secondary contrast, unadjusted).",
            "ACI's advantage over a rolling window depends on the panel and the base model; where power is too low it is inconclusive.",
            "DRACP versus ACI is inconclusive: the minimum detectable difference is undefined or above 7 pp.",
        ],
        "ce": build_ce(),
        "contrasts": build_contrasts(),
        "chronos_accuracy": {
            "note": "Clean target months only (from 2025-01); 30 countries; descriptive.",
            "rows": build_chronos(),
        },
        "feedback_delay_h12": build_feedback(),
        "native_vs_aci": build_native(),
        "commodity": build_commodity(),
        "llm_eval": build_llm(),
    }
    data["sources"] = sorted(SOURCES)
    return data


def dump(data: dict) -> str:
    # One line per top-level key keeps diffs reviewable while the file stays small.
    parts = []
    for k, v in data.items():
        parts.append(f"{json.dumps(k)}:{json.dumps(v, ensure_ascii=False, separators=(',', ':'))}")
    return "{\n" + ",\n".join(parts) + "\n}\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="exit 1 if the committed file differs")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    text = dump(build())
    out = Path(a.out)
    if a.check:
        ok = out.exists() and out.read_text(encoding="utf-8") == text
        print("up to date" if ok else "STALE: run build_demo_data.py")
        return 0 if ok else 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {out} ({len(text)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
