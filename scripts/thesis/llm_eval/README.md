# LLM explanation layer: evaluation harness (protocol section L)

Implements the evaluation fixed in the eighth Changes entry of `docs/thesis/experiment-protocol.md`:
13 countries x 4 horizons x 3 question types x 3 languages = 468 prompts, each in two conditions
(grounded: tool JSON in the system prompt; ungrounded: question only). No judge model.

Service code: `backend/fastapi_service/app/services/inflation_explainer.py`
(`explain(country, horizon, question_type, language, grounded, llm_client)`; the client is injected,
`OpenRouterClient` adapts the project's `ai_mentor._call_openrouter`).

## Run

From `backend/fastapi_service` with `.venv-thesis-check/Scripts/python.exe`:

    python ../../scripts/thesis/llm_eval/generate_prompts.py --out prompts.csv
    python ../../scripts/thesis/llm_eval/run_eval.py --client fake --fake-mode faithful --out OUT
    python ../../scripts/thesis/llm_eval/run_eval.py --client openrouter --yes-spend --out OUT_REAL
    python -m pytest tests/test_inflation_explainer.py ../../scripts/thesis/llm_eval/tests

Outputs in OUT: `answers.jsonl` (raw, appended per call, a rerun resumes), `per_answer.csv`,
`summary_*.csv`, `summary.md`, `manual_review_sample.csv` (30 grounded answers per language,
seed 20261119, columns for fluency and terminology scores).

The openrouter path prints the number of calls (936), refuses without `--yes-spend`, and refuses
unless `OPENROUTER_API_KEY` (or `GROQ_API_KEY`, the fallback in `app/core/config.py`) is set.
Model: `OPENROUTER_MODEL` (default in config). The model id must be written into results before
the run, as the protocol requires. Estimated size: about 0.3M input and 0.2M output tokens.

## Implementation choices (not specified by the protocol)

Language codes `en`, `ru`, `kk`. Prompt id `CC-h{H}-T{n}-{lang}`; order: sorted country, horizon,
question type, language. Level is 0.9. Country names are localized in questions.

Number-to-quantity mapping (`metrics.py`):
1. Tokens: optional minus (`-`, `−`, `–` only if not preceded by a digit or letter), digits with
   `.` or `,` decimal, optional `%`. Dates like 2026-09 are masked first.
2. Not claims (ignored): years 1900..2100, integers <= 24 followed by a month word (en/ru/kk),
   integers <= 12 without `%`, numbers followed by pp / п.п. / процентных пунктов, and `100%`.
3. Every other token is a claim. It matches a quantity if within tol = max(0.05, half a unit of its
   displayed precision) of: forecast point, lower, upper, upper-lower, mean_width, level x 100,
   empirical coverage x 100 (percent scale); level and coverage as fractions (tol 0.005, tokens
   without `%`); n_eval (integer, exact). mean_width and the width are accepted additionally to the
   protocol's list because the API reports them.
4. Numerical faithfulness: all claims match; an answer with no claims is faithful vacuously (the
   omission rate catches it). Signs are compared.
5. Omission: not (lower and upper both matched and level matched). Applied to all question types.
6. Overstatement: guarantee/certainty keyword (guarant*, certainly, definitely, for sure, surely;
   гарант*, наверняка, безусловно, несомненно; кепіл*, сөзсіз, міндетті түрде) with no negation
   within 35 characters either side, OR coverage gap (coverage < level - 5 pp) and no token
   matching the empirical coverage.
7. Wilson 95% intervals, z = 1.96.

Known limits: when coverage lies within tolerance of the level, a "90%" token counts for both;
negation window is a heuristic; hedged phrasing without keywords is not detected. The manual
review covers these.

The fake client (`fake_client.py`) only exercises the harness; its tables are not results.
