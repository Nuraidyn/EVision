import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common  # noqa: E402,F401
import metrics as v1  # noqa: E402
import metrics_v2 as v2  # noqa: E402

TRUTH = {"point": 0.36, "lower": -0.49, "upper": 1.27, "level": 0.9,
         "empirical_coverage": 0.9174, "n_eval": 218, "mean_width": 1.76}
GAP_TRUTH = {**TRUTH, "empirical_coverage": 0.80}


def claimed(text):
    return [n.value for n in v2.extract_numbers(text) if n.claimed]


class SignTests(unittest.TestCase):
    def test_defect_range_after_percent_en_dash(self):
        t = "Интервал -0.49%–1.27%, уровень 90%."
        self.assertEqual(claimed(t), [-0.49, 1.27, 90.0])
        self.assertEqual([n.value for n in v1.extract_numbers(t) if n.claimed][:2], [-0.49, -1.27])  # v1 defect

    def test_defect_comma_range(self):
        self.assertEqual(claimed("аралық 1,91%–2,96%"), [1.91, 2.96])

    def test_range_with_spaces_and_words(self):
        self.assertEqual(claimed("(-0.49% – 1.27%)"), [-0.49, 1.27])
        self.assertEqual(claimed("1.27% –1.5%"), [1.27, 1.5])
        self.assertEqual(claimed("от 1,5% до 2,5%"), [1.5, 2.5])
        self.assertEqual(claimed("1,5%-ден 2,5%-ға дейін"), [1.5, 2.5])
        self.assertEqual(claimed("1.5%-2.5%"), [1.5, 2.5])
        self.assertEqual(claimed("1.5%—2.5%"), [1.5, 2.5])

    def test_negative_lower_bound_stays_negative(self):
        self.assertEqual(claimed("from -0.49% to 1.27%"), [-0.49, 1.27])
        self.assertEqual(claimed("от −0,49% до 1,27%"), [-0.49, 1.27])
        self.assertEqual(claimed("(−0.49%–1.27%)"), [-0.49, 1.27])
        self.assertEqual(claimed("**−0.49%**"), [-0.49])
        self.assertEqual(claimed("interval=-0.49%"), [-0.49])
        self.assertEqual(claimed("interval: -0.49% to 1.27%"), [-0.49, 1.27])
        self.assertEqual(claimed("-0.49% to 1.27%"), [-0.49, 1.27])

    def test_faithful_range_answer(self):
        r = v2.evaluate_answer("Прогноз 0.36%; 90% интервал -0.49%–1.27%; покрытие 91.74% на 218 точках.", TRUTH)
        self.assertTrue(r["faithful"])
        self.assertFalse(r["omission"])
        self.assertFalse(v1.evaluate_answer("Прогноз 0.36%; 90% интервал -0.49%–1.27%; покрытие 91.74% на 218 точках.", TRUTH)["faithful"])

    def test_wrong_number_still_flagged(self):
        r = v2.evaluate_answer("Прогноз 0.36%; 90% интервал -0.49%–1.57%.", TRUTH)
        self.assertFalse(r["faithful"])
        self.assertEqual(r["n_unmatched"], 1)

    def test_wrong_sign_still_flagged(self):
        r = v2.evaluate_answer("Интервал от 0.49% до 1.27%, уровень 90%.", TRUTH)
        self.assertFalse(r["faithful"])

    def test_v1_cases_unchanged(self):
        self.assertEqual(claimed("range 1.5–2.5%"), [1.5, 2.5])
        self.assertEqual(claimed("Прогноз на 6 мес. равен −1,5% (интервал от −3,25% до 0,75%); более 5 п.п. в 2025 году."),
                         [-1.5, -3.25, 0.75])


class OverstatementTests(unittest.TestCase):
    NEGATED = [
        "The interval is not a guarantee of the outcome.",
        "Do not conclude that the actual value is guaranteed to fall inside the interval.",
        "This is not guaranteed, only a statistical estimate.",
        "Статистический интервал — это не гарантия.",
        "Модель не гарантирует, что значение попадёт в интервал.",
        "Это не означает, что инфляция наверняка окажется внутри интервала.",
        "Интервал не гарантирует попадания.",
        "Бұл кепілдік емес.",
        "Интервал міндетті түрде қамтиды деп айтуға болмайды.",
        "Нәтиже кепілдендірілмейді.",
        "Интервалды кепілдік деп түсінбеу керек.",
        "There is no guarantee that the outcome lies inside.",
    ]
    REAL = [
        "The interval is guaranteed to contain the outcome.",
        "Inflation will certainly stay within the interval.",
        "Интервал гарантированно накроет фактическое значение.",
        "Инфляция наверняка окажется в этом интервале.",
        "Интервал міндетті түрде қамтиды.",
        "Бұл интервал кепілдік береді.",
    ]

    def test_negated_not_flagged(self):
        for t in self.NEGATED:
            self.assertFalse(v2.overstates_guarantee(t), t)

    def test_real_overstatement_flagged(self):
        for t in self.REAL:
            self.assertTrue(v2.overstates_guarantee(t), t)

    def test_same_sentence_only(self):
        # negation in a different sentence does not rescue the keyword
        self.assertTrue(v2.overstates_guarantee("This is not noise. The interval is guaranteed to hold."))
        self.assertTrue(v2.overstates_guarantee("Это не шум.\nИнтервал гарантированно накроет значение."))
        # decimal point does not split a sentence
        self.assertFalse(v2.overstates_guarantee("The 0.36% interval does not guarantee anything."))

    def test_kazakh_percent_word_is_not_negation(self):
        self.assertTrue(v2.overstates_guarantee("Интервал 90 пайыз, міндетті түрде қамтиды."))
        self.assertFalse(v2.has_negation("90 пайыз интервал бағалау"))

    def test_v1_false_positive_fixed(self):
        t = "Интервал міндетті түрде қамтиды деп айтуға болмайды."
        self.assertTrue(v1.overstates_guarantee(t))
        self.assertFalse(v2.overstates_guarantee(t))

    def test_coverage_gap_clause_unchanged(self):
        r = v2.evaluate_answer("Прогноз 0.36%, 90% интервал -0.49% до 1.27%.", GAP_TRUTH)
        self.assertTrue(r["cov_omitted_in_gap"])
        self.assertTrue(r["overstatement"])
        r = v2.evaluate_answer("Прогноз 0.36%, 90% интервал -0.49% до 1.27%, покрытие 80.0%.", GAP_TRUTH)
        self.assertFalse(r["overstatement"])

    def test_deterministic(self):
        t = "Интервал гарантированно накроет значение. -0.49%–1.27%"
        self.assertEqual(v2.evaluate_answer(t, TRUTH), v2.evaluate_answer(t, TRUTH))


if __name__ == "__main__":
    unittest.main()
