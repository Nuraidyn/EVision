"""Seeded (20261123) stratified validation sample of 60 answers: 20 per language.
Per language: 7 from answers where v1 and v2 differ, 6 from v2-overstated (not in the first pool),
7 from the rest. Writes validation_sample_input.csv (no judgements) into --out. Deterministic."""
import argparse, csv, random
from pathlib import Path
import common  # noqa: F401
from reanalyze_v2 import truth_for

ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); a = ap.parse_args()
out = Path(a.out)
rows = list(csv.DictReader(open(out / "per_answer_v2.csv", encoding="utf-8")))
FL = ("faithful", "omission", "overstatement")
rng = random.Random(20261123)
sample = []
for lang in ("en", "ru", "kk"):
    pool = sorted([r for r in rows if r["language"] == lang], key=lambda r: (r["id"], r["condition"]))
    A = [r for r in pool if any(r[k] != r["v1_" + k] for k in FL)]
    B = [r for r in pool if r["overstatement"] == "True" and r not in A]
    C = [r for r in pool if r not in A and r not in B]
    for name, P, k in (("v1v2_disagree", A, 7), ("v2_overstated", B, 6), ("other", C, 7)):
        for r in rng.sample(P, min(k, len(P))):
            sample.append({**r, "stratum": name})
    # top up to 20 from the rest if a pool was small
    have = [s for s in sample if s["language"] == lang]
    while len(have) < 20:
        r = rng.choice(C)
        if all(r["id"] != s["id"] or r["condition"] != s["condition"] for s in have):
            s = {**r, "stratum": "other"}; sample.append(s); have.append(s)
rows_out = []
for s in sample:
    t = truth_for(s["country"], int(s["horizon"]))
    rows_out.append({"id": s["id"], "condition": s["condition"], "language": s["language"],
                     "question_type": s["question_type"], "stratum": s["stratum"],
                     "truth_point": t["point"], "truth_lower": t["lower"], "truth_upper": t["upper"],
                     "truth_level": t["level"], "truth_coverage": t["empirical_coverage"], "truth_n_eval": t["n_eval"],
                     **{"v2_" + k: s[k] for k in FL}, **{"v1_" + k: s["v1_" + k] for k in FL},
                     "answer": s["answer"]})
with open(out / "validation_sample_input.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows_out[0])); w.writeheader(); w.writerows(rows_out)
print(len(rows_out))
