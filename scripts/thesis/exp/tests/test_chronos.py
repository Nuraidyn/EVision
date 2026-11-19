"""Chronos forecaster (mock pipeline), possibly_seen flag, holdout2 loading/labelling."""
import json

import numpy as np
import pandas as pd
import pytest

from conftest import synth_cpi, synth_fx
from exp.data import build_frame, country_units, load_holdout
from exp.evaluate import Config, run_unit
from exp.forecasters import CHRONOS_MODEL_ID, Chronos, make_forecasters


class MockPipe:
    """Median forecast of step k = mean(last 3 context values) + 0.1*k ; records every context."""

    def __init__(self):
        self.seen = []

    def predict_quantiles(self, context, prediction_length, quantile_levels):
        import torch
        assert list(quantile_levels) == [0.5]
        out = []
        for c in context:
            c = np.asarray(c)
            self.seen.append(c.copy())
            base = np.nanmean(c[-3:])
            out.append(base + 0.1 * np.arange(1, prediction_length + 1))
        q = torch.tensor(np.stack(out))[:, :, None]
        return q, q[:, :, 0]


def _frame(n=150, seed=0):
    cpi = synth_cpi(n, seed=seed)
    return build_frame(cpi, synth_fx(cpi), None, (1, 3, 6))


def test_chronos_registered():
    assert isinstance(make_forecasters(["chronos"], chronos=dict(pipeline=MockPipe()))["chronos"], Chronos)
    assert CHRONOS_MODEL_ID.startswith("amazon/chronos")


def test_sum_of_h_medians_and_no_interval():
    fr = _frame()
    fc = Chronos(pipeline=MockPipe())
    pos = 100
    out = fc.forecast(fr, pos, (1, 3, 6))
    base = fr["m0"].iloc[pos - 2: pos + 1].mean()
    for h in (1, 3, 6):
        exp = sum(base + 0.1 * k for k in range(1, h + 1))
        assert out[h][0] == pytest.approx(exp, rel=1e-5)
        assert out[h][1] is None and out[h][2] is None


def test_no_lookahead_and_batch_equals_single():
    fr = _frame()
    pos = 90
    pipe = MockPipe()
    a = Chronos(pipeline=pipe).forecast(fr, pos, (3, 6))
    assert len(pipe.seen[0]) == pos          # monthly values of rows 1..pos only
    np.testing.assert_allclose(pipe.seen[0], fr["m0"].iloc[1: pos + 1].values, rtol=1e-6)
    bad = fr.copy()
    bad.iloc[pos + 1:] = 1e6                 # corrupt the future
    b = Chronos(pipeline=MockPipe()).forecast(bad, pos, (3, 6))
    assert a == b
    fc = Chronos(pipeline=MockPipe(), batch_size=7)
    fc.prepare(fr, list(range(80, 100)), (3, 6))
    assert fc.n_forecasts == 20
    assert fc.forecast(fr, pos, (3, 6)) == a
    assert fc.n_forecasts == 20              # served from cache


def test_context_truncated():
    fr = _frame(150)
    pipe = MockPipe()
    Chronos(pipeline=pipe, max_context=50).forecast(fr, 120, (3,))
    assert len(pipe.seen[0]) == 50


def test_possibly_seen_flag_and_model_id(monkeypatch):
    import exp.forecasters as F
    pipe = MockPipe()
    monkeypatch.setitem(F.make_forecasters.__globals__, "Chronos",
                        lambda **kw: Chronos(pipeline=pipe))
    cpi = synth_cpi(200, start="2009-01", seed=3)      # targets 2014 .. 2025-08
    fr = build_frame(cpi, synth_fx(cpi), None, (3,))
    fr.attrs["country"] = "XX"
    cfg = Config(models=("chronos", "naive_b"), conformal_models=("chronos",), horizons=(3,), n_cal=24)
    p, i = run_unit("XX", fr, cfg)
    c, n = p[p.model == "chronos"], p[p.model == "naive_b"]
    assert (c.possibly_seen == (pd.PeriodIndex(c.target, freq="M") < pd.Period("2025-01", "M"))).all()
    assert c.possibly_seen.any() and not c.possibly_seen.all()
    assert not n.possibly_seen.any()
    assert (c.model_id == CHRONOS_MODEL_ID).all()
    assert "possibly_seen" in i.columns and i[i.model == "chronos"].method.nunique() > 1


def _write_holdout2(d):
    cpi = synth_cpi(120, start="2015-01", seed=5)
    fx = synth_fx(cpi)
    snap = {"cpi": {"KZ": {str(k): float(v) for k, v in cpi.items()}},
            "fx": {}, "brent": {str(k): 50.0 + i for i, k in enumerate(cpi.index)}}
    (d / "snapshot.json").write_text(json.dumps(snap))
    h2 = {"cpi": {"ZZ": {str(k): float(v) for k, v in cpi.items()}},
          "fx": {"ZZ": {str(k): float(v) for k, v in fx.items()}}}
    (d / "holdout2.json").write_text(json.dumps(h2))


def test_holdout2_loading_and_labelling(tmp_path, monkeypatch):
    _write_holdout2(tmp_path)
    raw = load_holdout(path=tmp_path / "holdout2.json", data_dir=tmp_path)
    assert list(raw["cpi"]) == ["ZZ"] and raw["brent"] is not None
    from exp import run as R
    out = tmp_path / "res"
    monkeypatch.setattr(R, "RESULTS", tmp_path / "res")
    R.main(["full", "--holdout2", "--data-dir", str(tmp_path), "--models", "naive_b,lgbm",
            "--conformal-models", "naive_b", "--horizons", "3,6", "--boot", "20", "--n-cal", "24",
            "--out", "h2"])
    iv = pd.read_csv(out / "h2" / "intervals_all.csv")
    pts = pd.read_csv(out / "h2" / "points_all.csv")
    assert set(iv["sample"]) == {"holdout2"} and set(pts["sample"]) == {"holdout2"}
    assert set(pts.country) == {"ZZ"}
    # the ce command accepts the new sample label
    res = R.run_ce(out / "h2", out / "ce", model="naive_b", B=20, n_outer=2, sample="holdout2")
    assert "contrasts" in res


def test_ce_argparser_accepts_holdout2():
    from exp import run as R
    with pytest.raises(FileNotFoundError):      # parsed fine; fails only on the missing input dir
        R.main(["ce", "--in", "nonexistent_dir_xyz", "--out", "x", "--sample", "holdout2"])


def test_integration_real_model():
    try:
        fc = Chronos()
        fc._pipeline()
    except Exception as e:                     # model not downloadable / not installed
        pytest.skip(f"chronos model unavailable: {e}")
    fr = _frame(120)
    out = fc.forecast(fr, 100, (1, 3, 6))
    assert all(np.isfinite(out[h][0]) for h in out)
    again = Chronos().forecast(fr, 100, (1, 3, 6))
    assert out == again                        # deterministic
