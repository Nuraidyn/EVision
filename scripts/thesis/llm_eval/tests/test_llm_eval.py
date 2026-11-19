import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common  # noqa: E402,F401
from fake_client import FakeLLMClient  # noqa: E402
from generate_prompts import generate_prompts  # noqa: E402
from metrics import evaluate_answer, extract_numbers, overstates_guarantee, wilson  # noqa: E402
from sampler import sample_for_review  # noqa: E402
from app.services.inflation_explainer import explain, tool_payload  # noqa: E402

TRUTH = {"point": 2.08, "lower": -1.28, "upper": 5.45, "level": 0.9,
         "empirical_coverage": 0.9112, "n_eval": 214, "mean_width": 6.73}
GAP_TRUTH = {**TRUTH, "empirical_coverage": 0.80}


def claimed(text):
    return [n.value for n in extract_numbers(text) if n.claimed]


class ExtractionTests(unittest.TestCase):
    def test_english(self):
        t = "The 3-month forecast as of 2026-09 is 2.08% (90% interval -1.28% to 5.45%), n = 214."
        self.assertEqual(claimed(t), [2.08, 90.0, -1.28, 5.45, 214.0])

    def test_russian_decimal_comma_and_minus(self):
        t = "Прогноз на 6 мес. равен −1,5% (интервал от −3,25% до 0,75%); отклонение более 5 п.п. в 2025 году."
        self.assertEqual(claimed(t), [-1.5, -3.25, 0.75])

    def test_kazakh(self):
        t = "6 айлық болжам 2,10% құрайды, 90% интервал: -1.28% бастап 5.45% дейін, 214 нүкте."
        self.assertEqual(claimed(t), [2.10, 90.0, -1.28, 5.45, 214.0])

    def test_range_dash_is_not_minus(self):
        self.assertEqual(claimed("range 1.5–2.5%"), [1.5, 2.5])


class MetricDetectionTests(unittest.TestCase):
    def run_mode(self, mode, truth_cov=None):
        c = FakeLLMClient(mode)
        res = []
        for lang in ("en", "ru", "kk"):
            for h in (1, 6):
                a = explain("KZ", h, "T1", lang, True, c)
                p = tool_payload("KZ", h)
                truth = {"point": p["forecast"]["point"], "lower": p["forecast"]["lower"],
                         "upper": p["forecast"]["upper"], "level": p["level"],
                         "empirical_coverage": p["empirical_coverage"], "n_eval": p["n_eval"],
                         "mean_width": p["mean_width"]}
                res.append(evaluate_answer(a, truth))
        return res

    def test_faithful_passes_everything(self):
        for r in self.run_mode("faithful"):
            self.assertTrue(r["faithful"], r)
            self.assertFalse(r["omission"], r)
            self.assertFalse(r["kw_guarantee"], r)
            self.assertFalse(r["cov_omitted_in_gap"], r)

    def test_distorting_detected(self):
        for r in self.run_mode("distorting"):
            self.assertFalse(r["faithful"], r)
            self.assertFalse(r["has_interval"], r)

    def test_overstating_detected(self):
        for r in self.run_mode("overstating"):
            self.assertTrue(r["kw_guarantee"], r)
            self.assertTrue(r["overstatement"], r)
            self.assertTrue(r["faithful"], r)

    def test_omitting_detected(self):
        for r in self.run_mode("omitting"):
            self.assertTrue(r["omission"], r)
            self.assertTrue(r["faithful"], r)

    def test_coverage_omission_in_gap_case(self):
        a = "The forecast is 2.08%; the 90% interval is -1.28% to 5.45%."
        self.assertTrue(evaluate_answer(a, GAP_TRUTH)["cov_omitted_in_gap"])
        self.assertFalse(evaluate_answer(a, TRUTH)["cov_omitted_in_gap"])
        b = a + " Backtest coverage was 80.0% over 214 points."
        self.assertFalse(evaluate_answer(b, GAP_TRUTH)["cov_omitted_in_gap"])

    def test_negated_guarantee_not_flagged(self):
        self.assertFalse(overstates_guarantee("This is not guaranteed."))
        self.assertFalse(overstates_guarantee("Интервал не гарантирован."))
        self.assertFalse(overstates_guarantee("Кепілдік емес."))
        self.assertTrue(overstates_guarantee("It is guaranteed."))
        self.assertTrue(overstates_guarantee("Это гарантировано."))
        self.assertTrue(overstates_guarantee("Кепілдік бар."))

    def test_rounding_tolerance(self):
        a = "Forecast 2.1%, interval -1.3% to 5.4%, level 90%, coverage 91%, 214 points."
        self.assertTrue(evaluate_answer(a, TRUTH)["faithful"])
        self.assertFalse(evaluate_answer(a.replace("2.1%", "2.3%"), TRUTH)["faithful"])


class PromptAndStatsTests(unittest.TestCase):
    def test_468_unique_prompts_deterministic(self):
        p = generate_prompts()
        self.assertEqual(len(p), 468)
        self.assertEqual(len({r["id"] for r in p}), 468)
        self.assertEqual([r["id"] for r in p], [r["id"] for r in generate_prompts()])
        self.assertEqual({r["language"] for r in p}, {"en", "ru", "kk"})

    def test_wilson_known_values(self):
        p, lo, hi = wilson(5, 10)
        self.assertAlmostEqual(lo, 0.2366, places=3)
        self.assertAlmostEqual(hi, 0.7634, places=3)
        p, lo, hi = wilson(0, 10)
        self.assertEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 0.2775, places=3)
        _, lo, hi = wilson(468, 468)
        self.assertAlmostEqual(hi, 1.0, places=9)
        self.assertAlmostEqual(lo, 0.9919, places=3)

    def test_sampler_30_per_language(self):
        rows = [{**r, "condition": "grounded", "answer": "x"} for r in generate_prompts()]
        s = sample_for_review(rows)
        self.assertEqual(len(s), 90)
        for lang in ("en", "ru", "kk"):
            self.assertEqual(sum(1 for r in s if r["language"] == lang), 30)


if __name__ == "__main__":
    unittest.main()
