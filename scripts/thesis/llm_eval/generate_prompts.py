"""Deterministic generation of the 468 evaluation prompts (13 x 4 x 3 x 3)."""
from __future__ import annotations

import argparse
import csv

import common  # noqa: F401
from app.services.inflation_calibration import COUNTRY_NAMES, HORIZONS
from app.services.inflation_explainer import LANGUAGES, QUESTION_TYPES, question_text


def generate_prompts() -> list[dict]:
    rows = []
    for country in sorted(COUNTRY_NAMES):
        for h in HORIZONS:
            for qt in QUESTION_TYPES:
                for lang in LANGUAGES:
                    rows.append(
                        {
                            "id": f"{country}-h{h}-{qt}-{lang}",
                            "country": country,
                            "horizon": h,
                            "question_type": qt,
                            "language": lang,
                            "question": question_text(country, h, qt, lang),
                        }
                    )
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="prompts.csv")
    a = ap.parse_args()
    rows = generate_prompts()
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} prompts to {a.out}")
