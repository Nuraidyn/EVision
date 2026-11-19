import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # scripts/thesis
sys.path.insert(0, str(Path(__file__).resolve().parent))


def synth_cpi(n=200, start="2005-01", seed=0, drop=()):
    rng = np.random.default_rng(seed)
    m = np.zeros(n)
    for t in range(1, n):
        m[t] = 0.3 + 0.5 * (m[t - 1] - 0.3) + rng.normal(0, 0.3)
    idx = pd.period_range(start, periods=n, freq="M")
    cpi = pd.Series(100 * np.exp(np.cumsum(m) / 100), index=idx)
    return cpi.drop([idx[i] for i in drop]) if drop else cpi


def synth_fx(cpi, seed=1):
    rng = np.random.default_rng(seed)
    return pd.Series(np.exp(np.cumsum(rng.normal(0, 0.02, len(cpi)))), index=cpi.index)


@pytest.fixture
def cpi():
    return synth_cpi()
