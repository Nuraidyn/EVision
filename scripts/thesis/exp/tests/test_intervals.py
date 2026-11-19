import numpy as np
import pytest

from exp.intervals import METHODS, OwnACI, run_method


def _stream(n=300, seed=0):
    rng = np.random.default_rng(seed)
    point = rng.normal(0, 1, n)
    y = point + rng.normal(0, 1, n)
    X = np.column_stack([point, rng.normal(size=(n, 3))])
    return X, y


@pytest.mark.parametrize("h", [1, 3, 6])
@pytest.mark.parametrize("method", ["rolling", "aci", "faci", "pid", "dracp"])
def test_feedback_release_timing(method, h):
    X, y = _stream()
    log = []
    run_method(method, X, y, h, n_cal=60, on_release=lambda k, j: log.append((k, j)))
    assert log, "no feedback released"
    assert all(k >= j + h for k, j in log)               # outcome observable before it is used
    js = [j for _, j in log]
    assert js == sorted(set(js))                          # each origin released exactly once, in order
    assert all(k == j + h for k, j in log)                # released as soon as observable


@pytest.mark.parametrize("method", METHODS)
def test_intervals_do_not_depend_on_unreleased_outcomes(method):
    h, n_cal, k0 = 3, 60, 150
    X, y = _stream(n=220, seed=3)
    a = run_method(method, X, y, h, n_cal)
    y2 = y.copy()
    y2[k0 - h + 1:] += 1000.0                             # outcomes not observable at origin k0
    b = run_method(method, X, y2, h, n_cal)
    e = n_cal + h - 1
    assert np.allclose(a["lo"][e: k0 + 1], b["lo"][e: k0 + 1])
    assert np.allclose(a["hi"][e: k0 + 1], b["hi"][e: k0 + 1])
    assert np.isnan(a["lo"][:e]).all() and np.isfinite(a["lo"][e:]).all()


def test_own_aci_matches_package_h1():
    X, y = _stream(n=250, seed=5)
    n_cal = 60
    pkg = run_method("aci", X, y, 1, n_cal)
    own = OwnACI().fit(np.abs(y[:n_cal] - X[:n_cal, 0]))
    for k in range(n_cal, len(y)):
        r = own.predict_radius()
        lo, hi = X[k, 0] - r, X[k, 0] + r
        assert np.isclose(lo, pkg["lo"][k]) and np.isclose(hi, pkg["hi"][k]), k
        own.update(X[k, 0], y[k], lo, hi)


def test_aci_reaches_nominal_under_shift():
    rng = np.random.default_rng(1)
    n = 600
    sd = np.where(np.arange(n) < 300, 1.0, 3.0)           # variance jumps mid-sample
    y = rng.normal(0, sd)
    X = np.column_stack([np.zeros(n), np.zeros(n)])
    r_split = run_method("split", X, y, 1, 100)
    r_aci = run_method("aci", X, y, 1, 100)

    def cov(r):
        return np.mean((y[100:] >= r["lo"][100:]) & (y[100:] <= r["hi"][100:]))

    assert cov(r_split) < 0.8
    assert abs(cov(r_aci) - 0.9) < 0.07
