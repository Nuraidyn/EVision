"""LLM explanation layer for the calibrated inflation forecast (protocol section L).

explain() answers a fixed-type question about a country and horizon. In the grounded condition
the calibrated-forecast service is called in-process as the tool and its JSON is placed in the
system prompt; in the ungrounded condition the same question is asked without it.

The language model is injected: any object with ``complete(system_prompt, user_prompt) -> str``.
``OpenAIClient`` calls an OpenAI-compatible endpoint (the LiteLLM proxy).
"""
from __future__ import annotations

import json
from typing import Protocol

from app.services.inflation_calibration import COUNTRY_NAMES, calibrated_forecast

LANGUAGES = ("en", "ru", "kk")
QUESTION_TYPES = ("T1", "T2", "T3")
LEVEL = 0.9
GAP_PP = 5.0
TOOL_START = "TOOL_RESULT_JSON:"
TOOL_END = "END_TOOL_RESULT"

LANGUAGE_NAMES = {"en": "English", "ru": "Russian", "kk": "Kazakh"}

COUNTRY_NAMES_L = {
    "en": dict(COUNTRY_NAMES),
    "ru": {
        "KZ": "Казахстан", "RU": "Россия", "AZ": "Азербайджан", "UZ": "Узбекистан",
        "CO": "Колумбия", "CL": "Чили", "PE": "Перу", "BR": "Бразилия", "MX": "Мексика",
        "NG": "Нигерия", "MN": "Монголия", "ID": "Индонезия", "ZA": "Южная Африка",
    },
    "kk": {
        "KZ": "Қазақстан", "RU": "Ресей", "AZ": "Әзірбайжан", "UZ": "Өзбекстан",
        "CO": "Колумбия", "CL": "Чили", "PE": "Перу", "BR": "Бразилия", "MX": "Мексика",
        "NG": "Нигерия", "MN": "Моңғолия", "ID": "Индонезия", "ZA": "Оңтүстік Африка",
    },
}

# Fixed question templates. {country} is the localized name, {h} the horizon in months.
QUESTION_TEMPLATES = {
    "en": {
        "T1": "What is the inflation forecast for {country} at {h} months, and what is its interval?",
        "T2": "How reliable is this forecast interval for {country} at {h} months?",
        "T3": "What should I NOT conclude from the forecast interval for {country} at {h} months?",
    },
    "ru": {
        "T1": "Каков прогноз инфляции для страны {country} на {h} мес. и каков его интервал?",
        "T2": "Насколько надёжен этот интервал прогноза для страны {country} на {h} мес.?",
        "T3": "Какие выводы НЕЛЬЗЯ делать из интервала прогноза для страны {country} на {h} мес.?",
    },
    "kk": {
        "T1": "{country} үшін {h} айға инфляция болжамы қандай және оның интервалы қандай?",
        "T2": "{country} үшін {h} айлық болжам интервалы қаншалықты сенімді?",
        "T3": "{country} үшін {h} айлық болжам интервалынан қандай қорытынды ЖАСАУҒА БОЛМАЙДЫ?",
    },
}


def question_text(country: str, horizon: int, question_type: str, language: str) -> str:
    name = COUNTRY_NAMES_L[language][country.upper()]
    return QUESTION_TEMPLATES[language][question_type].format(country=name, h=horizon)


class LLMClient(Protocol):
    def complete(self, system_prompt: str, user_prompt: str) -> str: ...


class OpenAIClient:
    """OpenAI-compatible chat endpoint (here the LiteLLM proxy): OPENAI_BASE_URL, OPENAI_API_KEY and
    OPENAI_MODEL from app.core.config. Deterministic sampling. Not used by any test."""

    def __init__(self, max_tokens: int = 2000, timeout: float = 120.0) -> None:
        self.max_tokens = max_tokens
        self.timeout = timeout

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        import re

        import httpx

        from app.core.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        r = httpx.post(
            f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={
                "model": OPENAI_MODEL,
                "messages": [{"role": "system", "content": system_prompt},
                             {"role": "user", "content": user_prompt}],
                "temperature": 0,
                "max_tokens": self.max_tokens,
            },
            timeout=self.timeout,
        )
        r.raise_for_status()
        text = (r.json()["choices"][0]["message"].get("content") or "").strip()
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()  # reasoning models
        if not text:
            raise RuntimeError("LLM returned empty content")
        return text


def tool_payload(country: str, horizon: int, level: float = LEVEL) -> dict:
    """The API result reduced to what the model is allowed to see (no history series)."""
    r = calibrated_forecast(country, horizon, level)
    return {
        "country": r["country"],
        "horizon_months": r["horizon"],
        "as_of": r["as_of"],
        "unit": "cumulative log growth of CPI in percent over the horizon",
        "forecast": {
            "point": r["forecast"]["point"],
            "lower": r["forecast"]["lower"],
            "upper": r["forecast"]["upper"],
        },
        "level": r["level"],
        "empirical_coverage": r["calibration"]["empirical_coverage"],
        "n_eval": r["calibration"]["n_eval"],
        "mean_width": r["calibration"]["mean_width"],
        "notes": r["notes"],
    }


def grounded_system_prompt(payload: dict, language: str) -> str:
    return (
        "You are an assistant that explains a calibrated inflation forecast to a non-expert.\n"
        f"Answer language code: {language}. Answer only in {LANGUAGE_NAMES[language]}.\n"
        "Rules:\n"
        "1. Use ONLY the numbers in the tool result below. Do not invent, round differently "
        "or recompute any number; copy values with at most 2 decimals.\n"
        "2. State the forecast interval (lower and upper limit, in percent) and its nominal "
        "level (e.g. 90%).\n"
        "3. State the measured backtest coverage (empirical_coverage, as a percentage) and the "
        "number of evaluated points (n_eval).\n"
        "4. Never present the interval as guaranteed or certain; it is a statistical estimate.\n"
        f"5. If the measured coverage is below the nominal level by more than {GAP_PP:.0f} "
        "percentage points, warn the user explicitly that the interval under-covered in the "
        "backtest.\n"
        "6. Keep the answer under 150 words.\n"
        f"{TOOL_START}\n{json.dumps(payload, ensure_ascii=False)}\n{TOOL_END}"
    )


def ungrounded_system_prompt(language: str) -> str:
    return (
        "You are an assistant that answers questions about inflation forecasts.\n"
        f"Answer language code: {language}. Answer only in {LANGUAGE_NAMES[language]}.\n"
        "Keep the answer under 150 words."
    )


def explain(
    country: str,
    horizon: int,
    question_type: str,
    language: str,
    grounded: bool,
    llm_client: LLMClient,
) -> str:
    if language not in LANGUAGES:
        raise ValueError(f"language must be one of {LANGUAGES}")
    if question_type not in QUESTION_TEMPLATES["en"]:
        raise ValueError(f"question_type must be one of {QUESTION_TYPES}")
    user = question_text(country, horizon, question_type, language)
    if grounded:
        system = grounded_system_prompt(tool_payload(country, horizon, LEVEL), language)
    else:
        system = ungrounded_system_prompt(language)
    return llm_client.complete(system, user)
