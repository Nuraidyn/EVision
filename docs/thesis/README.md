# Thesis workspace

EVision is also the practical part of a master's thesis in Data Science (AI/ML x economics).
This folder holds the research documents; the code lives in `scripts/thesis/` and in the
platform modules listed below.

Topic: see `topic.md` (English, Russian, Kazakh).

## Documents

| File | Purpose |
|---|---|
| `topic.md` | Working title, research question and contribution in three languages |
| `experiment-protocol.md` | Fixed design: data, forecasters, interval methods, evaluation, primary contrasts, claim hierarchy, reproduction status |
| `shock-definition.md` | Frozen FX-stress rule, validity checks, disclosures, change log |

## Code

| Path | Purpose |
|---|---|
| `scripts/thesis/*.mjs` | Data download (IMF via DBnomics and the IMF SDMX API), shock and stress rules, validity checks |
| `scripts/thesis/data/` | Dated, hashed data snapshots (`snapshot.json` exploratory, `confirmatory.json` confirmatory) |
| `scripts/thesis/repro_dracp.py` | Partial reproduction of the DRACP paper's one-step inflation setting |
| `scripts/thesis/exp/` | Experiment engine (forecasters, interval methods, rolling-origin evaluation, power simulation) |
| `backend/fastapi_service/app/services/inflation_calibration.py` | Platform service for calibrated inflation intervals |
| `frontend/` (calibrated inflation page) | User-facing view of those intervals |

Python for the experiments: `scripts/thesis/.venv` (Python 3.12; pandas, statsmodels,
scikit-learn, LightGBM, `dracp`). Create it with
`uv venv --python 3.12 .venv` and `uv pip install --python .venv/Scripts/python.exe pandas numpy scipy statsmodels scikit-learn lightgbm dracp matplotlib requests PyYAML joblib pytest`.

## Working rules

1. **Exploratory versus confirmatory.** Months up to 2025-05 (first snapshot) are exploratory.
   Target months from 2025-07 (second snapshot) are confirmatory and are used only after the
   protocol is committed. Claims about transfer or stress come from the confirmatory set.
2. **Frozen documents.** `shock-definition.md` and `experiment-protocol.md` are changed only
   through their "Changes" section, with a date and a reason, before any affected result is
   recomputed.
3. **Independent review.** The project skill `thesis-committee` (`.claude/skills/`) runs a
   Sonnet reviewer that scores a decision from 1 to 10 and proposes a concrete fix. It is run
   at each major decision (topic, novelty claim, data, protocol, method, results), and again
   after fixing its objections.
4. **Honest reporting.** Negative and inconclusive results are reported as such. A contrast
   whose minimum detectable difference is too large is labelled inconclusive, not as "no
   effect".
5. **No tuning on the test period** and no change of a threshold to raise a result after
   looking at it. Anything computed on the exploratory snapshot is exploratory.
