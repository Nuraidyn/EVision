import math
import unittest

import numpy as np

from app.services import inflation_calibration as ic
from tests.test_api_endpoints import FastApiBaseTestCase


def _synthetic_cpi(n=400, seed=0, mu=0.4, sigma=0.5):
    rng = np.random.default_rng(seed)
    g = mu + sigma * rng.standard_normal(n)
    idx = 100.0 * np.exp(np.cumsum(g) / 100.0)
    return {i: float(v) for i, v in enumerate(idx, start=24000)}


class TargetConstructionTests(unittest.TestCase):
    def test_target_is_cumulative_log_growth(self):
        cpi = {0: 100.0, 1: 101.0, 2: 103.0, 3: 106.0}
        y = ic.build_targets(cpi, 3)
        self.assertEqual(set(y), {0})
        self.assertAlmostEqual(y[0], 100 * math.log(1.06))
        y1 = ic.build_targets(cpi, 1)
        self.assertEqual(set(y1), {0, 1, 2})
        self.assertAlmostEqual(y1[1], 100 * math.log(103 / 101))

    def test_targets_skip_missing_months(self):
        cpi = {0: 100.0, 1: 101.0, 3: 104.0}
        self.assertEqual(set(ic.build_targets(cpi, 1)), {0})
        self.assertEqual(set(ic.build_targets(cpi, 3)), {0})

    def test_point_forecast_uses_only_past(self):
        cpi = _synthetic_cpi(60)
        full = ic.point_forecasts(cpi, 3)
        cut = max(full) - 10
        trunc = ic.point_forecasts({k: v for k, v in cpi.items() if k <= cut}, 3)
        for t in trunc:
            self.assertAlmostEqual(trunc[t], full[t])


class SnapshotChainTests(unittest.TestCase):
    def test_chain_rescales_at_overlap_and_keeps_growth(self):
        base = {0: 100.0, 1: 101.0, 2: 102.0}
        new = {1: 50.5, 2: 51.0, 3: 51.51, 4: 52.02}  # same growth, index base halved
        out = ic._chain("KZ", base, new)
        self.assertEqual(set(out), {0, 1, 2, 3, 4})
        self.assertAlmostEqual(out[3], 102.0 * 51.51 / 51.0)
        self.assertAlmostEqual(math.log(out[4] / out[3]), math.log(52.02 / 51.51))

    def test_chain_without_overlap_returns_base(self):
        base = {0: 100.0, 1: 101.0}
        self.assertEqual(ic._chain("KZ", base, {5: 1.0, 6: 2.0}), base)

    def test_chain_stops_at_known_methodology_break(self):
        brk = ic.METHOD_BREAKS["NG"]
        base = {brk - 2: 100.0, brk - 1: 101.0}
        new = {brk - 1: 10.1, brk: 9.9, brk + 1: 10.0}
        out = ic._chain("NG", base, new)
        self.assertEqual(set(out), set(base))


class AciTests(unittest.TestCase):
    def test_no_lookahead_future_targets_do_not_change_intervals(self):
        cpi = _synthetic_cpi(300, seed=1)
        h = 3
        targets = ic.build_targets(cpi, h)
        points = ic.point_forecasts(cpi, h)
        origins = sorted(points)
        base = ic.aci_backtest(origins, points, targets, h, 0.1)
        cut = origins[200]
        # corrupt every target not yet revealed at origin `cut` (s > cut - h)
        bad = {s: (y + 50.0 if s > cut - h else y) for s, y in targets.items()}
        pert = ic.aci_backtest(origins, points, bad, h, 0.1)
        self.assertEqual(base.origins, pert.origins)
        for o, lo, hi, plo, phi in zip(base.origins, base.lower, base.upper, pert.lower, pert.upper):
            if o <= cut:

                self.assertAlmostEqual(lo, plo)
                self.assertAlmostEqual(hi, phi)

    def test_coverage_close_to_nominal_on_synthetic_series(self):
        cpi = _synthetic_cpi(600, seed=2)
        for h in (1, 6):
            targets = ic.build_targets(cpi, h)
            points = ic.point_forecasts(cpi, h)
            res = ic.aci_backtest(sorted(points), points, targets, h, 0.1)
            self.assertGreater(len(res.covered), 300)
            self.assertAlmostEqual(float(np.mean(res.covered)), 0.9, delta=0.05)

    def test_conformal_quantile(self):
        s = np.arange(1.0, 10.0)
        self.assertEqual(ic._conformal_quantile(s, 0.2), 8.0)  # ceil(10*0.8)=8
        self.assertEqual(ic._conformal_quantile(s, 0.01), 9.0)  # capped at max score


class InflationEndpointTests(FastApiBaseTestCase):
    def test_countries(self):
        r = self.client.get("/api/v1/inflation/countries")
        self.assertEqual(r.status_code, 200)
        rows = r.json()
        self.assertEqual({x["code"] for x in rows}, set(ic.COUNTRY_NAMES))
        self.assertEqual(set(rows[0]), {"code", "name", "n_months", "first", "last"})

    def test_calibrated_forecast_shape(self):
        r = self.client.get("/api/v1/inflation/calibrated-forecast?country=KZ&horizon=3&level=0.9")
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertEqual(d["country"], "KZ")
        self.assertEqual(d["method"], "aci")
        self.assertEqual(d["horizon"], 3)
        self.assertEqual(len(d["history"]), 60)
        self.assertEqual(set(d["history"][0]), {"date", "value"})
        self.assertEqual(d["history"][-1]["date"], d["as_of"])
        f = d["forecast"]
        self.assertLessEqual(f["lower"], f["point"])
        self.assertLessEqual(f["point"], f["upper"])
        c = d["calibration"]
        self.assertEqual(set(c), {"empirical_coverage", "nominal", "n_eval", "mean_width"})
        self.assertGreater(c["n_eval"], 50)
        self.assertAlmostEqual(c["empirical_coverage"], 0.9, delta=0.1)
        self.assertIsInstance(d["notes"], list)

    def test_all_countries_and_horizons_work(self):
        for code in ic.COUNTRY_NAMES:
            for h in ic.HORIZONS:
                r = self.client.get(f"/api/v1/inflation/calibrated-forecast?country={code}&horizon={h}")
                self.assertEqual(r.status_code, 200, (code, h, r.text))

    def test_validation_errors(self):
        base = "/api/v1/inflation/calibrated-forecast"
        self.assertEqual(self.client.get(f"{base}?country=XX").status_code, 404)
        self.assertEqual(self.client.get(f"{base}?country=KZ&horizon=5").status_code, 400)
        self.assertEqual(self.client.get(f"{base}?country=KZ&level=1.2").status_code, 400)
        self.assertEqual(self.client.get(f"{base}?country=KZ&level=0").status_code, 400)
        self.assertEqual(self.client.get(base).status_code, 422)


if __name__ == "__main__":
    unittest.main()
