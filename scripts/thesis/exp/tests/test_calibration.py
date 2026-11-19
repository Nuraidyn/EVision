import numpy as np
import pandas as pd

from exp.calibration import (ce_arrays, ce_contrast_test, ce_contrasts, ce_value, null_ce_bias,
                             per_unit_coverage, t_stat)
from exp.evaluate import holm


def make_iv(n_units=8, T=120, seed=0, h=3, extra_methods=False):
    """'good' hits with coverage 0.90 in every unit; 'bad' over-covers (0.99) in half of the units
    and under-covers (0.81) in the other half, so pooled coverage is also ~0.90."""
    rng = np.random.default_rng(seed)
    origins = [str(p) for p in pd.period_range("2010-01", periods=T, freq="M")]
    rows = []
    for u in range(n_units):
        pb = 0.99 if u % 2 == 0 else 0.81
        good = np.zeros(T)
        good[rng.permutation(T)[: int(round(0.9 * T))]] = 1
        bad = (rng.random(T) < pb).astype(float)
        for me, hits in (("split", bad), ("rolling", bad), ("aci", good), ("dracp", good)):
            rows.append(pd.DataFrame(dict(unit=f"U{u}", model="lgbm", h=h, sample="exploratory",
                                          method=me, origin=origins, covered=hits)))
    return pd.concat(rows, ignore_index=True)


def test_ce_definition():
    assert np.allclose(ce_value([0.8, 0.95, 0.9]), [0.1, 0.05, 0.0])
    iv = make_iv(n_units=2, T=20)
    pu = per_unit_coverage(iv, (3,))
    assert np.allclose(pu["ce"], (pu["coverage"] - 0.9).abs())
    assert set(pu.columns) >= {"model", "method", "h", "sample", "unit", "n", "coverage", "ce"}


def test_t_equal_weights_and_sign():
    # unit 1: a perfect (0.9) vs b 1.0 -> -0.1 ; unit 2: a 0.5 vs b 0.9 -> +0.4 ; mean 0.15
    Ha = np.array([[1] * 9 + [0], [1] * 5 + [0] * 5], float)
    Hb = np.array([[1] * 10, [1] * 9 + [0]], float)
    O = np.ones((2, 10))
    assert abs(t_stat(Ha, Hb, O) - 0.15) < 1e-12
    # replicate with the identity index reproduces the point estimate
    idx = np.arange(10)[None, :]
    assert abs(t_stat(Ha, Hb, O, idx)[0] - 0.15) < 1e-12


def test_calibrated_method_wins_while_pooled_coverage_cancels():
    iv = make_iv()
    for h in (3,):
        a = ce_arrays(iv, "lgbm", h, "aci", "split")
        Ha, Hb, O, _ = a
        assert abs(Ha.sum() / O.sum() - Hb.sum() / O.sum()) < 0.03     # pooled difference ~ 0
        r = ce_contrast_test(a, h, B=500)
        assert r["T"] < -0.05
        assert r["ci_hi"] < 0 and r["p"] < 0.01


def test_contrasts_table_and_holm():
    iv = make_iv()
    iv6 = make_iv(h=6, seed=1)
    con = ce_contrasts(pd.concat([iv, iv6], ignore_index=True), "lgbm", "exploratory", B=200)
    prim = con[con.family == "primary"]
    assert len(prim) == 4 and set(prim.h) == {3, 6}
    assert set(prim.contrast) == {"aci-rolling", "dracp-aci"}
    assert set(con[con.family == "secondary"].contrast) == {"aci-split"}
    assert con[con.family == "secondary"]["p_holm"].isna().all()
    adj = holm(prim["p"].tolist())
    assert np.allclose(prim["p_holm"], adj) and (prim["p_holm"] >= prim["p"] - 1e-12).all()
    assert np.allclose(prim[prim.contrast == "dracp-aci"]["T"], 0)     # identical methods
    assert (con["block_len"] == 12).all()


def test_block_length_is_parameter_default_12():
    from exp.calibration import block_len_ce
    assert block_len_ce(3) == 12 and block_len_ce(6) == 12 and block_len_ce(24) == 24
    assert block_len_ce(3, 6) == 6
    iv = make_iv()
    a = ce_contrasts(iv, "lgbm", "exploratory", B=300, block_len=12)
    b = ce_contrasts(iv, "lgbm", "exploratory", B=300, block_len=3)
    assert (b[b.h == 3]["block_len"] == 3).all() and not np.allclose(a["ci_lo"], b["ci_lo"])


def test_tost_identical_methods_equivalent_and_different_not():
    from exp.calibration import tost_test
    iv = make_iv()
    same = tost_test(ce_arrays(iv, "lgbm", 3, "dracp", "aci"), 3, B=500)
    assert same["T"] == 0 and same["verdict"] == "equivalent"
    assert same["p_tost"] == max(same["p_lower"], same["p_upper"]) < 0.05
    diff = tost_test(ce_arrays(iv, "lgbm", 3, "split", "aci"), 3, B=500)    # T ~ +0.09 > margin
    assert diff["T"] > 0.05 and diff["verdict"] == "not shown"
    assert diff["p_upper"] > 0.5 and diff["p_lower"] < 0.05
    tight = tost_test(ce_arrays(iv, "lgbm", 3, "split", "aci"), 3, margin=0.20, B=500)
    assert tight["verdict"] == "equivalent"              # a wide margin makes the same data equivalent


def test_tost_missing_panel():
    from exp.calibration import tost_test
    r = tost_test(None, 3)
    assert r["verdict"] == "not shown" and np.isnan(r["p_tost"])


def _with_winkler(iv):
    iv = iv.copy()
    iv["winkler"] = np.where(iv["method"] == "aci", 2.0, 1.0) * (1 + iv["unit"].str[1:].astype(int))
    return iv


def test_winkler_contrast_relative_difference():
    from exp.calibration import w_stat, winkler_contrasts, value_arrays
    iv = _with_winkler(make_iv())
    arrs = value_arrays(iv, "lgbm", 3, "aci", "split", "exploratory", "winkler")
    assert abs(w_stat(*arrs[:3]) - 1.0) < 1e-12                  # aci is exactly twice split
    idx = np.arange(arrs[2].shape[1])[None, :]
    assert abs(w_stat(*arrs[:3], idx)[0] - 1.0) < 1e-12
    wk = winkler_contrasts(iv, "lgbm", "exploratory", B=100)
    r = wk[(wk.h == 3) & (wk.contrast == "aci-split")].iloc[0]
    assert abs(r["rel_diff"] - 1.0) < 1e-12
    assert set(wk.contrast) == {"aci-rolling", "dracp-aci", "aci-split"}
    assert abs(wk[(wk.h == 3) & (wk.contrast == "dracp-aci")].iloc[0]["rel_diff"] + 0.5) < 1e-12


def test_sd_coverage_across_units():
    from exp.calibration import sd_coverage
    iv = make_iv()
    sd = sd_coverage(iv, (3,))
    good = sd[sd.method == "aci"].iloc[0]
    bad = sd[sd.method == "split"].iloc[0]
    assert good["sd_coverage"] < 0.01 < 0.05 < bad["sd_coverage"]
    assert good["n_units"] == 8


def test_holdout_and_confirmatory_samples_pooled():
    from exp.calibration import tost_table
    for smp in ("holdout", "confirmatory"):
        iv = make_iv(T=15, n_units=7)
        iv["sample"] = smp
        con = ce_contrasts(iv, "lgbm", smp, B=100)
        assert con[con.h == 3]["n_units"].eq(7).all() and con[con.h == 3]["n_months"].eq(15).all()
        assert con[con.h == 6]["p"].isna().all()                  # no h=6 rows: handled, not an error
        assert tost_table(iv, "lgbm", smp, B=100)["verdict"].notna().all()
        assert ce_contrasts(iv, "lgbm", "exploratory", B=50)["T"].isna().all()   # other sample is empty


def test_holm_known_values():
    assert np.allclose(holm([0.01, 0.04, 0.03, 0.5]), [0.04, 0.09, 0.09, 0.5])


def test_null_bias_helper():
    small, big = null_ce_bias(15, n_sim=100_000), null_ce_bias(190, n_sim=100_000)
    assert small["expected_ce"] > big["expected_ce"] > 0
    # exact E|X/15 - 0.9| for X~Bin(15, 0.9)
    from math import comb
    ex = sum(comb(15, k) * 0.9 ** k * 0.1 ** (15 - k) * abs(k / 15 - 0.9) for k in range(16))
    assert abs(small["expected_ce"] - ex) < 0.003
    assert abs(small["expected_T_null"]) < 4 * small["se_T_null"]


def test_mde_ce_runs_small():
    from exp.power import mde_ce_panel
    iv = make_iv(n_units=6, T=60)
    r = mde_ce_panel(ce_arrays(iv, "lgbm", 3, "aci", "split"), 3, n_outer=20, B_inner=49)
    assert r["n_units"] == 6 and (np.isnan(r["mde_pp"]) or 0 < r["mde_pp"] <= 10)
