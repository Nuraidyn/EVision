"""Shared path setup: makes the backend package `app` importable from the harness."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parents[2] / "backend" / "fastapi_service"
for p in (str(BACKEND), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)
