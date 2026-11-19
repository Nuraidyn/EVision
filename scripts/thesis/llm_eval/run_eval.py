"""Run the 468-prompt x 2-condition evaluation and compute the metrics.

  python run_eval.py --client fake --fake-mode faithful --out out_fake_faithful
  python run_eval.py --client openrouter --yes-spend --out out_real      (spends API credit)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import common  # noqa: F401
from app.services.inflation_explainer import explain, tool_payload
from fake_client import MODES, FakeLLMClient
from generate_prompts import generate_prompts
from metrics import evaluate_answer, summarize, summary_markdown, write_csv
from sampler import sample_for_review, write_review_csv

KEY_VARS = ("OPENROUTER_API_KEY", "GROQ_API_KEY")  # names read by app.core.config


def build_client(kind: str, mode: str, model: str | None = None):
    if kind == "fake":
        return FakeLLMClient(mode)
    if kind == "litellm":
        from app.services.inflation_explainer import LiteLLMClient
        return LiteLLMClient(model)
    from app.services.inflation_explainer import OpenRouterClient
    return OpenRouterClient()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", choices=("fake", "openrouter", "litellm"), default="fake")
    ap.add_argument("--model", default=None, help="LiteLLM model id (default: env LITELLM_MODEL)")
    ap.add_argument("--fake-mode", choices=MODES, default="faithful")
    ap.add_argument("--yes-spend", action="store_true")
    ap.add_argument("--out", default="out")
    ap.add_argument("--limit", type=int, default=0, help="use only the first N prompts (smoke test)")
    a = ap.parse_args(argv)

    prompts = generate_prompts()
    if a.limit:
        prompts = prompts[: a.limit]
    n_calls = len(prompts) * 2
    print(f"{len(prompts)} prompts x 2 conditions = {n_calls} LLM calls (client={a.client})")
    if a.client in ("openrouter", "litellm"):
        if not a.yes_spend:
            print(f"Refusing: the {a.client} client spends API credit; pass --yes-spend.")
            return 2
        if not any(os.environ.get(v) for v in KEY_VARS):
            print(f"Refusing: set one of {KEY_VARS} in the environment.")
            return 2

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    raw = out / "answers.jsonl"
    done: dict[tuple, str] = {}
    if raw.exists():  # resume after an interruption
        for line in raw.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            done[(r["id"], r["condition"])] = r["answer"]

    client = build_client(a.client, a.fake_mode, a.model)
    truths: dict[tuple, dict] = {}
    rows = []
    with raw.open("a", encoding="utf-8") as fh:
        for p in prompts:
            key = (p["country"], p["horizon"])
            if key not in truths:
                t = tool_payload(*key)
                truths[key] = {"point": t["forecast"]["point"], "lower": t["forecast"]["lower"],
                               "upper": t["forecast"]["upper"], "level": t["level"],
                               "empirical_coverage": t["empirical_coverage"], "n_eval": t["n_eval"],
                               "mean_width": t["mean_width"]}
            for cond in ("grounded", "ungrounded"):
                k = (p["id"], cond)
                if k in done:
                    ans = done[k]
                else:
                    ans = explain(p["country"], p["horizon"], p["question_type"], p["language"],
                                  cond == "grounded", client)
                    fh.write(json.dumps({"id": p["id"], "condition": cond, "answer": ans},
                                        ensure_ascii=False) + "\n")
                    fh.flush()
                m = evaluate_answer(ans, truths[key])
                rows.append({**p, "condition": cond, "answer": ans, **m})

    write_csv(str(out / "per_answer.csv"), rows)
    md = []
    for by in (("condition",), ("condition", "language"), ("condition", "question_type")):
        s = summarize(rows, by)
        write_csv(str(out / ("summary_" + "_".join(by) + ".csv")), s)
        md.append("Rates by " + ", ".join(by) + " (Wilson 95%)\n\n" + summary_markdown(s, by))
    (out / "summary.md").write_text("\n\n".join(md) + "\n", encoding="utf-8")
    write_review_csv(str(out / "manual_review_sample.csv"), sample_for_review(rows))
    print("\n\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
