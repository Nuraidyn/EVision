"""Read the precomputed thesis benchmark (built offline by scripts/thesis/build_demo_data.py)."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.core.config import INFLATION_BENCHMARK_PATH


class BenchmarkUnavailable(RuntimeError):
    pass


@lru_cache(maxsize=2)
def _load(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise BenchmarkUnavailable(
            "thesis_benchmark.json not found; build it with scripts/thesis/build_demo_data.py"
        )
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_benchmark(path: str | None = None) -> dict:
    return _load(str(path or INFLATION_BENCHMARK_PATH))
