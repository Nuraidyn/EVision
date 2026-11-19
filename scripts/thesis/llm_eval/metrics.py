"""Programmatic metrics for the LLM explanation layer (no judge model).

Number-to-quantity mapping (see README):
 1. Extract numeric tokens (dot or comma decimals, optional minus, optional % sign).
 2. Drop tokens that are not claims: dates/years, horizon counts ("3 months"), small integers
    0..12 without % or decimals, thresholds in percentage points ("5 pp"), and "100%".
 3. A remaining ("claimed") token is faithful if it equals, within tol = max(0.05, half a unit of
    its displayed precision), one of the API quantities: point, lower, upper, upper-lower,
    mean_width, level*100, empirical_coverage*100 (percent scale); level and empirical_coverage
    as fractions (only for tokens without %); n_eval (integers, exact).
 4. Faithfulness of an answer: every claimed token matches. Vacuously true with no claims.
"""
from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass

GAP_PP = 5.0

_LETTER = "A-Za-zЀ-ӿԀ-ԯӘәҒғҚқҢңӨөҰұҮүҺһІі"
_NUM = re.compile(r"(?<![" + _LETTER + r"])(?P<sign>[-−–])?(?P<num>\d+(?:[.,]\d+)?)")
_DATE = re.compile(r"\b(?:19|20)\d{2}[-/.]\d{1,2}(?:[-/.]\d{1,2})?\b")
_PCT_AFTER = re.compile(r"^\s?(%|percent|процент|пайыз)", re.I)
_PP_AFTER = re.compile(r"^\s?(pp\b|p\.p\.|percentage point|п\.\s?п\.|пп\b|процентн|пайыздық)", re.I)
_MONTH_AFTER = re.compile(r"^\s?-?\s?(months?\b|mo\b|мес|месяц|ай)", re.I)


@dataclass
class Num:
    value: float
    decimals: int
    percent: bool
    start: int
    end: int
    claimed: bool = True


def extract_numbers(text: str) -> list[Num]:
    """All numeric tokens with a `claimed` flag (False = date, year, horizon, threshold...)."""
    masked = _DATE.sub(lambda m: " " * len(m.group()), text)
    out: list[Num] = []
    for m in _NUM.finditer(masked):
        raw = m.group("num")
        sign = m.group("sign")
        if sign:
            before = masked[m.start() - 1] if m.start() > 0 else " "
            if before.isalnum() or before in ".,":
                sign = None  # range separator, not a minus
        norm = raw.replace(",", ".")
        dec = len(norm.split(".")[1]) if "." in norm else 0
        val = float(norm)
        if sign:
            val = -val
        after = masked[m.end(): m.end() + 24]
        pct = bool(_PCT_AFTER.match(after))
        integer = dec == 0
        claimed = True
        if _PP_AFTER.match(after):
            claimed = False
        elif integer and not pct and 1900 <= abs(val) <= 2100:
            claimed = False
        elif integer and not pct and abs(val) <= 24 and _MONTH_AFTER.match(after):
            claimed = False
        elif integer and not pct and abs(val) <= 12:
            claimed = False
        elif pct and integer and val == 100:
            claimed = False
        out.append(Num(val, dec, pct, m.start(), m.end(), claimed))
    return out


def _tol(n: Num, fraction: bool = False) -> float:
    return max(0.005 if fraction else 0.05, 0.5 * 10 ** (-n.decimals))


def _pct_quantities(t: dict) -> dict[str, float]:
    return {
        "point": t["point"], "lower": t["lower"], "upper": t["upper"],
        "width": t["upper"] - t["lower"], "mean_width": t["mean_width"],
        "level": t["level"] * 100, "coverage": t["empirical_coverage"] * 100,
    }


def match_quantities(n: Num, t: dict) -> set[str]:
    """Names of API quantities the token equals within tolerance."""
    hit = set()
    for name, q in _pct_quantities(t).items():
        if q is not None and abs(n.value - q) <= _tol(n):
            hit.add(name)
    if not n.percent:
        if abs(n.value - t["level"]) <= _tol(n, True):
            hit.add("level")
        if abs(n.value - t["empirical_coverage"]) <= _tol(n, True):
            hit.add("coverage")
    if n.decimals == 0 and not n.percent and n.value == t["n_eval"]:
        hit.add("n_eval")
    return hit


_GUARANTEE = re.compile(
    r"guarant|\bcertainly\b|with certainty|\bdefinitely\b|for sure|\bsurely\b|"
    r"гарант|наверняка|безусловно|несомненно|"
    r"кепіл|сөзсіз|міндетті түрде",
    re.I,
)
_NEGATION = re.compile(
    r"\b(?:not|no|never|cannot|can't|without|neither|nor)\b|n't|\bне\b|\bнет\b|\bни\b|\bбез\b|"
    r"емес|жоқ|бермейд",
    re.I,
)


def overstates_guarantee(text: str) -> bool:
    """True if a guarantee/certainty keyword occurs without a negation within 35 characters."""
    for m in _GUARANTEE.finditer(text):
        ctx = text[max(0, m.start() - 35): m.start()] + " " + text[m.end(): m.end() + 35]
        if not _NEGATION.search(ctx):
            return True
    return False


def evaluate_answer(text: str, truth: dict) -> dict:
    nums = [n for n in extract_numbers(text) if n.claimed]
    matched: set[str] = set()
    unmatched = 0
    for n in nums:
        hit = match_quantities(n, truth)
        if hit:
            matched |= hit
        else:
            unmatched += 1
    gap = truth["empirical_coverage"] * 100 < truth["level"] * 100 - GAP_PP
    has_interval = "lower" in matched and "upper" in matched
    has_level = "level" in matched
    has_cov = "coverage" in matched
    kw = overstates_guarantee(text)
    cov_omit = gap and not has_cov
    return {
        "n_claimed": len(nums),
        "n_unmatched": unmatched,
        "faithful": unmatched == 0,
        "has_interval": has_interval,
        "has_level": has_level,
        "has_coverage": has_cov,
        "omission": not (has_interval and has_level),
        "gap_case": gap,
        "kw_guarantee": kw,
        "cov_omitted_in_gap": cov_omit,
        "overstatement": kw or cov_omit,
    }


def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float, float]:
    """Wilson score interval: (proportion, lower, upper). n = 0 gives (nan, nan, nan)."""
    if n == 0:
        return (math.nan, math.nan, math.nan)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


METRICS = ("faithful", "omission", "overstatement")
EXTRA = ("kw_guarantee", "cov_omitted_in_gap")


def summarize(rows: list[dict], by: tuple[str, ...] = ("condition",)) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        groups.setdefault(tuple(r[b] for b in by), []).append(r)
    out = []
    for key in sorted(groups):
        g = groups[key]
        rec = dict(zip(by, key))
        rec["n"] = len(g)
        for m in METRICS + EXTRA + ("gap_case",):
            k = sum(1 for r in g if str(r[m]) == "True")
            p, lo, hi = wilson(k, len(g))
            rec[m] = k
            rec[m + "_rate"] = p
            rec[m + "_lo"] = lo
            rec[m + "_hi"] = hi
        out.append(rec)
    return out


def summary_markdown(summary: list[dict], by: tuple[str, ...]) -> str:
    head = list(by) + ["n", "faithfulness", "omission", "overstatement"]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for s in summary:
        cells = [str(s[b]) for b in by] + [str(s["n"])]
        for m in METRICS:
            cells.append(f"{s[m + '_rate']*100:.1f}% [{s[m + '_lo']*100:.1f}, {s[m + '_hi']*100:.1f}] ({s[m]}/{s['n']})")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_csv(path: str, rows: list[dict]) -> None:
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
