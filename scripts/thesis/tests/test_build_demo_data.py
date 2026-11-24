"""The demo benchmark JSON is deterministic, matches the CSVs and applies rule R5/E5.

Run from scripts/thesis: .venv/Scripts/python.exe -m pytest tests/test_build_demo_data.py -q
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import build_demo_data as b  # noqa: E402


def test_build_is_deterministic_and_matches_committed_file():
    a = b.dump(b.build())
    assert a == b.dump(b.build())
    assert b.OUT.read_text(encoding="utf-8") == a


def test_verdicts_follow_r5_e5():
    d = json.loads(b.OUT.read_text(encoding="utf-8"))
    prim = [x for x in d["contrasts"] if x["family"] == "primary"]
    assert prim
    for x in prim:
        undefined_or_big = x["mde_pp"] is None or x["mde_pp"] > 7.0
        if undefined_or_big:
            assert x["verdict"] == "inconclusive", x
        else:
            assert x["verdict"] in ("shown", "not shown")
            assert (x["verdict"] == "shown") == (x["p_holm"] < 0.05 and x["diff_pp"] < 0)
    assert any(x["verdict"] == "shown" for x in prim)  # hold-out 2, ACI vs rolling, h=3


def test_ce_matches_csv_independently():
    d = json.loads(b.OUT.read_text(encoding="utf-8"))
    path = b.c.RESULTS / "holdout_ncal48" / "interval_summary.csv"
    vals = [abs(float(r["coverage"]) - 0.9) * 100 for r in csv.DictReader(open(path, encoding="utf-8"))
            if r["model"] == "lgbm" and r["method"] == "aci" and r["h"] == "3" and r["unit"] != "ALL"
            and r["sample"] == "holdout"]
    row = [x for x in d["ce"] if x["panel"] == "hold1" and x["base_model"] == "lgbm"
           and x["method"] == "aci" and x["h"] == 3][0]
    assert abs(row["ce_pp"] - sum(vals) / len(vals)) < 1e-3


def test_commodity_and_llm_numbers():
    d = json.loads(b.OUT.read_text(encoding="utf-8"))
    assert (d["commodity"]["n_qualifying"], d["commodity"]["n_countries"]) == (27, 30)
    low = {x["code"] for x in d["commodity"]["countries"] if not x["qualifies_60"]}
    assert low == {"MX", "ID", "GE"}
    v1 = {(r["by"], r["condition"]): r for r in d["llm_eval"]["v1"]["rows"]}
    v2 = {(r["by"], r["condition"]): r for r in d["llm_eval"]["v2"]["rows"]}
    assert v2[("condition", "grounded")]["faithful_rate"] == 1.0
    assert abs(v1[("condition", "grounded")]["faithful_rate"] - 0.906) < 1e-3
    assert d["llm_eval"]["v2"]["status"] == "post hoc" and d["llm_eval"]["v1"]["status"] == "pre-specified"
