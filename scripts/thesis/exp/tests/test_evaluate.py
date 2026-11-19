import numpy as np
import pandas as pd

from conftest import synth_cpi, synth_fx
from exp.data import build_frame
from exp.evaluate import (Config, add_interval_columns, block_indices, boot_ratio, holm,
                          interval_summary, month_sums, point_metrics, run_unit, winkler)


def test_block_bootstrap_block_length():
    rng = np.random.default_rng(0)
    T, b = 100, 7
    idx = block_indices(T, b, 50, rng)
    assert idx.shape == (50, T)
    for r in np.diff(idx, axis=1):                       # consecutive inside a block
        breaks = np.where(r != 1)[0]
        assert all((x + 1) % b == 0 for x in breaks)
    assert idx.min() >= 0 and idx.max() < T


def test_bootstrap_resamples_months_jointly():
    origin = [str(pd.Period("2020-01", "M") + i // 2) for i in range(12)]
    df = pd.DataFrame({"unit": ["A", "B"] * 6, "origin": origin, "x": [1.0, 0.0] * 6})
    s, c, grid = month_sums(df, "x")
    assert len(grid) == 6 and (c == 2).all() and (s == 1).all()   # both units share each month
    bs = boot_ratio(s, c, 3, 100, np.random.default_rng(1))
    assert np.allclose(bs, 0.5)                                    # cells stay together


def test_winkler_and_coverage():
    assert np.isclose(winkler([0.5], [0], [1], 0.1)[0], 1.0)
    assert np.isclose(winkler([-1.0], [0], [1], 0.1)[0], 1 + 20 * 1.0)
    assert np.isclose(winkler([3.0], [0], [1], 0.1)[0], 1 + 20 * 2.0)
    iv = add_interval_columns(pd.DataFrame(dict(y=[0, 5], lo=[-1, -1], hi=[1, 1])))
    assert iv.covered.tolist() == [1.0, 0.0] and iv.width.tolist() == [2, 2]


def test_holm():
    assert np.allclose(holm([0.01, 0.04, 0.03, 0.5]), [0.04, 0.09, 0.09, 0.5])


def test_point_metrics_relative():
    rows = []
    for mod, pt in (("naive_a", 1.0), ("naive_b", 0.5), ("m", 0.0)):
        for i in range(4):
            rows.append(dict(unit="U", country="U", model=mod, h=1, origin=f"2020-0{i+1}",
                             target=f"2020-0{i+2}", y=0.0, point=pt, sample="exploratory"))
    pm = point_metrics(pd.DataFrame(rows))
    g = pm[(pm.model == "m") & (pm.unit == "ALL")].iloc[0]
    assert g.mae == 0 and g.rel_mae_naive_a == 0
    a = pm[(pm.model == "naive_a") & (pm.unit == "ALL")].iloc[0]
    assert np.isclose(a.rel_mae_naive_b, 2.0)


def test_end_to_end_tiny():
    pts, ivs = [], []
    cfg = Config(models=("naive_a", "naive_b", "lgbm"), conformal_models=("lgbm",),
                 methods=("split", "aci", "dracp"), horizons=(1, 3), min_train=60, n_cal=40,
                 n_eval_last=25, boot_B=50, lgbm={"refit_every": 6})
    for i in range(2):
        cpi = synth_cpi(n=140, seed=i)
        fr = build_frame(cpi, synth_fx(cpi, seed=i), None, horizons=(1, 3))
        fr.attrs["country"] = f"S{i}"
        p, v = run_unit(f"S{i}", fr, cfg)
        pts.append(p)
        ivs.append(v)
    iv = pd.concat(ivs)
    assert set(iv.method) == {"split", "aci", "dracp"} and set(iv.h) == {1, 3}
    assert iv.groupby(["unit", "model", "method", "h"]).size().min() >= 20
    assert iv.lo.lt(iv.hi).all() and iv.covered.between(0, 1).all()
    assert set(iv["sample"]) == {"exploratory"}
    all_ = interval_summary(iv, B=50)
    all_ = all_[all_.unit == "ALL"]
    assert all_.coverage.between(0.5, 1).all()
    assert {"cov_lo", "cov_hi"} <= set(all_.columns)
    assert len(point_metrics(pd.concat(pts))) > 0
