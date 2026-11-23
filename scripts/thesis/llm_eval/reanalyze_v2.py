"""Re-analyse an existing answers.jsonl with metrics v2 (no LLM call, input is only read).

  python reanalyze_v2.py --answers ../../../docs/thesis/results/llm_eval_qwen/answers.jsonl \
                         --out ../../../docs/thesis/results/llm_eval_qwen_v2
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import common  # noqa: F401
import metrics as m1
import metrics_v2 as m2
from app.services.inflation_explainer import tool_payload
from generate_prompts import generate_prompts

FLAGS = ("faithful", "omission", "overstatement", "kw_guarantee")


def truth_for(country, horizon):
    t = tool_payload(country, horizon)
    return {"point": t["forecast"]["point"], "lower": t["forecast"]["lower"],
            "upper": t["forecast"]["upper"], "level": t["level"],
            "empirical_coverage": t["empirical_coverage"], "n_eval": t["n_eval"],
            "mean_width": t["mean_width"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    done = {}
    for line in Path(a.answers).read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        done[(r["id"], r["condition"])] = r["answer"]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows, v1rows, changed = [], [], []
    for p in generate_prompts():
        tr = truth_for(p["country"], p["horizon"])
        for cond in ("grounded", "ungrounded"):
            if (p["id"], cond) not in done:
                continue
            ans = done[(p["id"], cond)]
            e1, e2 = m1.evaluate_answer(ans, tr), m2.evaluate_answer(ans, tr)
            base = {**p, "condition": cond, "answer": ans}
            rows.append({**base, **e2, **{"v1_" + k: e1[k] for k in FLAGS},
                         "v1_n_unmatched": e1["n_unmatched"]})
            v1rows.append({**base, **e1})
            if any(e1[k] != e2[k] for k in FLAGS) or e1["n_unmatched"] != e2["n_unmatched"]:
                changed.append({"id": p["id"], "condition": cond, "language": p["language"],
                                "question_type": p["question_type"],
                                **{f"v1_{k}": e1[k] for k in FLAGS}, "v1_n_unmatched": e1["n_unmatched"],
                                **{f"v2_{k}": e2[k] for k in FLAGS}, "v2_n_unmatched": e2["n_unmatched"]})
    m2.write_csv(str(out / "per_answer_v2.csv"), rows)
    m2.write_csv(str(out / "v1_vs_v2_changed.csv"), changed)
    md = []
    for by in (("condition",), ("condition", "language"), ("condition", "question_type")):
        s = m2.summarize(rows, by)
        m2.write_csv(str(out / ("summary_v2_" + "_".join(by) + ".csv")), s)
        md.append("Rates by " + ", ".join(by) + " (Wilson 95%), metrics v2 (post hoc)\n\n" + m2.summary_markdown(s, by))
    # v1 vs v2 side by side
    cmp_md = ["v1 (pre-specified) vs v2 (post hoc) rates; k/n", ""]
    for by in (("condition",), ("condition", "language"), ("condition", "question_type")):
        s1, s2 = m1.summarize(v1rows, by), m2.summarize(rows, by)
        head = list(by) + ["n"] + [f"{k} v1 -> v2" for k in m1.METRICS]
        cmp_md += ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
        for x, y in zip(s1, s2):
            cells = [str(x[b]) for b in by] + [str(x["n"])]
            for k in m1.METRICS:
                cells.append(f"{x[k]} ({x[k+'_rate']*100:.1f}%) -> {y[k]} ({y[k+'_rate']*100:.1f}%)")
            cmp_md.append("| " + " | ".join(cells) + " |")
        cmp_md.append("")
    cmp_md.append(f"Answers with any changed flag or unmatched-claim count: {len(changed)} of {len(rows)}; "
                  "list in v1_vs_v2_changed.csv")
    (out / "summary_v2.md").write_text("\n\n".join(md) + "\n", encoding="utf-8")
    (out / "v1_vs_v2_comparison.md").write_text("\n".join(cmp_md) + "\n", encoding="utf-8")
    print("rows", len(rows), "changed", len(changed))


if __name__ == "__main__":
    main()
