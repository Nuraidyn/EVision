# EVision AI

**AI-powered economic analysis platform.** Compare macroeconomic indicators across countries, forecast trends, and get intelligent explanations — powered by LLM + RAG.

Supports three languages: **English · Русский · Қазақша**

---

## What Makes It AI

### AI Economic Mentor
A full ChatGPT-style interface for economic analysis. Ask anything about the data you're viewing — the AI answers with structured insights grounded in a curated economic knowledge base.

**How it works (RAG pipeline):**
```
Your question
     │
     ▼
RAG Retriever          sentence-transformers all-MiniLM-L6-v2
     │ top-4 chunks     cosine similarity over 9 economic knowledge files
     ▼
Context Builder        rolling 6-msg history + live chart data + retrieved chunks
     │
     ▼
LLM (Llama 3.3 70B)   via OpenRouter — OpenAI-compatible API
     │
     ▼
Structured response    { summary, insights[], limitations, suggested_next_steps[] }
```

RAG is chosen over fine-tuning: knowledge lives in editable markdown files, updates require no retraining, and retrieved chunks are fully transparent.

### Chart Insight Agent
Embedded in the analysis workspace — ask a question about any chart and receive an AI explanation using OpenAI (`gpt-4o-mini`) or Google Gemini (`gemini-2.5-flash`). Falls back to a local statistical summary if no API key is configured.

---

## Core Features

| Feature | Description |
|---|---|
| **Country comparison** | 30+ indicators (GDP, inflation, unemployment, trade, demographics) across any countries |
| **Forecasting** | Linear trend with 95% confidence intervals, backtest (MAE/RMSE), 1–20 year horizon |
| **Income inequality** | Lorenz curves, Gini coefficient, country rankings and trends over time |
| **AI Mentor** | Full conversational AI with session memory, follow-up suggestions, and report export |
| **Chart Insight** | Per-chart AI explanations inline with the analysis |
| **Saved presets** | Save and reload your analysis configurations |
| **Calibrated inflation intervals** | Monthly inflation forecasts for 13 emerging economies, 11 of which are commodity-dependent by the UNCTAD 60% criterion (commodities at least 60% of merchandise exports, 2021-2023), with conformally calibrated intervals (ACI) and the measured backtest coverage next to the nominal level (`/inflation-intervals`). ACI is used because adaptive calibration was better calibrated than a calibration done once; the thesis benchmark did not establish that it beats a rolling window (see `docs/thesis/results-holdout-v1.md`) |

---

## Research Component (Master's Thesis)

EVision is the practical part of a master's thesis in Data Science:
**Evaluating Methods for Building Reliable Prediction Intervals for Machine-Learning Inflation Forecasts in Commodity-Dependent Economies.**
The title in Russian and Kazakh, the research question and the contribution are in
[`docs/thesis/topic.md`](docs/thesis/topic.md). "Commodity-dependent" is defined there by the UNCTAD
60% criterion (commodities at least 60% of merchandise exports, 2021-2023, applied post hoc): 27 of the
30 economies of the three panels meet it; Mexico, Indonesia and Georgia do not and are kept as
comparison cases.

- Design and rules: [`docs/thesis/README.md`](docs/thesis/README.md),
  [`experiment-protocol.md`](docs/thesis/experiment-protocol.md),
  [`shock-definition.md`](docs/thesis/shock-definition.md).
- Data and experiments: [`scripts/thesis/`](scripts/thesis/) (dated, hashed IMF snapshots;
  exploratory and confirmatory samples are kept apart).
- Platform module: `GET /api/v1/inflation/calibrated-forecast`, served by
  `backend/fastapi_service/app/services/inflation_calibration.py`.

The platform applies the same ACI procedure as the benchmark but with a simpler point forecast
(an exponentially weighted average of monthly growth, minimum calibration size 30) than the
benchmark's models, so the coverage it reports is its own backtest coverage and not the
benchmark's numbers.

### Demo: the thesis inside the product (`/inflation-research`)

A presenter can show the thesis live on one page with four tabs (also linked from the Navbar and from
`/inflation-intervals`). Every number carries an evidence tag (pre-specified, exploratory or post hoc) and
every tab has a disclaimer box (research prototype, not advice, descriptive results).

| Tab | What it shows | Endpoint |
|---|---|---|
| Forecast | The existing calibrated forecast page | `GET /api/v1/inflation/calibrated-forecast` |
| Methods compared | Live rolling-origin backtest of split, rolling-window and ACI intervals for any country and horizon: coverage against the 90% nominal level, calibration error, mean width, interval band with covered and missed outcomes, running coverage. Warm-up 48 residuals by default (the forecast page uses 30) | `GET /api/v1/inflation/compare?country=KZ&horizon=3` |
| What we found | Precomputed results: calibration error by method, horizon, panel and base model; primary contrasts with Holm p, minimum detectable difference and the verdict shown / not shown / inconclusive (rule R5/E5: MDE undefined or above 7 pp is inconclusive); UNCTAD commodity badge per country; Chronos accuracy on clean months; feedback delay at h=12; native versus ACI intervals | `GET /api/v1/inflation/benchmark` |
| Explain it | The LLM explanation layer (en/ru/kk): grounded (sees the forecast service output) versus ungrounded (no data), the numbers the model saw, and a programmatic numeric check. Evaluated on one model with post hoc corrected metrics (grounded 100% numerically faithful under v2, 90.6% under the pre-specified v1) | `POST /api/v1/inflation/explain` |

The benchmark JSON is built offline and committed; rebuild it after any change to `docs/thesis/results/`:

```bash
cd scripts/thesis
.venv/Scripts/python.exe build_demo_data.py          # writes backend/fastapi_service/app/data/thesis_benchmark.json
.venv/Scripts/python.exe build_demo_data.py --check  # fails if the committed file is stale
```

Run the demo: start the backend (`cd backend/fastapi_service && .venv-thesis-check/Scripts/python.exe -m uvicorn app.main:app --port 8001`)
and the frontend (`cd frontend && npm run dev`), then open `/inflation-research`. The first three tabs need no
credentials. The "Explain it" tab calls an OpenAI-compatible endpoint configured in `.env` (`OPENAI_BASE_URL`,
`OPENAI_API_KEY`, `OPENAI_MODEL`); without a key it answers 503 with a clear message and the rest of the page keeps
working. The endpoint is public like the other inflation routes and has an in-process cap
(`INFLATION_EXPLAIN_MAX_PER_MINUTE`, default 20) and a token limit (`INFLATION_EXPLAIN_MAX_TOKENS`, default 4000).

---

## Tech Stack

| Layer | Technologies |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, Chart.js |
| AI / LLM | OpenRouter (Llama 3.3 70B), OpenAI, Google Gemini, sentence-transformers |
| Analytics backend | FastAPI + SQLAlchemy |
| Auth backend | Django 4 + DRF + SimpleJWT |
| Database | PostgreSQL (Docker) / SQLite (local) |

---

## Architecture

Two backends with separate responsibilities:

```
                        React Frontend
                              │
              ┌───────────────┴───────────────┐
              │                               │
        Django :8000                    FastAPI :8001
        Auth · JWT · Presets            Analytics · Forecast
                                        AI Mentor · Chart Explain
              └───────────────┬───────────────┘
                              │
                         PostgreSQL
```

FastAPI validates JWTs by introspecting Django's `/api/auth/introspect` endpoint. All AI and analytics endpoints require a valid JWT + accepted data agreement.

---

## Quick Start

**Docker (recommended):**
```bash
cp .env.example .env
# Fill in your API keys
docker compose up -d --build
```

**Local dev:**
```bash
bash dev.sh
```

Services: Frontend `http://localhost:5173` · Django `http://127.0.0.1:8000/api` · FastAPI `http://127.0.0.1:8001/api/v1`

---

## Key Environment Variables

| Variable | Service | Purpose |
|---|---|---|
| `OPENROUTER_API_KEY` | FastAPI | LLM for AI Mentor (Llama 3.3 70B) |
| `OPENAI_API_KEY` | FastAPI | Chart explanations via GPT-4o-mini |
| `GEMINI_API_KEY` | FastAPI | Chart explanations via Gemini |
| `CHART_EXPLAIN_PROVIDER` | FastAPI | `openai` / `gemini` / `auto` |
| `DJANGO_SECRET_KEY` | Both | JWT signing secret — change in production |
| `DATABASE_URL` | FastAPI | SQLAlchemy URL (default: SQLite) |

See `.env.example` for the full list.

---

## AI Mentor Knowledge Base

Nine curated economic markdown files power the RAG retriever:

`gdp.md` · `inflation.md` · `unemployment.md` · `gini_lorenz.md` · `trade_balance.md` · `demographics.md` · `chart_reading.md` · `forecasting_limitations.md` · `indicator_relationships.md`

Each file is chunked (~300 words, 50-word overlap), embedded at startup with `all-MiniLM-L6-v2`, and stored as a normalized numpy matrix in memory — no vector database required. To update knowledge: edit a markdown file and restart FastAPI, or call `POST /api/v1/ai/reindex` (admin only).

---

## Running Tests

```bash
# Frontend
cd frontend && npm test

# Django
cd backend/django_service && python manage.py test core.tests

# FastAPI
cd backend/fastapi_service && python -m pytest tests/
```
