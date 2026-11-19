# exp: experiment engine (protocol: docs/thesis/experiment-protocol.md)

Run from `scripts/thesis` with the venv interpreter:

    .venv/Scripts/python.exe -m pytest exp/tests -q
    .venv/Scripts/python.exe -m exp.run smoke            # 2 countries, h=3,6, ~30 s -> results/smoke/
    .venv/Scripts/python.exe -m exp.run full [--countries BR,MX] [--horizons 1,3,6,12] [--start 2000-01] [--resume]

Modules: data (targets, features, stretches, FX stress), forecasters (naive A/B, ETS, ARIMA, LightGBM),
intervals (split/rolling/ACI/FACI/PID/DRACP via `dracp` with a pass-through base model and delayed
feedback), evaluate (rolling origin, metrics, block bootstrap, contrasts, stress deciles), power (MDE), run (CLI).
`data/confirmatory.json` is merged automatically if present (snapshot wins on overlap).

Decisions (not fixed by the protocol): min_train=60 months, n_cal=48 warm-up residuals, window 120,
ACI step 0.02, FACI/PID/DRACP package defaults + repro_dracp.py DRACP config; DRACP warm-up split 50/50
train/cal; first evaluated origin n_cal+h-1; infinite radii capped at 10x max residual; failed
statsmodels fits carry the last point forecast forward (column n_fallback); ARIMA = ARMA(p,q<=2) on
monthly inflation + 2 annual harmonics, AICc, re-selected every 12 origins; ETS = additive seasonal;
native ARIMA intervals are Gaussian (psi-weights), ETS native by simulation (400 paths).
