"""Metrics v2 (post hoc, ninth Changes entry of docs/thesis/experiment-protocol.md, 2026-11-23).

`metrics.py` (v1, pre-specified) is unchanged and its results stay reproducible. v2 differs from
v1 in exactly two places; everything else (non-claim rules, tolerances, quantity matching,
omission, coverage-gap clause, Wilson intervals) is imported from v1.

(a) Sign rule. A `-`, `−` or `–` is a minus sign only at a token start:
      start of text, or directly after whitespace or one of  ( [ = : * " « ~ ≈ < > _
    It is never a sign directly after a digit, `%`, a letter, `.` or `,`. If it is `–` and the
    closest preceding non-space character is a digit or `%`, it is a range separator. A separator
    ('-', '–', '—', 'to', 'до', '-ден', 'бастап'...) between two numbers never changes the sign of
    the second number. Example: '-0.49%–1.27%' reads as -0.49 and +1.27.

(b) Overstatement keywords (unchanged list): guarant*, certainly, with certainty, definitely,
    for sure, surely; гарант*, наверняка, безусловно, несомненно; кепіл*, сөзсіз,
    міндетті түрде. A keyword counts only if the SAME SENTENCE contains no negation/denial marker.
    Sentence split: after '.', '!', '?', '…' followed by whitespace/end of text, and at line breaks
    (not at ';' or ':').
    Negation markers:
      en: not, no, never, cannot, without, nor, neither (whole words), n't / n’t, 'rather than'
      ru: не, нет, нельзя, ни, без, отнюдь (whole words)
      kk: емес, жоқ (whole words), and negated verb forms: a word with >= 2 letters, then one of
          ма ме ба бе па пе (negation morpheme), then a word-final ending from
          { й йды йді ймыз йміз йсыз йсіз ймын ймін йтын йтін йық йік ған ген қан кен са се
            у уге уға уы ушы ды ді ты ті ңыз ңіз }
          e.g. болмайды, алмайды, бермейді, кепілдендірілмейді, түсінбеу, болмауы.
    The coverage-gap clause (coverage < level - 5 pp and no token equal to the empirical
    coverage) is unchanged. Known cost: a negation elsewhere in the sentence can mask a real
    overstatement (false negatives are possible).
Deterministic: no randomness, no external calls.
"""
from __future__ import annotations

import re

from metrics import (  # noqa: F401  (re-exported)
    GAP_PP, METRICS, Num, _DATE, _LETTER, _MONTH_AFTER, _PCT_AFTER, _PP_AFTER,
    match_quantities, summarize, summary_markdown, wilson, write_csv,
)

_NUM = re.compile(r"(?<![" + _LETTER + r"])(?P<sign>[-−–])?(?P<num>\d+(?:[.,]\d+)?)")
SIGN_PREV_OK = set("([=:*\"«~≈<>_")


def extract_numbers(text: str) -> list[Num]:
    """Like metrics.extract_numbers but with the v2 sign rule."""
    masked = _DATE.sub(lambda m: " " * len(m.group()), text)
    out: list[Num] = []
    for m in _NUM.finditer(masked):
        raw = m.group("num")
        sign = m.group("sign")
        if sign:
            i = m.start()
            before = masked[i - 1] if i > 0 else ""
            if before == "" or before.isspace() or before in SIGN_PREV_OK:
                if before.isspace() and sign == "–":
                    prev = masked[:i].rstrip()
                    if prev and (prev[-1].isdigit() or prev[-1] == "%"):
                        sign = None  # 'x% –y%': range separator
            else:
                sign = None  # after digit, %, letter, '.', ',' ...
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


_GUARANTEE = re.compile(
    r"guarant|\bcertainly\b|with certainty|\bdefinitely\b|for sure|\bsurely\b|"
    r"гарант|наверняка|безусловно|несомненно|"
    r"кепіл|сөзсіз|міндетті түрде",
    re.I,
)
_L = _LETTER
_W_BEFORE = r"(?<![" + _L + r"])"
_W_AFTER = r"(?![" + _L + r"])"
_NEG_WORDS = re.compile(
    _W_BEFORE + r"(?:not|no|never|cannot|without|nor|neither|"
    r"не|нет|нельзя|ни|без|отнюдь|емес|жоқ)" + _W_AFTER
    + r"|n['’]t\b|\brather than\b",
    re.I,
)
_KK_ENDINGS = (r"(?:й|йды|йді|ймыз|йміз|йсыз|йсіз|ймын|ймін|йтын|йтін|йық|йік|ған|ген|қан|кен|са|се|"
               r"у|уге|уға|уы|ушы|ды|ді|ты|ті|ңыз|ңіз)")
_KK_NEG = re.compile(
    _W_BEFORE + r"[" + _L + r"]{2,}?(?:ма|ме|ба|бе|па|пе)" + _KK_ENDINGS + _W_AFTER, re.I)
_SENT_SPLIT = re.compile(r"(?<=[.!?…])\s+|\n+")


def has_negation(sentence: str) -> bool:
    return bool(_NEG_WORDS.search(sentence) or _KK_NEG.search(sentence))


def split_sentences(text: str) -> list[str]:
    return [s for s in _SENT_SPLIT.split(text) if s and s.strip()]


def overstates_guarantee(text: str) -> bool:
    """True if a guarantee/certainty keyword occurs in a sentence with no negation marker."""
    return any(_GUARANTEE.search(s) and not has_negation(s) for s in split_sentences(text))


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
