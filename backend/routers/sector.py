import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query
try:
    from ..data.history import analyze_distinct_history
except ImportError:
    from data.history import analyze_distinct_history
try:
    from ..data.sector_registry import get_all_sector_configs, get_sector_config
except ImportError:
    from data.sector_registry import get_all_sector_configs, get_sector_config

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

router = APIRouter()
DATA_GOV_BASE_URL = "https://api.data.gov.in/resource"


def _normalized_response(config: Any, records: list[dict[str, Any]], metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": config.status,
        "sector": config.sector,
        "component": config.component,
        "resource_id": config.resource_id,
        "source": "data.gov.in",
        "records": records,
        "metadata": metadata,
        "metric": metadata.get("metric"),
        "summary": metadata.get("message", f"{len(records)} public record(s) found for this component."),
        "fields": list(config.fields),
        "filters": config.filters,
    }


@router.get("/sector-status")
def sector_status() -> dict[str, Any]:
    """Return the verified data-source status for every app component."""
    return {"components": get_all_sector_configs()}


@router.get("/retail-prices")
def retail_prices(commodity: str, location: str | None = None) -> dict[str, Any]:
    try:
        from ..data.retail_service import get_retail_prices
    except ImportError:
        from data.retail_service import get_retail_prices
    return get_retail_prices(commodity, location)


@router.get("/sector-analysis")
async def sector_analysis(
    sector: str = Query(..., min_length=1),
    component: str = Query(..., min_length=1),
) -> dict[str, Any]:
    config = get_sector_config(sector, component)
    if config is None:
        raise HTTPException(status_code=404, detail="This sector/component is not configured in the data registry.")

    if config.status != "API_AVAILABLE" or not config.resource_id:
        return _normalized_response(config, [], {
            "message": (
                "The official dataset exists, but a Resource API is not currently available."
                if config.status == "API_UNAVAILABLE"
                else "No suitable official data.gov.in dataset is currently configured."
            ),
            "verification_note": config.verification_note,
            "dataset_found": config.dataset_found,
            "resource_api_available": config.api_available,
            "required_fields": list(config.fields),
            "supported_filters": config.filters,
        })

    if config.component == "Fresh fruits & vegetables":
        return _normalized_response(config, [], {
            "message": "This component uses the existing produce photo and freshness workflow.",
            "required_fields": list(config.fields),
            "supported_filters": config.filters,
        })

    api_key = os.getenv("DATA_GOV_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="DATA_GOV_API_KEY is not configured on the server.")

    # Fetch enough records to build a 10-distinct-period history
    params = {
        "api-key": api_key,
        "format": "json",
        "limit": 100,
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0, headers=headers) as client:
            response = await client.get(
                f"{DATA_GOV_BASE_URL}/{config.resource_id}",
                params=params,
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=502,
            detail=f"data.gov.in returned HTTP {error.response.status_code} for this sector resource.",
        ) from error
    except httpx.RequestError as error:
        raise HTTPException(
            status_code=502,
            detail="Unable to reach data.gov.in. Check network connectivity.",
        ) from error

    records = payload.get("records", [])
    history = analyze_distinct_history(
        records,
        config.date_field,
        config.value_field,
        aggregate=config.aggregation,
    )
    return _normalized_response(config, records, {
        "total": payload.get("total"),
        "count": len(records),
        "required_fields": list(config.fields),
        "supported_filters": config.filters,
        "metric": {
            "name": config.metric_name,
            "unit": config.unit,
            "periods_available": history.get("periods_available", 0),
            **history,
        },
    })
