import numpy as np
import pytest

from conftest import synth_cpi, synth_fx
from exp.data import build_frame
from exp.forecasters import ARIMA, ETS, LGBM, NaiveA, NaiveB

HS = (1, 3, 6, 12)


def _frames(pos):
    cpi = synth_cpi(n=160)
    fx = synth_fx(cpi)
    a = build_frame(cpi, fx, None)
    cpi2, fx2 = cpi.copy(), fx.copy()
    rng = np.random.default_rng(9)
    cpi2.iloc[pos + 1:] = 100 * np.exp(rng.normal(0, 1, len(cpi2) - pos - 1).cumsum())  # garbage future
    fx2.iloc[pos + 1:] *= 7
    return a, build_frame(cpi2, fx2, None)


def _cmp(r1, r2):
    for h in HS:
        for x, y in zip(r1[h], r2[h]):
            if x is None or y is None:
                assert x is None and y is None
            else:
                assert np.isclose(x, y, rtol=1e-9, atol=1e-9), (h, x, y)


@pytest.mark.parametrize("make", [NaiveA, NaiveB, lambda: LGBM(refit_every=1), ETS, ARIMA])
def test_no_lookahead(make):
    pos = 100
    a, b = _frames(pos)
    ra = make().forecast(a, pos, HS)
    rb = make().forecast(b, pos, HS)
    assert all(np.isfinite(ra[h][0]) for h in HS)
    _cmp(ra, rb)


def test_naive_definitions(cpi):
    fr = build_frame(cpi, None, None)
    pos = 80
    a = NaiveA().forecast(fr, pos, HS)
    b = NaiveB().forecast(fr, pos, HS)
    m = 100 * np.log(cpi.iloc[pos] / cpi.iloc[pos - 1])
    for h in HS:
        assert np.isclose(a[h][0], h * m)
        assert np.isclose(b[h][0], 100 * np.log(cpi.iloc[pos] / cpi.iloc[pos - h]))


def test_native_intervals_ordered(cpi):
    fr = build_frame(cpi, None, None)
    for fc in (ETS(), ARIMA()):
        r = fc.forecast(fr, 120, HS)
        for h in HS:
            assert r[h][1] < r[h][2]
        assert (r[12][2] - r[12][1]) > (r[1][2] - r[1][1])      # wider at longer horizon
