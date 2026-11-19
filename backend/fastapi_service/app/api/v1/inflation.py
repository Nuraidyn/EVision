from fastapi import APIRouter, HTTPException, Query

from app.services.inflation_calibration import (
    InflationError,
    COUNTRY_NAMES,
    calibrated_forecast,
    list_countries,
)

router = APIRouter(tags=["inflation"])


@router.get("/inflation/countries")
def inflation_countries():
    return list_countries()


@router.get("/inflation/calibrated-forecast")
def inflation_calibrated_forecast(
    country: str = Query(..., min_length=2, max_length=3),
    horizon: int = Query(3),
    level: float = Query(0.9),
):
    if country.upper() not in COUNTRY_NAMES:
        raise HTTPException(status_code=404, detail=f"Unknown country '{country}'")
    try:
        return calibrated_forecast(country, horizon, level)
    except InflationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
