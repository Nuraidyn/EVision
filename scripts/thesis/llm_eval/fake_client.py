"""Deterministic fake LLM client with switchable behaviours. Never touches the network.

Modes: faithful, distorting (numbers changed), overstating (says 'guaranteed', omits coverage),
omitting (no interval, no level, no coverage). It reads the tool JSON from the system prompt
when present (grounded); otherwise it invents numbers from a hash of the question (ungrounded).
"""
from __future__ import annotations

import json
import re
import zlib

import common  # noqa: F401
from app.services.inflation_explainer import COUNTRY_NAMES_L, TOOL_END, TOOL_START

MODES = ("faithful", "distorting", "overstating", "omitting")


def _fmt(x: float, comma: bool) -> str:
    s = f"{x:.2f}"
    return s.replace(".", ",") if comma else s


class FakeLLMClient:
    def __init__(self, mode: str = "faithful"):
        if mode not in MODES:
            raise ValueError(mode)
        self.mode = mode
        self.calls: list[tuple[str, str]] = []

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        lang = re.search(r"Answer language code: (\w+)", system_prompt).group(1)
        h = zlib.crc32(user_prompt.encode("utf-8"))
        comma = lang == "ru" and h % 2 == 1
        if TOOL_START in system_prompt:
            blob = system_prompt.split(TOOL_START, 1)[1].split(TOOL_END, 1)[0]
            d = json.loads(blob)
            return self._grounded(d, lang, comma)
        return self._ungrounded(user_prompt, lang, comma, h)

    # ------------------------------------------------------------------ grounded
    def _grounded(self, d: dict, lang: str, comma: bool) -> str:
        f = d["forecast"]
        point, lo, hi = f["point"], f["lower"], f["upper"]
        cov, n = d["empirical_coverage"] * 100, d["n_eval"]
        lvl = round(d["level"] * 100)
        hz = d["horizon_months"]
        name = COUNTRY_NAMES_L[lang][d["country"]]
        gap = cov < lvl - 5
        if self.mode == "distorting":
            point, lo, hi, n = point + 0.40, lo - 0.30, hi * 1.2 + 0.5, n + 7
        p, l, u, c = (_fmt(x, comma) for x in (point, lo, hi, cov))
        if self.mode == "omitting":
            return {
                "en": f"{name}: the {hz}-month forecast is {p}%.",
                "ru": f"{name}: прогноз на {hz} мес. составляет {p}%.",
                "kk": f"{name}: {hz} айлық болжам {p}% құрайды.",
            }[lang]
        guaranteed = self.mode == "overstating"
        if lang == "en":
            t = (f"{name}: the {hz}-month forecast of cumulative inflation is {p}% (as of {d['as_of']}). "
                 f"The {lvl}% interval is from {l}% to {u}%. ")
            if guaranteed:
                return t + "The outcome is guaranteed to fall inside this interval."
            t += f"In the backtest it covered the outcome {c}% of the time over {n} evaluated points. "
            t += "The interval is an estimate and is not guaranteed."
            if gap:
                t += " Warning: coverage was more than 5 percentage points below the nominal level."
            return t
        if lang == "ru":
            t = (f"{name}: прогноз накопленной инфляции на {hz} мес. равен {p}% (по состоянию на {d['as_of']}). "
                 f"{lvl}% интервал: от {l}% до {u}%. ")
            if guaranteed:
                return t + "Результат гарантированно окажется внутри этого интервала."
            t += f"В бэктесте интервал накрывал итог в {c}% случаев на {n} оценённых точках. "
            t += "Интервал является оценкой и не гарантирован."
            if gap:
                t += " Предупреждение: покрытие ниже номинального более чем на 5 п.п."
            return t
        t = (f"{name}: {hz} айлық жиынтық инфляция болжамы {p}% ({d['as_of']} жағдайы бойынша). "
             f"{lvl}% интервал: {l}% бастап {u}% дейін. ")
        if guaranteed:
            return t + "Нәтиже осы интервалдың ішінде болатынына кепілдік бар."
        t += f"Бэктестте интервал {n} бағаланған нүктеде жағдайдың {c}% қамтыды. "
        t += "Интервал тек бағалау, кепілдік емес."
        if gap:
            t += " Ескерту: қамту номиналдан 5 п.п.-тан астам төмен."
        return t

    # ---------------------------------------------------------------- ungrounded
    def _ungrounded(self, user: str, lang: str, comma: bool, h: int) -> str:
        p = 1.0 + (h % 400) / 100.0
        lo, hi = p - 1.5 - (h % 7) / 10, p + 1.7
        l, u, pp = _fmt(lo, comma), _fmt(hi, comma), _fmt(p, comma)
        guaranteed = self.mode == "overstating"
        if lang == "en":
            return f"The forecast is about {pp}% with a likely range of {l}% to {u}%." + (
                " This is guaranteed." if guaranteed else "")
        if lang == "ru":
            return f"Прогноз около {pp}%, вероятный диапазон от {l}% до {u}%." + (
                " Это гарантировано." if guaranteed else "")
        return f"Болжам шамамен {pp}%, ықтимал аралық {l}% бастап {u}% дейін." + (
            " Бұған кепілдік бар." if guaranteed else "")
