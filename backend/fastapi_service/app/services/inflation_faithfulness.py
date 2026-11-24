"""Cheap programmatic check of an LLM answer against the numbers the model was given.

A minimal, self-contained copy of the numeric-faithfulness logic of the thesis evaluation
(``scripts/thesis/llm_eval/metrics_v2.py``, post hoc corrected metrics v2): every "claimed" number in
the answer (not a date, year, horizon or a bare small integer) must equal one of the tool-result
quantities within rounding tolerance. It does not check wording, fluency or correctness of
the explanation, and it can miss errors (for example a wrong number that happens to equal another
quantity). Deterministic; no external calls.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

GAP_PP = 5.0

_LETTER = "A-Za-zЀ-ӿԀ-ԯӘәҒғҚқҢңӨөҰұҮүҺһІі"
_NUM = re.compile(r"(?<![" + _LETTER + r"])(?P<sign>[-−–])?(?P<num>\d+(?:[.,]\d+)?)")
_DATE = re.compile(r"\b(?:19|20)\d{2}[-/.]\d{1,2}(?:[-/.]\d{1,2})?\b")
_PCT_AFTER = re.compile(r"^\s?(%|percent|процент|пайыз)", re.I)
_PP_AFTER = re.compile(r"^\s?(pp\b|p\.p\.|percentage point|п\.\s?п\.|пп\b|процентн|пайыздық)", re.I)
_MONTH_AFTER = re.compile(r"^\s?-?\s?(months?\b|mo\b|мес|месяц|ай)", re.I)
_SIGN_PREV_OK = set("([=:*\"«~≈<>_")


@dataclass
class _Num:
    value: float
    decimals: int
    percent: bool
    claimed: bool = True


def _extract(text: str) -> list[_Num]:
    masked = _DATE.sub(lambda m: " " * len(m.group()), text)
    out: list[_Num] = []
    for m in _NUM.finditer(masked):
        raw = m.group("num")
        sign = m.group("sign")
        if sign:
            i = m.start()
            before = masked[i - 1] if i > 0 else ""
            if before == "" or before.isspace() or before in _SIGN_PREV_OK:
                if before.isspace() and sign == "–":
                    prev = masked[:i].rstrip()
                    if prev and (prev[-1].isdigit() or prev[-1] == "%"):
                        sign = None  # 'x% –y%': range separator
            else:
                sign = None
        norm = raw.replace(",", ".")
        dec = len(norm.split(".")[1]) if "." in norm else 0
        val = -float(norm) if sign else float(norm)
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
        out.append(_Num(val, dec, pct, claimed))
    return out


def _tol(n: _Num, fraction: bool = False) -> float:
    return max(0.005 if fraction else 0.05, 0.5 * 10 ** (-n.decimals))


def _match(n: _Num, t: dict) -> set[str]:
    pct = {
        "point": t["point"], "lower": t["lower"], "upper": t["upper"],
        "width": t["upper"] - t["lower"], "mean_width": t.get("mean_width"),
        "level": t["level"] * 100, "coverage": t["empirical_coverage"] * 100,
    }
    hit = {k for k, q in pct.items() if q is not None and abs(n.value - q) <= _tol(n)}
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
    r"гарант|наверняка|безусловно|несомненно|кепіл|сөзсіз|міндетті түрде", re.I)
_W_B = r"(?<![" + _LETTER + r"])"
_W_A = r"(?![" + _LETTER + r"])"
_NEG = re.compile(
    _W_B + r"(?:not|no|never|cannot|without|nor|neither|не|нет|нельзя|ни|без|отнюдь|емес|жоқ)" + _W_A
    + r"|n['’]t\b|\brather than\b", re.I)
_KK_END = (r"(?:й|йды|йді|ймыз|йміз|йсыз|йсіз|ймын|ймін|йтын|йтін|йық|йік|ған|ген|қан|кен|са|се|"
           r"у|уге|уға|уы|ушы|ды|ді|ты|ті|ңыз|ңіз)")
_KK_NEG = re.compile(_W_B + r"[" + _LETTER + r"]{2,}?(?:ма|ме|ба|бе|па|пе)" + _KK_END + _W_A, re.I)
_SENT = re.compile(r"(?<=[.!?…])\s+|\n+")


def _overstates(text: str) -> bool:
    return any(_GUARANTEE.search(s) and not (_NEG.search(s) or _KK_NEG.search(s))
               for s in _SENT.split(text) if s and s.strip())


def check_numeric_faithfulness(answer: str, payload: dict | None) -> dict:
    """Compare the numbers in ``answer`` with the tool payload (as returned by ``tool_payload``).

    Returns ``checked=False`` when there is no payload (ungrounded answer: nothing to check against).
    """
    if not payload:
        return {"checked": False, "reason": "no tool data was given to the model, so there is nothing to compare with"}
    truth = {
        "point": payload["forecast"]["point"], "lower": payload["forecast"]["lower"],
        "upper": payload["forecast"]["upper"], "level": payload["level"],
        "empirical_coverage": payload["empirical_coverage"], "n_eval": payload["n_eval"],
        "mean_width": payload.get("mean_width"),
    }
    claimed = [n for n in _extract(answer) if n.claimed]
    matched: set[str] = set()
    unmatched: list[float] = []
    for n in claimed:
        hit = _match(n, truth)
        if hit:
            matched |= hit
        else:
            unmatched.append(n.value)
    gap = truth["empirical_coverage"] * 100 < truth["level"] * 100 - GAP_PP
    return {
        "checked": True,
        "n_claimed": len(claimed),
        "n_unmatched": len(unmatched),
        "unmatched_values": unmatched,
        "faithful": not unmatched,
        "states_interval": "lower" in matched and "upper" in matched,
        "states_level": "level" in matched,
        "states_coverage": "coverage" in matched,
        "coverage_gap_case": gap,
        "guarantee_wording": _overstates(answer),
        "scope": "numbers only (metrics v2, post hoc); not a check of wording or correctness of reasoning",
    }
