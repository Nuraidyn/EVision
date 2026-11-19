import numpy as np
import pandas as pd
import pytest

from exp import robust as R


def _rows(unit, model, method, h, covered, width, winkler, sample="exploratory", start="2010-01"):
    n = len(covered)
    o = pd.period_range(start, periods=n, freq="M")
    return pd.DataFrame(dict(unit=unit, model=model, h=h, origin=o.astype(str), sample=sample, method=method,
                             covered=np.asarray(covered, float), width=width, winkler=winkler))


def _panel(n=60, units=8, driver="U0", h=3, seed=0, model="lgbm"):
    """aci covers 0.9 everywhere except unit `driver`, where rolling is far off (so aci-rolling < 0 only there)."""
    rng = np.random.default_rng(seed)
    parts = []
    for i in range(units):
        u = f"U{i}"
        base = (rng.random(n) < 0.9).astype(float)
        bad = (rng.random(n) < 0.5).astype(float)
        roll = bad if u == driver else base
        for m, cov in (("aci", base), ("rolling", roll), ("split", base), ("dracp", base)):
            parts.append(_rows(u, model, m, h, cov, 2.0 if m != "rolling" else 1.0,
                               3.0 if m != "rolling" else 2.0))
    return pd.concat(parts, ignore_index=True)


def test_s1_one_unit_drives_effect():
    iv = _panel()
    df = R.s1_leave_one_out(iv, "lgbm", "exploratory", B=100)
    s = df[(df.contrast == "aci-rolling") & (df.h == 3) & (df.removed_unit == "SUMMARY")].iloc[0]
    assert s["T"] < 0
    assert s["n_removals"] == 8
    assert s["n_sign_changes"] >= 1                     # removing the driver flips / nulls the sign
    r = df[(df.contrast == "aci-rolling") & (df.h == 3) & (df.removed_unit == "U0")].iloc[0]
    assert r["sign_change"] and r["n_units"] == 7
    assert s["T_min"] <= s["T"] or s["T_max"] >= s["T"]
    full = df[(df.contrast == "aci-rolling") & (df.h == 3) & (df.removed_unit == "NONE(full)")].iloc[0]
    assert full["T"] == pytest.approx(s["T"])


def test_s1_no_sign_change_when_all_units_agree():
    iv = _panel(driver="U0")
    iv.loc[(iv.method == "rolling"), "covered"] = (np.random.default_rng(5).random((iv.method == "rolling").sum()) < 0.4).astype(float)
    df = R.s1_leave_one_out(iv, "lgbm", "exploratory", B=50)
    s = df[(df.contrast == "aci-rolling") & (df.h == 3) & (df.removed_unit == "SUMMARY")].iloc[0]
    assert s["n_sign_changes"] == 0 and s["T_max"] < 0


def test_s1_rejects_confirmatory():
    iv = _panel()
    iv["sample"] = "confirmatory"
    with pytest.raises(ValueError):
        R.s1_leave_one_out(iv, "lgbm", "confirmatory", B=10)


def test_s2_other_models_and_tost():
    iv = pd.concat([_panel(model="lgbm"), _panel(model="arima", seed=3)], ignore_index=True)
    df = R.s2_other_models(iv, models=("lgbm", "arima", "naive_b"), sample="exploratory", B=100)
    assert set(df.model) == {"lgbm", "arima"}           # naive_b absent from the data -> skipped
    d = df[(df.contrast == "dracp-aci") & (df.h == 3)]
    assert len(d) == 2 and (d.tost_verdict == "equivalent").all()   # identical coverage -> T = 0
    assert df[df.contrast == "aci-rolling"].tost_verdict.isna().all()


def test_s3_pairing_on_identical_cells():
    n = 40
    cov_d = (np.arange(n) % 5 != 0).astype(float)       # 0.8
    cov_i = np.ones(n)                                    # 1.0 -> diff 0.2
    delayed = pd.concat([_rows(u, "lgbm", "aci", 12, cov_d, 1, 1) for u in ("A", "B")], ignore_index=True)
    instant = pd.concat([_rows(u, "lgbm", "aci", 12, cov_i, 1, 1) for u in ("A", "B")], ignore_index=True)
    df = R.s3_feedback(instant, delayed, "lgbm", "exploratory", methods=("aci",), B=200)
    a = df[df.unit == "ALL"].iloc[0]
    assert a["diff"] == pytest.approx(0.2) and a["cells_paired"] == 80
    assert 0.05 < a["ci_lo"] <= 0.2 <= a["ci_hi"] < 0.35
    assert len(df) == 3
    # unequal cells: instant has two extra cells for A; paired set stays 80
    extra = _rows("A", "lgbm", "aci", 12, [1, 1], 1, 1, start="2030-01")
    df2 = R.s3_feedback(pd.concat([instant, extra]), delayed, "lgbm", "exploratory", methods=("aci",), B=50)
    a2 = df2[df2.unit == "ALL"].iloc[0]
    assert a2["cells_paired"] == 80 and a2["cells_instant"] == 82 and a2["diff"] == pytest.approx(0.2)


def test_s4_reference_ratio_is_one():
    iv = _panel()
    s4 = R.s4_width_efficiency(iv, "lgbm", "exploratory", hs=(3,))
    r = s4[s4.method == "rolling"]
    assert np.allclose(r.winkler_ratio, 1.0) and np.allclose(r.width_ratio, 1.0)
    a = s4[(s4.method == "aci") & (s4.unit == "POOLED")].iloc[0]
    assert a["winkler_ratio"] == pytest.approx(1.5) and a["width_ratio"] == pytest.approx(2.0)
    c = R.s4_compact(s4)
    assert {"ce_h3", "winkler_ratio_h3", "width_ratio_h3"} <= set(c.columns)
    assert c.loc[c.method == "rolling", "winkler_ratio_h3"].iloc[0] == pytest.approx(1.0)
