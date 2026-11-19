import sys
from pathlib import Path

import pytest

PAPER_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PAPER_DIR))


@pytest.fixture(scope="session")
def built(tmp_path_factory):
    """Run the full pipeline once into a temporary directory."""
    from build_paper_assets import build

    out = tmp_path_factory.mktemp("paper_out")
    made = build(out)
    return out, made
