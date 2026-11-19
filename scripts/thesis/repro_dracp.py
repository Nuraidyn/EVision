"""Partial reproduction of the DRACP paper's one-step inflation setting (arXiv 2608.17079).

Uses the released `dracp` package (pip install dracp) through its public API; none of the
authors' pipeline scripts are executed. Setup copied from the authors' configs
(configs/inflation_*.yaml, identical across the five countries compared):
  target: annual HICP inflation rate (Eurostat prc_hicp_manr), features: lags 1,2,3,6,12,
  rolling means over 3 and 12 months of the lagged series, month sin/cos;
  chronological split 50% train / 25% calibration / 25% test; the base model is fitted once;
  calibration is updated online during the test period; nominal level 0.90.

Usage: py -I repro_dracp.py <dir with inflation_<GEO>.csv> [GEO,GEO,...]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from dracp import (AdaptiveConformalRegressor, ConformalPIDRegressor, DRACPConfig,
                   DRACPRegressor, FACIRegressor, RollingConformalRegressor,
                   SAOCPRegressor, SplitConformalRegressor)
from dracp.metrics import interval_metrics

ALPHA = 0.10
SEED = 42
DRACP_CFG = dict(calibration_window=120, target_window=24, temporal_decay=0.985,
                 bandwidth=2.0, adaptive_bandwidth=True, bandwidth_grid=[0.5, 1.0, 2.0, 4.0],
                 min_ess=20, max_weight=0.30, ratio_clip_min=0.1, ratio_clip_max=10.0,
                 n_regimes=3, regime_beta=1.0, alpha_step=0.02, fallback='global')
FEATURES = ['inflation_lag_1', 'inflation_lag_2', 'inflation_lag_3', 'inflation_lag_6',
            'inflation_lag_12', 'inflation_rolling_mean_3', 'inflation_rolling_mean_12',
            'month_sin', 'month_cos']


def prepare(csv):
    df = pd.read_csv(csv).rename(columns={'inflation': 'inflation'})
    df['date'] = pd.to_datetime(df['date'])
    df['inflation'] = pd.to_numeric(df['inflation'], errors='coerce')
    df = df.sort_values('date').drop_duplicates('date')
    for lag in (1, 2, 3, 6, 12):
        df[f'inflation_lag_{lag}'] = df['inflation'].shift(lag)
    df['inflation_rolling_mean_3'] = df['inflation'].shift(1).rolling(3).mean()
    df['inflation_rolling_mean_12'] = df['inflation'].shift(1).rolling(12).mean()
    df['month_sin'] = np.sin(2 * np.pi * df['date'].dt.month / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['date'].dt.month / 12)
    return df.dropna().reset_index(drop=True)


def methods():
    base = HistGradientBoostingRegressor(max_iter=150, learning_rate=0.05, random_state=SEED)
    win = DRACP_CFG['calibration_window']
    cfg = DRACPConfig(alpha=ALPHA, random_state=SEED, **{**DRACP_CFG, 'use_faci_control': True})
    return {
        'split_cp': SplitConformalRegressor(ALPHA, base),
        'rolling_cp': RollingConformalRegressor(ALPHA, win, base),
        'adaptive_cp': AdaptiveConformalRegressor(ALPHA, win, DRACP_CFG['alpha_step'], base),
        'faci': FACIRegressor(ALPHA, win, model=base),
        'saocp': SAOCPRegressor(ALPHA, win, model=base),
        'conformal_pid': ConformalPIDRegressor(ALPHA, win, model=base),
        'dracp': DRACPRegressor(cfg, base_model=base),
    }


def run_country(csv):
    df = prepare(csv)
    n = len(df)
    i, j = int(n * 0.50), int(n * 0.50) + int(n * 0.25)
    train, cal, test = df.iloc[:i], df.iloc[i:j], df.iloc[j:]
    out = []
    for name, m in methods().items():
        m.fit(train[FEATURES].to_numpy(), train['inflation'].to_numpy(),
              cal[FEATURES].to_numpy(), cal['inflation'].to_numpy())
        rows = []
        for x, y in zip(test[FEATURES].to_numpy(), test['inflation'].to_numpy()):
            r = m.predict_one(x)
            m.update_one(x, float(y), r)   # h = 1: the outcome is known before the next origin
            rows.append({'y': float(y), 'lower': r['lower'], 'upper': r['upper']})
        met = interval_metrics(pd.DataFrame(rows), ALPHA)
        out.append({'method': name, 'n_test': len(test), 'coverage': met['coverage'],
                    'mean_width': met['mean_width'], 'interval_score': met['mean_interval_score']})
    return out


def main(raw_dir, geos):
    allrows = []
    for g in geos:
        for r in run_country(Path(raw_dir) / f'inflation_{g}.csv'):
            allrows.append({'geo': g, **r})
    res = pd.DataFrame(allrows)
    pd.set_option('display.width', 160)
    print(res.pivot(index='geo', columns='method', values='coverage').round(3).to_string())
    summ = res.groupby('method').agg(coverage=('coverage', 'mean'), width=('mean_width', 'mean'),
                                     score=('interval_score', 'mean')).round(3)
    summ['abs_dev_from_0.90'] = (res.groupby('method')['coverage'].mean() - 0.90).abs().round(3)
    print('\nmean over countries (single seed, single fit):')
    print(summ.sort_values('abs_dev_from_0.90').to_string())


if __name__ == '__main__':
    main(sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else 'DE,FR,IT,ES,RO').split(','))
