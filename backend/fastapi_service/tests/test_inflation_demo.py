"""Demo endpoints of the thesis research pages: benchmark, compare, explain (fake LLM only)."""
import json
import unittest
from unittest.mock import patch

from app.api.v1 import inflation as api
from app.core import config
from app.main import app
from app.services import inflation_calibration as ic
from app.services import inflation_compare as cmp
from app.services import inflation_explainer as ie
from app.services.inflation_faithfulness import check_numeric_faithfulness
from tests.test_api_endpoints import FastApiBaseTestCase
from tests.test_inflation_calibration import _synthetic_cpi


class FakeClient:
    def __init__(self, text=None, fail=False):
        self.text, self.fail, self.calls = text, fail, []

    def complete(self, system_prompt, user_prompt):
        self.calls.append((system_prompt, user_prompt))
        if self.fail:
            raise RuntimeError("boom https://secret-proxy.example/v1 key=sk-SECRET")
        return self.text or "ok"


class CompareServiceTests(unittest.TestCase):
    def test_aci_equals_existing_endpoint_numbers_at_min_cal(self):
        for code, h in (("KZ", 3), ("BR", 12), ("NG", 1)):
            r = cmp.compare_methods(code, h, 0.9, warmup=ic.MIN_CAL)
            f = ic.calibrated_forecast(code, h, 0.9)
            a = r["methods"]["aci"]
            self.assertEqual(a["n_eval"], f["calibration"]["n_eval"])
            self.assertAlmostEqual(a["coverage"], f["calibration"]["empirical_coverage"], places=12)
            self.assertAlmostEqual(a["mean_width"], f["calibration"]["mean_width"], places=9)

    def test_invariants_all_countries_and_horizons(self):
        for code in ic.COUNTRY_NAMES:
            for h in ic.HORIZONS:
                r = cmp.compare_methods(code, h)
                self.assertEqual(set(r["methods"]), {"split", "rolling", "aci"})
                n = {m["n_eval"] for m in r["methods"].values()}
                self.assertEqual(len(n), 1, (code, h, n))  # same origins for all methods
                for m in r["methods"].values():
                    self.assertTrue(0.0 <= m["coverage"] <= 1.0)
                    self.assertAlmostEqual(m["calibration_error"], abs(m["coverage"] - 0.9))
                    self.assertGreater(m["mean_width"], 0)
                    self.assertLessEqual(len(m["series"]), 60)
                    last = m["series"][-1]
                    self.assertLessEqual(last["lower"], last["upper"])
                    self.assertEqual(last["covered"], last["lower"] <= last["actual"] <= last["upper"])
                    self.assertTrue(0.0 <= last["running_coverage"] <= 1.0)

    def test_series_dates_and_downsampling(self):
        r = cmp.compare_methods("KZ", 3, n_last=120)
        s = r["methods"]["aci"]["series"]
        self.assertLessEqual(len(s), 60)
        self.assertGreater(len(s), 20)
        self.assertEqual([x["date"] for x in s], sorted(x["date"] for x in s))
        self.assertEqual(s[-1]["date"], ic.int_to_month(ic._month_to_int(s[-1]["origin"]) + 3))

    def test_no_lookahead_in_static_methods(self):
        cpi = _synthetic_cpi(300, seed=3)
        h = 3
        targets, points = ic.build_targets(cpi, h), ic.point_forecasts(cpi, h)
        origins = sorted(points)
        for mode in ("split", "rolling"):
            base = cmp.static_backtest(origins, points, targets, h, 0.1, mode)
            cut = origins[-1] - 40
            tg = {k: (v + 100 if k > cut - h else v) for k, v in targets.items()}  # corrupt late targets
            alt = cmp.static_backtest(origins, points, tg, h, 0.1, mode)
            keep = [i for i, t in enumerate(base[0]) if t <= cut]
            self.assertTrue(keep)
            for i in keep:
                self.assertAlmostEqual(base[1][i], alt[1][i])
                self.assertAlmostEqual(base[2][i], alt[2][i])

    def test_split_is_frozen_rolling_moves(self):
        cpi = _synthetic_cpi(300, seed=5)
        targets, points = ic.build_targets(cpi, 1), ic.point_forecasts(cpi, 1)
        o, lo, hi, _ = cmp.static_backtest(sorted(points), points, targets, 1, 0.1, "split")
        self.assertEqual(len({round(u - l, 9) for l, u in zip(lo, hi)}), 1)
        _, lo, hi, _ = cmp.static_backtest(sorted(points), points, targets, 1, 0.1, "rolling")
        self.assertGreater(len({round(u - l, 9) for l, u in zip(lo, hi)}), 5)

    def test_bad_inputs(self):
        for kw in (dict(country="XX", horizon=3), dict(country="KZ", horizon=5),
                   dict(country="KZ", horizon=3, level=1.2), dict(country="KZ", horizon=3, warmup=5)):
            with self.assertRaises(ic.InflationError):
                cmp.compare_methods(**kw)


class FaithfulnessTests(unittest.TestCase):
    PAYLOAD = {"forecast": {"point": 1.5, "lower": -0.49, "upper": 3.5}, "level": 0.9,
               "empirical_coverage": 0.913, "n_eval": 196, "mean_width": 4.0}

    def test_faithful_answer(self):
        r = check_numeric_faithfulness(
            "The 90% interval is from -0.49% to 3.50%; backtest coverage was 91.3% over 196 points.", self.PAYLOAD)
        self.assertTrue(r["checked"] and r["faithful"], r)
        self.assertTrue(r["states_interval"] and r["states_level"] and r["states_coverage"])

    def test_wrong_number_flagged_and_guarantee_wording(self):
        r = check_numeric_faithfulness("The interval is 0.5% to 9.9%, guaranteed.", self.PAYLOAD)
        self.assertFalse(r["faithful"])
        self.assertIn(9.9, r["unmatched_values"])
        self.assertTrue(r["guarantee_wording"])
        r2 = check_numeric_faithfulness("This is not guaranteed.", self.PAYLOAD)
        self.assertFalse(r2["guarantee_wording"])

    def test_range_separator_does_not_flip_sign(self):
        r = check_numeric_faithfulness("Interval -0.49%–3.50%", self.PAYLOAD)
        self.assertTrue(r["faithful"], r)

    def test_no_payload(self):
        self.assertFalse(check_numeric_faithfulness("x", None)["checked"])


class BenchmarkAndExplainApiTests(FastApiBaseTestCase):
    def tearDown(self):
        app.dependency_overrides.pop(api.get_llm_client, None)
        api._EXPLAIN_CALLS.clear()
        super().tearDown()

    def _fake(self, client):
        app.dependency_overrides[api.get_llm_client] = lambda: client

    # ---- benchmark
    def test_benchmark_served_with_honesty_tags(self):
        r = self.client.get("/api/v1/inflation/benchmark")
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertIn("generated", d)
        self.assertTrue(d["sources"])
        self.assertEqual(d["mde_limit_pp"], 7.0)
        for e in d["contrasts"]:
            self.assertIn(e["panel"], d["panels"])
            self.assertIn("status", e)
            if e["family"] == "primary" and (e["mde_pp"] is None or e["mde_pp"] > 7.0):
                self.assertEqual(e["verdict"], "inconclusive")
        self.assertTrue(all(e["status"] in ("pre-specified", "exploratory", "post hoc") for e in d["ce"]))
        self.assertEqual(d["llm_eval"]["v2"]["status"], "post hoc")

    def test_benchmark_missing_file_is_503(self):
        with patch("app.services.thesis_benchmark.INFLATION_BENCHMARK_PATH", "/nonexistent/x.json"):
            r = self.client.get("/api/v1/inflation/benchmark")
        self.assertEqual(r.status_code, 503)

    # ---- compare
    def test_compare_endpoint(self):
        r = self.client.get("/api/v1/inflation/compare?country=kz&horizon=3")
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertEqual((d["country"], d["warmup"]), ("KZ", 48))
        self.assertEqual(set(d["methods"]), {"split", "rolling", "aci"})
        f = self.client.get("/api/v1/inflation/calibrated-forecast?country=KZ&horizon=3").json()
        r30 = self.client.get("/api/v1/inflation/compare?country=KZ&horizon=3&warmup=30").json()
        self.assertEqual(r30["methods"]["aci"]["coverage"], f["calibration"]["empirical_coverage"])

    def test_compare_errors(self):
        b = "/api/v1/inflation/compare"
        self.assertEqual(self.client.get(f"{b}?country=ZZ&horizon=3").status_code, 404)
        self.assertEqual(self.client.get(f"{b}?country=KZ&horizon=4").status_code, 400)
        self.assertEqual(self.client.get(f"{b}?country=KZ&horizon=3&warmup=1").status_code, 400)

    # ---- explain
    def _post(self, **over):
        body = dict(country="KZ", horizon=3, question_type="T1", language="en", grounded=True)
        body.update(over)
        return self.client.post("/api/v1/inflation/explain", json=body)

    def test_explain_grounded_returns_payload_and_check(self):
        api_payload = ie.tool_payload("KZ", 3)
        f = api_payload["forecast"]
        fake = FakeClient(f"The 90% interval is {f['lower']:.2f}% to {f['upper']:.2f}%.")
        self._fake(fake)
        r = self._post()
        self.assertEqual(r.status_code, 200, r.text)
        d = r.json()
        self.assertEqual(d["model_saw"], api_payload)
        self.assertTrue(d["check"]["checked"] and d["check"]["faithful"], d["check"])
        self.assertIn(ie.TOOL_START, fake.calls[0][0])
        self.assertIn("question", d)
        self.assertNotIn("sk-", json.dumps(d))

    def test_explain_ungrounded_has_no_tool_data(self):
        fake = FakeClient("Inflation will be 99.9% for sure.")
        self._fake(fake)
        d = self._post(grounded=False, language="ru").json()
        self.assertIsNone(d["model_saw"])
        self.assertNotIn(ie.TOOL_START, fake.calls[0][0])
        self.assertIsNotNone(d["reference"])
        self.assertFalse(d["check"]["faithful"])  # 99.9 is not a real quantity
        self.assertTrue(d["check"]["guarantee_wording"])

    def test_explain_no_key_is_503_without_secret(self):
        with patch.object(config, "OPENAI_API_KEY", ""):
            r = self._post()
        self.assertEqual(r.status_code, 503)
        self.assertIn("not configured", r.json()["detail"])

    def test_explain_llm_failure_is_503_and_does_not_leak(self):
        self._fake(FakeClient(fail=True))
        r = self._post()
        self.assertEqual(r.status_code, 503)
        self.assertNotIn("secret", r.text.lower())
        self.assertNotIn("sk-", r.text)

    def test_explain_validation(self):
        self._fake(FakeClient("ok"))
        self.assertEqual(self._post(country="ZZ").status_code, 404)
        self.assertEqual(self._post(horizon=5).status_code, 400)
        self.assertEqual(self._post(question_type="T9").status_code, 422)
        self.assertEqual(self._post(language="de").status_code, 422)

    def test_explain_in_process_cap(self):
        self._fake(FakeClient("ok"))
        with patch.object(config, "INFLATION_EXPLAIN_MAX_PER_MINUTE", 2):
            codes = [self._post().status_code for _ in range(3)]
        self.assertEqual(codes, [200, 200, 429])

    def test_openai_client_attempt_limit(self):
        self.assertEqual(ie.OpenAIClient(max_tokens=100, max_attempts=1).max_attempts, 1)


if __name__ == "__main__":
    unittest.main()
