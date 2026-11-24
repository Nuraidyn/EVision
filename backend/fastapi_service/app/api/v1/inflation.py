import logging
import threading
import time
from collections import deque
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core import config
from app.services.inflation_calibration import (
    HORIZONS,
    InflationError,
    COUNTRY_NAMES,
    calibrated_forecast,
    list_countries,
)
from app.services.inflation_compare import DEFAULT_WARMUP, compare_methods
from app.services.inflation_explainer import (
    LLMClient,
    OpenAIClient,
    explain,
    question_text,
    tool_payload,
)
from app.services.inflation_faithfulness import check_numeric_faithfulness
from app.services.thesis_benchmark import BenchmarkUnavailable, load_benchmark

logger = logging.getLogger(__name__)
router = APIRouter(tags=["inflation"])

# These routes are public (like the other inflation routes). The LLM endpoint spends money, so it
# has a small in-process cap on top of the global rate-limit middleware.
_EXPLAIN_CALLS: deque[float] = deque()
_EXPLAIN_LOCK = threading.Lock()


def _explain_quota() -> None:
    limit = config.INFLATION_EXPLAIN_MAX_PER_MINUTE
    now = time.monotonic()
    with _EXPLAIN_LOCK:
        while _EXPLAIN_CALLS and now - _EXPLAIN_CALLS[0] > 60.0:
            _EXPLAIN_CALLS.popleft()
        if len(_EXPLAIN_CALLS) >= limit:
            retry = max(1, int(60 - (now - _EXPLAIN_CALLS[0])))
            raise HTTPException(
                status_code=429,
                detail=f"Too many explanation requests (limit {limit} per minute). Try again later.",
                headers={"Retry-After": str(retry)},
            )
        _EXPLAIN_CALLS.append(now)


def get_llm_client() -> LLMClient:
    """Dependency: the proxy-backed client, or 503 when no key is configured (tests override this)."""
    if not config.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="The explanation service is not configured on this server (no LLM credentials).",
        )
    return OpenAIClient(
        max_tokens=config.INFLATION_EXPLAIN_MAX_TOKENS,
        timeout=max(30.0, config.OPENAI_TIMEOUT_SECONDS * 3),
        max_attempts=1,
    )


@router.get("/inflation/countries")
def inflation_countries():
    return list_countries()


def _check_country(country: str) -> None:
    if country.upper() not in COUNTRY_NAMES:
        raise HTTPException(status_code=404, detail=f"Unknown country '{country}'")


@router.get("/inflation/calibrated-forecast")
def inflation_calibrated_forecast(
    country: str = Query(..., min_length=2, max_length=3),
    horizon: int = Query(3),
    level: float = Query(0.9),
):
    _check_country(country)
    try:
        return calibrated_forecast(country, horizon, level)
    except InflationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/inflation/benchmark")
def inflation_benchmark():
    """Precomputed thesis results (built offline from the committed result files)."""
    try:
        return load_benchmark()
    except BenchmarkUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/inflation/compare")
def inflation_compare(
    country: str = Query(..., min_length=2, max_length=3),
    horizon: int = Query(3),
    level: float = Query(0.9),
    warmup: int = Query(DEFAULT_WARMUP, description="revealed residuals before the first interval"),
    n_last: int = Query(120, description="number of most recent origins in the series"),
):
    _check_country(country)
    try:
        return compare_methods(country, horizon, level, warmup=warmup, n_last=n_last)
    except InflationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class ExplainRequest(BaseModel):
    country: str
    horizon: int
    question_type: Literal["T1", "T2", "T3"]
    language: Literal["en", "ru", "kk"]
    grounded: bool = True


@router.post("/inflation/explain")
def inflation_explain(body: ExplainRequest, client: LLMClient = Depends(get_llm_client)):
    code = body.country.upper()
    if code not in COUNTRY_NAMES:
        raise HTTPException(status_code=404, detail=f"Unknown country '{body.country}'")
    if body.horizon not in HORIZONS:
        raise HTTPException(status_code=400, detail=f"horizon must be one of {list(HORIZONS)}")
    _explain_quota()
    try:
        reference = tool_payload(code, body.horizon)
    except InflationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    t0 = time.monotonic()
    try:
        answer = explain(code, body.horizon, body.question_type, body.language, body.grounded, client)
    except Exception as exc:  # network, proxy, or model failure: never echo details (may contain URLs)
        logger.warning("inflation explain failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=503,
            detail="The explanation service is temporarily unavailable. Try again later.",
        ) from None
    elapsed = time.monotonic() - t0
    return {
        "country": code,
        "horizon": body.horizon,
        "question_type": body.question_type,
        "language": body.language,
        "grounded": body.grounded,
        "question": question_text(code, body.horizon, body.question_type, body.language),
        "answer": answer,
        # What the model was allowed to see: the tool payload when grounded, nothing when not.
        "model_saw": reference if body.grounded else None,
        # The true values of the same forecast service; for an ungrounded answer these are values
        # the model did NOT see, used only to check its numbers.
        "reference": reference,
        "check": check_numeric_faithfulness(answer, reference),
        "model": config.OPENAI_MODEL,
        "seconds": round(elapsed, 1),
        "evaluation_note": (
            "Evaluated on one model with post hoc corrected metrics (v2): grounded answers 100% "
            "numerically faithful (90.6% under the pre-specified v1 metrics); ungrounded answers "
            "cannot state a calibrated interval. The programmatic check covers numbers only."
        ),
    }
