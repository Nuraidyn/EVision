import json
import unittest

from app.services import inflation_explainer as ie
from app.services.inflation_calibration import calibrated_forecast


class RecordingClient:
    def __init__(self):
        self.calls = []

    def complete(self, system_prompt, user_prompt):
        self.calls.append((system_prompt, user_prompt))
        return "ok"


class ExplainTests(unittest.TestCase):
    def test_grounded_passes_api_json_and_rules(self):
        c = RecordingClient()
        self.assertEqual(ie.explain("KZ", 3, "T1", "ru", True, c), "ok")
        system, user = c.calls[0]
        blob = system.split(ie.TOOL_START, 1)[1].split(ie.TOOL_END, 1)[0]
        payload = json.loads(blob)
        api = calibrated_forecast("KZ", 3, 0.9)
        self.assertEqual(payload["forecast"], {k: api["forecast"][k] for k in ("point", "lower", "upper")})
        self.assertEqual(payload["level"], 0.9)
        self.assertEqual(payload["n_eval"], api["calibration"]["n_eval"])
        self.assertEqual(payload["empirical_coverage"], api["calibration"]["empirical_coverage"])
        self.assertEqual(payload["as_of"], api["as_of"])
        self.assertNotIn("history", payload)
        self.assertIn("ONLY the numbers", system)
        self.assertIn("never present the interval as guaranteed".lower(), system.lower().replace("never present", "never present"))
        self.assertIn("Answer language code: ru", system)
        self.assertIn("Казахстан", user)

    def test_ungrounded_has_no_tool_json(self):
        c = RecordingClient()
        ie.explain("BR", 12, "T3", "kk", False, c)
        system, user = c.calls[0]
        self.assertNotIn(ie.TOOL_START, system)
        self.assertIn("Answer language code: kk", system)
        self.assertIn("12", user)

    def test_question_types_and_languages_validated(self):
        with self.assertRaises(ValueError):
            ie.explain("KZ", 3, "T9", "en", False, RecordingClient())
        with self.assertRaises(ValueError):
            ie.explain("KZ", 3, "T1", "fr", False, RecordingClient())

    def test_all_templates_exist(self):
        for lang in ie.LANGUAGES:
            for qt in ie.QUESTION_TYPES:
                self.assertIn("3", ie.question_text("MX", 3, qt, lang))


if __name__ == "__main__":
    unittest.main()
