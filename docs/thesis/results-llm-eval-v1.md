# LLM explanation layer: evaluation results (2026-11-23)

Status: results of the evaluation specified in rule L (eighth Changes entry) with the programmatic
metrics, plus a post hoc correction of two metric defects (ninth Changes entry). The component is an
engineering extension; no result here enters the main claims of the thesis, and the evaluation has
no pass threshold. Scripts: `scripts/thesis/llm_eval/` (`metrics.py` = v1, pre-specified;
`metrics_v2.py` = post hoc). Raw answers: `docs/thesis/results/llm_eval_qwen/answers.jsonl`
(unchanged); v1 tables in the same directory; v2 tables in `docs/thesis/results/llm_eval_qwen_v2/`.

## 1. Setup

- Model: `qwen3.8-27b` (`OPENAI_MODEL` in `.env`), accessed through an OpenAI-compatible LiteLLM
  proxy (host `litellm.cic.kz`), temperature 0.
- 468 prompts (13 countries x 4 horizons x 3 question types x 3 languages) x 2 conditions
  (grounded: tool JSON in the system prompt; ungrounded: question only) = 936 answers. All 936
  completed, no failed calls.
- Decoding budget: `max_tokens` 8000; on `finish_reason == "length"` the call is retried with the
  budget doubled up to 32000. 3 parallel workers.
- Mixed budgets: the first 37 answers in `answers.jsonl` come from an earlier run that crashed and
  used `max_tokens` 2000/8000; the resume kept those answers instead of regenerating them, so the
  token budget is not identical across all 936 answers.
- Temperature 0 gives one answer per prompt; the proxy does not guarantee bit-identical reruns, and
  no repeated runs were done, so there is no estimate of run-to-run variation.

## 2. Pre-specified metrics (v1, primary-as-specified)

Wilson 95% intervals. Source: `docs/thesis/results/llm_eval_qwen/summary.md`.

| condition | n | faithfulness | omission | overstatement |
|---|---|---|---|---|
| grounded | 468 | 90.6% [87.6, 92.9] (424/468) | 9.0% [6.7, 11.9] (42/468) | 23.3% [19.7, 27.3] (109/468) |
| ungrounded | 468 | 69.0% [64.7, 73.0] (323/468) | 100.0% [99.2, 100.0] (468/468) | 26.5% [22.7, 30.7] (124/468) |

Grounded by language: faithfulness en 100%, ru 96.8%, kk 75.0%; omission en 0%, ru 3.2%, kk 23.7%;
overstatement en 19.2%, ru 21.2%, kk 29.5%. Grounded by question type: overstatement T1 5.1%,
T2 6.4%, T3 58.3%. Full tables: `summary.md`.

## 3. Two metric defects and the post hoc v2 numbers

The defects were found by reading answers after the v1 numbers were known, so v2 is post hoc
(`docs/thesis/experiment-protocol.md`, ninth entry, written before v2 was computed). The v1 numbers
remain the primary-as-specified result; v2 numbers are labelled post hoc.

(a) Ranges. `-0.49%–1.27%` or `1,91%–2,96%` (en dash after a percent sign) was read as an upper bound
of -1.27 / -2.96, which never matches the API value and creates one unmatched claim. This accounts for
all 39 inspected grounded Kazakh answers that v1 called unfaithful although their text was correct,
and it also removes the interval from the "has interval" check, which is where most of the v1
omission came from.

(b) Negated guarantee words. v1 looked for a negation within 35 characters of the keyword; "not a
guarantee", "не гарантирует", "кепілдік емес", "... деп айтуға болмайды" and similar were flagged.
T3 questions ask what not to conclude and are hit hardest.

Post hoc v2 (`docs/thesis/results/llm_eval_qwen_v2/`; v1 -> v2, k/n):

| condition | n | faithfulness | omission | overstatement |
|---|---|---|---|---|
| grounded | 468 | 424 -> 468 (90.6% -> 100.0% [99.2, 100.0]) | 42 -> 0 (9.0% -> 0.0% [0.0, 0.8]) | 109 -> 14 (23.3% -> 3.0% [1.8, 5.0]) |
| ungrounded | 468 | 323 -> 323 (69.0%) | 468 -> 468 (100%) | 124 -> 61 (26.5% -> 13.0% [10.3, 16.4]) |

Grounded by language (v2): faithfulness 156/156 and omission 0/156 in en, ru and kk; overstatement
en 0, kk 0, ru 14 (9.0%). Grounded by question type (v2): overstatement T1 0, T2 0, T3 14 (9.0%).
Ungrounded overstatement by language (v2): en 6 (3.8%), kk 7 (4.5%), ru 48 (30.8%). Tables with
intervals and the list of the 185 answers whose flags changed: `summary_v2.md`,
`v1_vs_v2_comparison.md`, `v1_vs_v2_changed.csv`.

Remaining defects in v2 (found by reading, not corrected, because another rule change needs a new
Changes entry):

- All 59 residual guarantee-keyword flags (14 grounded, 45 ungrounded; 58 Russian, 1 Kazakh) look like
  false positives. 57 of the 58 flagged bullet items sit under a negating lead-in line ("Нельзя делать
  выводы:" followed by "- что ... гарантированно ..."), which a sentence-level rule cannot see; one is
  a Kazakh list whose negation comes after the list; one Russian answer is split by the abbreviation
  "мес.". I read the 14 grounded flags; for the others the lead-in was checked by pattern, not by
  reading each. The grounded overstatement of 3.0% is therefore what this rule produces, not an
  estimate of real overstatement; I found no real "guaranteed" claim among the grounded flags.
- The coverage-gap leg applies to 18 prompts per condition where coverage is more than 5 pp below
  nominal. All 18 grounded answers state the coverage; ungrounded answers cannot, so the ungrounded
  overstatement contains these 18 by construction.
- Every number is a claim, so generic benchmarks in ungrounded answers ("80-90% coverage") count as
  unmatched.

## 4. Validation of v2 by reading (single reader)

A seeded (20261123) stratified sample of 60 answers (20 en, 20 ru, 20 kk; per language 7 where v1 and
v2 disagree, 6 where v2 flags overstatement, 7 others; both conditions, T1-T3 mixed) was read against
the tool payload by me, the model that wrote the analysis. This is a single-reader judgement by the
model, not an independent human review, and it was made knowing the v1 and v2 flags. Table with
judgements: `docs/thesis/results/llm_eval_qwen_v2/validation_sample.csv`.

Agreement with my judgement (n = 60). "Overstatement" = guarantee language asserted, or empirical
coverage omitted when it is more than 5 pp below nominal:

| metric | v1 agree | v1 disagreements | v2 agree | v2 disagreements |
|---|---|---|---|---|
| faithful | 51/60 | 9 (metric unfaithful, judged faithful) | 56/60 | 4 (metric unfaithful, judged faithful) |
| omission | 55/60 | 5 (metric omitted, judged stated) | 60/60 | 0 |
| overstatement | 35/60 | 25 (metric flagged, judged not) | 52/60 | 8 (metric flagged, judged not) |

Every disagreement of v1 and v2 is a false alarm; neither missed a case I judged problematic. The 4 v2
faithfulness disagreements are ungrounded answers with generic benchmark numbers ("80-90%", "+-1-2 pp")
that I judged not to be claims about the forecast; the 8 overstatement disagreements are the
list-under-negation cases above (7 Russian, 1 Kazakh). The two answers I judged numerically unfaithful
(invented forecasts) were also flagged by v2. I found no answer in the sample that really presents the
interval as guaranteed (0/60), so the sensitivity of the keyword rule to real overstatement is tested
only by the unit-test positive controls (`tests/test_metrics_v2.py`: "is guaranteed to contain the
outcome", "гарантированно накроет", "міндетті түрде қамтиды"), not by these data. The coverage-gap leg
flagged 11 sample answers and I agreed with all 11, but that leg is mechanical. The sample was
enriched for disagreements, so the counts are not rates, and 60 is small.

## 5. Manual review

`manual_review_sample.csv` has 90 grounded answers (30 per language, seed 20261119; the figure of 185
rows is the 186 physical lines of the file, answers contain line breaks) with empty fluency and
terminology columns. This scoring has not been done. It must be done by humans; the Kazakh fluency
and terminology judgement must come from a native speaker. My reading of Kazakh above covers numbers
and negation only, not fluency.

## 6. Interpretation and limits

What the numbers support, for this one model, these 468 prompts and these programmatic metrics:

- With the tool payload in the context, the answers repeated the API numbers without a mismatch under
  v2 (468/468, Wilson lower bound 99.2%), and every grounded answer stated the interval, the level and
  the empirical coverage, including the 18 where coverage was well below nominal. Under the
  pre-specified v1 the same answers scored 90.6% faithful with a Kazakh gap (75.0%); the gap was a
  tokenizer artefact of ranges written with an en dash, not wrong Kazakh numbers (39 of 39 inspected
  cases; also the validation sample).
- The 100% and 0% grounded results are a ceiling of what these metrics can see. They check that
  numbers equal some API value and that the interval and level appear; they do not check that the
  explanation is correct, useful or well worded.
- I found no real guarantee claims in grounded answers; the 3.0% is residual false alarms. This says
  nothing about phrasing the keyword rule does not cover ("точно окажется", hedges without keywords).

What cannot be concluded:

- No claim that "grounding works" in general: one model, one prompt template, temperature 0, one run,
  13 countries, no other models or prompts, no repeated runs. The grounded numbers largely follow from
  copying values out of the context.
- The ungrounded condition is a floor, not a competitor. Omission is 100% by construction (no data in
  the context). "Faithful" for ungrounded answers means that no wrong number was claimed: 312 of the
  468 ungrounded answers contain no claimed number (refusals, requests for the data, general advice;
  all T3 answers), so they are faithful vacuously. Only 156 ungrounded answers contain claims (T1 88,
  T2 68), and 145 of them have at least one number that matches nothing in the payload, for example an
  invented "4.5% with an interval of 3.5% to 5.5%" for Kazakhstan whose payload interval is far wider.
  Some of those 145 are generic benchmarks, not invented forecasts (see above), so the count overstates
  inventions. The ungrounded faithfulness of 44% for T1 is thus a mix of refusals (vacuously faithful)
  and invented numbers.
- The ungrounded v2 overstatement rate (13.0%) is not informative: 61 flags are the 18 coverage-gap cases (by
  construction) and the 45 keyword flags (list-item false alarms, mostly Russian T3 answers), with an overlap of 2.
- Language: after the correction no language gap remains in grounded faithfulness or omission in this
  data. The Russian excess of flagged overstatement (9.0%) is the list-format artefact above, not a
  finding about Russian. Kazakh fluency and terminology are untested (section 5).
- The v1 numbers and the post hoc v2 numbers must be reported together; v2 was designed after the v1
  results were seen and checked by one reader who knew the flags.
