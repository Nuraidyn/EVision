"""Manual-review sampler: 30 random answers per language, written to a CSV for human review."""
from __future__ import annotations

import csv
import random


def sample_for_review(rows: list[dict], per_language: int = 30, seed: int = 20261119,
                      condition: str = "grounded") -> list[dict]:
    rng = random.Random(seed)
    out = []
    for lang in ("en", "ru", "kk"):
        pool = sorted((r for r in rows if r["language"] == lang and r["condition"] == condition),
                      key=lambda r: r["id"])
        pick = rng.sample(pool, min(per_language, len(pool)))
        for r in sorted(pick, key=lambda r: r["id"]):
            out.append({"id": r["id"], "language": lang, "condition": condition,
                        "question": r["question"], "answer": r["answer"],
                        "fluency_1to5": "", "terminology_1to5": "", "comment": ""})
    return out


def write_review_csv(path: str, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "language", "condition", "question", "answer",
                                          "fluency_1to5", "terminology_1to5", "comment"])
        w.writeheader()
        w.writerows(rows)
