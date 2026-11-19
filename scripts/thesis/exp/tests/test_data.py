import numpy as np
import pandas as pd

from conftest import synth_cpi, synth_fx
from exp.data import build_frame, country_units, fx_z_scores, sample_label, stretches


def test_target_definition(cpi):
    fr = build_frame(cpi, synth_fx(cpi), None)
    for h in (1, 3, 6, 12):
        t = 10
        expect = 100 * np.log(cpi.iloc[t + h] / cpi.iloc[t])
        assert np.isclose(fr[f"y{h}"].iloc[t], expect)
        assert fr[f"y{h}"].iloc[-h:].isna().all()          # no target beyond the sample
        assert fr[f"y{h}"].iloc[:-h].notna().all()


def test_features_are_causal(cpi):
    fx = synth_fx(cpi)
    a = build_frame(cpi, fx, None)
    t = 120
    cpi2, fx2 = cpi.copy(), fx.copy()
    cpi2.iloc[t + 1:] *= 3.0                                  # change the future
    fx2.iloc[t + 1:] *= 5.0
    b = build_frame(cpi2, fx2, None)
    feat = ["m0", "m1", "m2", "m5", "m11", "roll3", "roll12", "fx0", "fx1", "msin", "mcos", "stress"]
    pd.testing.assert_frame_equal(a[feat].iloc[: t + 1], b[feat].iloc[: t + 1])
    assert not np.isclose(a["y3"].iloc[t], b["y3"].iloc[t])  # targets do look forward


def test_gaps_split_into_stretches():
    c = synth_cpi(n=250, drop=range(100, 103))
    assert len(stretches(c.index)) == 2
    raw = {"cpi": {"XX": c}, "fx": {}, "brent": None}
    units = country_units(raw, "XX", min_len=60)
    assert set(units) == {"XX#1", "XX#2"}
    u1 = units["XX#1"]
    assert len(u1) == 100 and u1["y12"].iloc[-12:].isna().all()   # no target across the gap
    assert u1.index[-1] == pd.Period("2005-01", "M") + 99


def test_stress_matches_definition():
    cpi = synth_cpi(n=150)
    fx = synth_fx(cpi)
    z = fx_z_scores(fx)
    assert z.index[0] == fx.index[61]                          # first 60 diffs only train m, s
    d = np.log(fx.values[1:] / fx.values[:-1])
    w = d[:60]
    m = np.median(w)
    s = max(1.4826 * np.median(np.abs(w - m)), 0.005)
    assert np.isclose(z.iloc[0], (d[60] - m) / s)
    fr = build_frame(cpi, fx, None)
    t = 100
    expect = z.abs().reindex(fr.index[t - 3: t + 1]).max()
    assert np.isclose(fr["stress"].iloc[t], expect)


def test_sample_label():
    assert sample_label(pd.Period("2025-06", "M")) == "exploratory"
    assert sample_label(pd.Period("2025-07", "M")) == "confirmatory"


def test_chain_rescales_index_base_and_keeps_growth():
    from exp.data import chain_cpi
    idx = pd.period_range("2024-01", periods=6, freq="M")
    old = pd.Series([100.0, 101.0, 102.0], index=idx[:3])
    new = pd.Series([50.5, 51.0, 51.51, 52.02], index=idx[1:5])    # same growth, base halved
    out = chain_cpi("KZ", old, new)
    assert list(out.index) == list(idx[:5])
    assert np.isclose(out.iloc[3], 102.0 * 51.51 / 51.0)
    assert np.isclose(np.log(out.iloc[4] / out.iloc[3]), np.log(52.02 / 51.51))
    assert np.isclose(out.iloc[1], 101.0)                             # earlier snapshot wins


def test_chain_stops_at_methodology_break():
    from exp.data import METHOD_BREAKS, chain_cpi
    brk = METHOD_BREAKS["NG"]
    old = pd.Series([100.0, 101.0], index=pd.period_range(brk - 2, periods=2, freq="M"))
    new = pd.Series([10.1, 9.9, 10.0], index=pd.period_range(brk - 1, periods=3, freq="M"))
    out = chain_cpi("NG", old, new)
    assert out.index.max() == brk - 1


def test_real_data_has_no_level_jump_at_the_snapshot_junction():
    """Regression: merging two IMF snapshots with different index bases must not create a jump."""
    import pytest
    from exp.data import DATA_DIR, load_raw
    if not (DATA_DIR / "confirmatory.json").exists():
        pytest.skip("no confirmatory snapshot")
    raw = load_raw()
    for c, s in raw["cpi"].items():
        s = s[s.index >= pd.Period("2024-01", "M")]
        step = np.abs(np.diff(np.log(s.values)))
        assert step.max() < 0.15, f"{c}: monthly log jump {step.max():.2f}"
