"""Single-reader judgements (by the model, not an independent human) of the 60-answer validation
sample, entered after reading each answer against its tool payload. T/F strings in order of the
sample file within each language: faithful, omission, overstated_kw (guarantee language asserted),
overstated_spec (kw or coverage omitted in a >5 pp gap case). Writes validation_sample.csv and prints agreement."""
import csv, argparse
from pathlib import Path
from collections import defaultdict

J = {
 "en": "TTFF TFFF TTFF TFFF TTFF TTFF TTFF FTFT TTFT TTFT FTFT TTFT TTFT TFFF TFFF TTFF TTFF TTFF TTFF TFFF",
 "ru": "TTFF TFFF TTFF TFFF TFFF TFFF TFFF TFFF TTFF TFFF TFFF TFFF TTFF TFFF TFFF TTFF TTFF TTFF TFFF TFFF",
 "kk": "TTFF TFFF TFFF TFFF TFFF TFFF TFFF TTFF TTFT TTFT TTFT TTFT TTFT TFFF TTFF TTFF TTFF TFFF TTFF TTFF",
}
NOTES = {  # id|condition -> note
 ("en", 12): "generic benchmark '80-90%' is not a claim about this forecast; metric counts it as unmatched",
 ("en", 17): "generic benchmark '80-90%'; metric counts it as unmatched",
 ("ru", 17): "generic benchmark '80-90%'; metric counts it as unmatched",
 ("kk", 18): "invented example '+-0,1-0,3 pp' marked 'for example'; borderline, judged not a claim",
 ("kk", 9): "generic '+-1-2 pp' interval, not a claim about this forecast",
 ("ru", 1): "list item under 'Нельзя делать выводы' negates the keyword; v2 sentence rule misses the lead-in",
}
ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); a = ap.parse_args()
out = Path(a.out)
rows = list(csv.DictReader(open(out / "validation_sample_input.csv", encoding="utf-8")))
by = defaultdict(list)
for r in rows: by[r["language"]].append(r)
res = []
for lang, rs in by.items():
    js = J[lang].split(); assert len(js) == len(rs) == 20, (lang, len(js), len(rs))
    for i, (r, j) in enumerate(zip(rs, js)):
        res.append({**{k: v for k, v in r.items() if k != "answer"},
                    "judge_faithful": j[0] == "T", "judge_omission": j[1] == "T",
                    "judge_overstated_kw": j[2] == "T", "judge_overstated_spec": j[3] == "T",
                    "note": NOTES.get((lang, i), ""), "answer": r["answer"]})
with open(out / "validation_sample.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(res[0])); w.writeheader(); w.writerows(res)
def b(x): return str(x) == "True"
lines = []
for ver in ("v1", "v2"):
    for name, jk, mk in (("faithful", "judge_faithful", "faithful"), ("omission", "judge_omission", "omission"),
                         ("overstatement(spec)", "judge_overstated_spec", "overstatement")):
        key = (lambda r: r["v2_" + mk]) if ver == "v2" else (lambda r: r["v1_" + mk])
        fp = sum(1 for r in res if b(key(r)) and not b(r[jk]))
        fn = sum(1 for r in res if not b(key(r)) and b(r[jk]))
        ag = sum(1 for r in res if b(key(r)) == b(r[jk]))
        lines.append(f"{ver} {name}: agree {ag}/60, metric-T-judge-F {fp}, metric-F-judge-T {fn}")
    # kw leg: v2 kw_guarantee column is in per_answer; sample input only has overstatement, derive kw = flagged and not gap-only
for r in res:
    pass
print("\n".join(lines))
print("judge counts:", {k: sum(b(r[k]) for r in res) for k in ("judge_faithful","judge_omission","judge_overstated_kw","judge_overstated_spec")})
