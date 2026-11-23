# LLM explanation layer: evaluation harness (protocol section L)

Implements the evaluation fixed in the eighth Changes entry of `docs/thesis/experiment-protocol.md`:
13 countries x 4 horizons x 3 question types x 3 languages = 468 prompts, each in two conditions
(grounded: tool JSON in the system prompt; ungrounded: question only). No judge model.

Service code: `backend/fastapi_service/app/services/inflation_explainer.py`
(`explain(country, horizon, question_type, language, grounded, llm_client)`; the client is injected,
`OpenAIClient` calls an OpenAI-compatible endpoint, here the LiteLLM proxy).

## Run

From `backend/fastapi_service` with `.venv-thesis-check/Scripts/python.exe`:

    python ../../scripts/thesis/llm_eval/generate_prompts.py --out prompts.csv
    python ../../scripts/thesis/llm_eval/run_eval.py --client fake --fake-mode faithful --out OUT
    python ../../scripts/thesis/llm_eval/run_eval.py --client openai --yes-spend --out OUT_REAL
    python -m pytest tests/test_inflation_explainer.py ../../scripts/thesis/llm_eval/tests

Outputs in OUT: `answers.jsonl` (raw, appended per call, a rerun resumes), `per_answer.csv`,
`summary_*.csv`, `summary.md`, `manual_review_sample.csv` (30 grounded answers per language,
seed 20261119, columns for fluency and terminology scores).

The openai path prints the number of calls (936), refuses without `--yes-spend`, and refuses
unless `OPENAI_API_KEY` is set. Endpoint and model come from `OPENAI_BASE_URL` and `OPENAI_MODEL`
(read from `.env` by `app/core/config.py`); temperature 0. The model id must be written into results
before the run, as the protocol requires. Estimated size: about 0.3M input and 0.2M output tokens.

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

## Metrics v2 (post hoc, ninth Changes entry, 2026-11-23)

`metrics_v2.py` corrects two defects of the implementation found after the v1 results were seen;
`metrics.py` is unchanged and its numbers stay the pre-specified ones (primary-as-specified).
v2 numbers are always labelled post hoc. Everything not listed here is imported from v1.

1. Sign rule. `-`, `−`, `–` is a minus only at a token start: start of text, or directly after
   whitespace or one of `( [ = : * " « ~ ≈ < > _`; never directly after a digit, `%`, letter, `.` or `,`.
   `–` after whitespace that follows a digit or `%` is a range separator. Ranges such as
   `-0.49%–1.27%` or `1,91%–2,96%` read as -0.49/1.27 and 1.91/2.96.
2. Overstatement keywords (unchanged list) count only if the same sentence has no negation marker.
   Sentences split after `. ! ? …` followed by whitespace or end, and at line breaks (not `;`, `:`).
   Markers: en `not no never cannot without nor neither`, `n't`/`n’t`, `rather than`;
   ru `не нет нельзя ни без отнюдь`; kk `емес жоқ` and negated verb forms (word of >= 2 letters +
   `ма/ме/ба/бе/па/пе` + a word-final ending from a fixed list; e.g. болмайды, алмайды, бермейді,
   кепілдендірілмейді, түсінбеу). Exact regular expressions: docstring and code of `metrics_v2.py`.
3. Coverage-gap clause unchanged.

Known remaining limits of v2 (found when reading, not corrected, to be handled only through a new
Changes entry): a bullet item under a negating lead-in line ("Нельзя делать выводы:" followed by
"- что ... гарантированно ...") is a separate sentence and is flagged; an abbreviation such as
"мес." splits a sentence; any number is a claim, so generic benchmarks ("80-90% coverage") in
ungrounded answers count as unmatched; a negation elsewhere in the sentence can mask a real
overstatement.

Re-analysis (no LLM call, reads `answers.jsonl` only):

    python reanalyze_v2.py --answers ../../../docs/thesis/results/llm_eval_qwen/answers.jsonl --out ../../../docs/thesis/results/llm_eval_qwen_v2
    python make_validation_sample.py --out ../../../docs/thesis/results/llm_eval_qwen_v2   # seed 20261123
    python judge_validation.py --out ../../../docs/thesis/results/llm_eval_qwen_v2          # single-reader judgements

(run from `backend/fastapi_service` with the thesis venv). Tests: `tests/test_metrics_v2.py`.
