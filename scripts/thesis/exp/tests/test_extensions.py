"""Tests for the fourth-amendment extensions: instant-feedback diagnostic, n_cal, hold-out panel,
windowed MDE and the ce command.  Synthetic data only."""
import json

import numpy as np
import pandas as pd
import pytest

from conftest import synth_cpi, synth_fx
from exp.data import build_frame, country_units, load_holdout
from exp.evaluate import Config, run_unit
from exp.intervals import run_method


def _stream(n=300, seed=0):
    rng = np.random.default_rng(seed)
    point = rng.normal(0, 1, n)
    y = point + rng.normal(0, 1, n)
    return np.column_stack([point, rng.normal(size=(n, 3))]), y


@pytest.mark.parametrize("method", ["rolling", "aci", "dracp"])
def test_instant_feedback_releases_at_next_origin(method):
    X, y = _stream()
    log = []
    run_method(method, X, y, 12, n_cal=60, on_release=lambda k, j: log.append((k, j)), instant_feedback=True)
    assert log and all(k == j + 1 for k, j in log)
    delayed = []
    run_method(method, X, y, 12, n_cal=60, on_release=lambda k, j: delayed.append((k, j)))
    assert all(k == j + 12 for k, j in delayed)
    assert len(log) > len(delayed)


def test_instant_feedback_changes_aci_not_split_and_is_default_off():
    X, y = _stream()
    a = run_method("aci", X, y, 12, 60)
    b = run_method("aci", X, y, 12, 60, instant_feedback=True)
    assert not np.allclose(a["lo"][71:], b["lo"][71:])
    s1, s2 = run_method("split", X, y, 12, 60), run_method("split", X, y, 12, 60, instant_feedback=True)
    assert np.allclose(s1["lo"][71:], s2["lo"][71:])


def _cfg(**kw):
    return Config(models=("naive_b", "lgbm"), conformal_models=("naive_b",), horizons=(3,),
                  methods=("split", "aci"), min_train=60, n_cal=kw.pop("n_cal", 30), **kw)


def test_run_unit_ncal_marker_and_sample_override(cpi):
    fr = build_frame(cpi, synth_fx(cpi), None, horizons=(3,))
    p30, i30 = run_unit("U", fr, _cfg(n_cal=30))
    p50, i50 = run_unit("U", fr, _cfg(n_cal=50))
    assert i30.origin.min() < i50.origin.min()                 # longer warm-up -> later first interval
    assert (i30["feedback"] == "delayed").all() and (p30["feedback"] == "delayed").all()
    pi, ii = run_unit("U", fr, _cfg(n_cal=30, instant_feedback=True))
    assert (ii["feedback"] == "instant_DIAGNOSTIC").all()
    ph, ih = run_unit("U", fr, _cfg(n_cal=30, sample="holdout"))
    assert set(ih["sample"]) == {"holdout"} and set(ph["sample"]) == {"holdout"}
    assert set(i30["sample"]) == {"exploratory"}               # synthetic data are 2005-2021


def _holdout_file(tmp_path, countries=("AA", "BB")):
    d = {"cpi": {}, "fx": {}, "brent": None}
    for j, c in enumerate(countries):
        cpi = synth_cpi(150, start="1999-06", seed=10 + j)
        d["cpi"][c] = {str(k): float(v) for k, v in cpi.items()}
        d["fx"][c] = {str(k): float(v) for k, v in synth_fx(cpi, seed=20 + j).items()}
    p = tmp_path / "holdout.json"
    p.write_text(json.dumps(d))
    snap = tmp_path / "snap"
    snap.mkdir()
    b = synth_cpi(200, start="1995-01", seed=5)
    (snap / "snapshot.json").write_text(json.dumps(
        {"cpi": {}, "fx": {}, "brent": {str(k): float(v) for k, v in b.items()}}))
    return p, snap


def test_load_holdout_structure_and_brent_from_main(tmp_path):
    p, snap = _holdout_file(tmp_path)
    raw = load_holdout(p, snap)
    assert set(raw["cpi"]) == {"AA", "BB"} and set(raw["fx"]) == {"AA", "BB"}
    assert raw["brent"] is not None and len(raw["brent"]) == 200
    units = country_units(raw, "AA", horizons=(3,), start="2000-01")
    fr = units["AA"]
    assert fr.index[0] == pd.Period("2000-01", "M")           # start >= 2000-01
    assert fr["br0"].notna().sum() > 0                         # Brent attached


def test_holdout_end_to_end_and_ce(tmp_path):
    from exp import run as R
    p, snap = _holdout_file(tmp_path)
    raw = load_holdout(p, snap)
    cfg = Config(models=("naive_b", "lgbm"), conformal_models=("naive_b",), horizons=(3, 6),
                 n_cal=30, boot_B=50, sample="holdout")
    units = {}
    for c in raw["cpi"]:
        units.update(country_units(raw, c, horizons=cfg.horizons, start="2000-01"))
    res = R.execute(units, cfg, tmp_path / "out", primary_model="naive_b")
    iv = res["intervals"]
    assert set(iv["sample"]) == {"holdout"} and (tmp_path / "out" / "calibration_contrasts.csv").exists()
    cc = pd.read_csv(tmp_path / "out" / "calibration_contrasts.csv")
    assert set(cc["sample"]) == {"holdout"} and len(cc) == 6
    assert (tmp_path / "out" / "calibration_tost.csv").exists()
    assert (tmp_path / "out" / "winkler_contrasts.csv").exists()
    assert (tmp_path / "out" / "sd_coverage.csv").exists()
    # the ce command on the holdout rows, with the windowed MDE
    out = R.run_ce(tmp_path / "out", tmp_path / "ce", "naive_b", B=100, n_outer=10, sample="holdout",
                   window_mde=True, window=15, n_windows=3)
    assert (tmp_path / "ce" / "power_mde_ce_windows15.csv").exists()
    assert set(out["contrasts"]["sample"]) == {"holdout"}
    with pytest.raises(SystemExit):
        R.run_ce(tmp_path / "out", tmp_path / "ce2", "naive_b", B=50, sample="confirmatory")


def test_instant_diagnostic_marker_file_and_outdir_guard(tmp_path):
    from exp import run as R
    cpi = synth_cpi(150)
    units = {"U": build_frame(cpi, synth_fx(cpi), None, horizons=(3, 6))}
    cfg = Config(models=("naive_b",), conformal_models=("naive_b",), horizons=(3, 6), n_cal=30,
                 boot_B=50, instant_feedback=True)
    R.execute(units, cfg, tmp_path / "diag")
    assert (tmp_path / "diag" / "DIAGNOSTIC_instant_feedback.txt").exists()
    assert (pd.read_csv(tmp_path / "diag" / "intervals_all.csv")["feedback"] == "instant_DIAGNOSTIC").all()
    with pytest.raises(SystemExit):
        R.main(["full", "--instant-feedback", "--out", "full"])


def test_window_mde_runs_and_reports():
    from exp.power import mde_ce_windows
    from test_calibration import make_iv
    iv = make_iv(n_units=6, T=80)
    r = mde_ce_windows(iv, "lgbm", "exploratory", window=15, n_windows=4, n_outer=15, B_inner=39)
    assert set(r.contrast) == {"aci-rolling", "dracp-aci"}
    h3 = r[(r.h == 3) & (r.contrast == "aci-rolling")].iloc[0]
    assert h3["n_windows"] == 4 and h3["window"] == 15
    assert 0 <= h3["share_undefined"] <= 1
    short = mde_ce_windows(make_iv(n_units=3, T=10), "lgbm", window=15, n_windows=2)
    assert (short["n_windows"] == 0).all()
