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
    from ..data.fuel_data import get_all_fuel_data
except ImportError:
    from data.fuel_data import get_all_fuel_data
try:
    from ..data.wastewater_data import get_all_wastewater_data
except ImportError:
    from data.wastewater_data import get_all_wastewater_data
try:
    from ..data.sector_data_stores import (
        get_chemicals_data,
        get_construction_data,
        get_ewaste_data,
        get_procurement_data,
    )
except ImportError:
    from data.sector_data_stores import (
        get_chemicals_data,
        get_construction_data,
        get_ewaste_data,
        get_procurement_data,
    )
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
        "source": metadata.get("source", "data.gov.in"),
        "records": records,
        "metadata": metadata,
        "metric": metadata.get("metric"),
        "fuel_data": metadata.get("fuel_data"),
        "wastewater_data": metadata.get("wastewater_data"),
        "analytics_data": metadata.get("analytics_data"),
        "summary": metadata.get("summary") or metadata.get("message", f"{len(records)} public record(s) found for this component."),
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

    if config.component == "Fossil fuels like petrol, diesel, and coal":
        fuel_payload = get_all_fuel_data()
        petrol_info = fuel_payload.get("petrol", {})
        tirupattur_petrol = petrol_info.get("districts", {}).get("Tirupattur", {})
        history_points = [
            {"date": item["display_date"], "value": item["price"]}
            for item in tirupattur_petrol.get("history", [])
        ]
        return _normalized_response(config, fuel_payload.get("records", []), {
            "source": fuel_payload.get("source", "PPAC / Regional Fuel Price Data"),
            "total": fuel_payload.get("total_records", 0),
            "count": len(fuel_payload.get("records", [])),
            "required_fields": list(config.fields),
            "supported_filters": config.filters,
            "summary": fuel_payload.get("summary"),
            "fuel_data": fuel_payload,
            "metric": {
                "name": "Petrol & Diesel Price Analysis",
                "unit": config.unit,
                "current_value": tirupattur_petrol.get("current_price", 107.74),
                "average_10_days": tirupattur_petrol.get("average_10_days", 107.74),
                "high_10_days": tirupattur_petrol.get("high_10_days", 107.74),
                "low_10_days": tirupattur_petrol.get("low_10_days", 107.74),
                "percentage_change": tirupattur_petrol.get("percentage_change", 0.0),
                "trend": tirupattur_petrol.get("trend", "STABLE"),
                "periods_available": len(history_points),
                "history": history_points,
            },
        })

    if config.component == "Industrial wastewater and factory effluents":
        ww_payload = get_all_wastewater_data()
        effluent_info = ww_payload.get("effluent", {})
        ranipet_effluent = effluent_info.get("districts", {}).get("Ranipet", {})
        history_points = [
            {"date": item["display_date"], "value": item["volume"]}
            for item in ranipet_effluent.get("history", [])
        ]
        return _normalized_response(config, ww_payload.get("records", []), {
            "source": ww_payload.get("source", "CPCB / TNPCB Continuous Effluent Monitoring"),
            "total": ww_payload.get("total_records", 0),
            "count": len(ww_payload.get("records", [])),
            "required_fields": list(config.fields),
            "supported_filters": config.filters,
            "summary": ww_payload.get("summary"),
            "wastewater_data": ww_payload,
            "metric": {
                "name": "Industrial Effluent & Treated Wastewater (MLD)",
                "unit": config.unit,
                "current_value": ranipet_effluent.get("current_volume", 18.2),
                "average_10_days": ranipet_effluent.get("average_10_days", 17.07),
                "high_10_days": ranipet_effluent.get("high_10_days", 18.5),
                "low_10_days": ranipet_effluent.get("low_10_days", 11.0),
                "percentage_change": ranipet_effluent.get("percentage_change", 0.0),
                "trend": ranipet_effluent.get("trend", "STABLE"),
                "periods_available": len(history_points),
                "history": history_points,
            },
        })

    if config.component == "E-waste like smartphones, laptops, and batteries":
        ew_payload = get_ewaste_data()
        primary_info = ew_payload.get("primary", {})
        vellore_ew = primary_info.get("districts", {}).get("Vellore", {})
        history_points = [
            {"date": item["display_date"], "value": item["value"]}
            for item in vellore_ew.get("history", [])
        ]
        return _normalized_response(config, ew_payload.get("records", []), {
            "source": ew_payload.get("source"),
            "total": ew_payload.get("total_records", 0),
            "count": len(ew_payload.get("records", [])),
            "required_fields": list(config.fields),
            "supported_filters": config.filters,
            "summary": ew_payload.get("summary"),
            "analytics_data": ew_payload,
            "metric": {
                "name": "E-Waste Generation & Recycling (MT)",
                "unit": config.unit,
                "current_value": vellore_ew.get("current_value", 1.85),
                "average_10_days": vellore_ew.get("average_10_days", 1.67),
                "high_10_days": vellore_ew.get("high_10_days", 1.86),
                "low_10_days": vellore_ew.get("low_10_days", 0.90),
                "percentage_change": vellore_ew.get("percentage_change", 0.0),
                "trend": vellore_ew.get("trend", "STABLE"),
                "periods_available": len(history_points),
                "history": history_points,
            },
        })

    if config.component == "Industrial solvents, paints, and manufacturing toxins":
        chem_payload = get_chemicals_data()
        primary_info = chem_payload.get("primary", {})
        ranipet_chem = primary_info.get("districts", {}).get("Ranipet", {})
        history_points = [
            {"date": item["display_date"], "value": item["value"]}
            for item in ranipet_chem.get("history", [])
        ]
        return _normalized_response(config, chem_payload.get("records", []), {
            "source": chem_payload.get("source"),
            "total": chem_payload.get("total_records", 0),
            "count": len(chem_payload.get("records", [])),
            "required_fields": list(config.fields),
            "supported_filters": config.filters,
            "summary": chem_payload.get("summary"),
            "analytics_data": chem_payload,
            "metric": {
                "name": "Industrial Solvents & Toxins (KL)",
                "unit": config.unit,
                "current_value": ranipet_chem.get("current_value", 28.6),
                "average_10_days": ranipet_chem.get("average_10_days", 25.7),
                "high_10_days": ranipet_chem.get("high_10_days", 29.2),
                "low_10_days": ranipet_chem.get("low_10_days", 12.0),
                "percentage_change": ranipet_chem.get("percentage_change", 0.0),
                "trend": ranipet_chem.get("trend", "STABLE"),
                "periods_available": len(history_points),
                "history": history_points,
            },
        })

    if config.component == "Construction materials like concrete, cement, and steel":
        con_payload = get_construction_data()
        primary_info = con_payload.get("primary", {})
        vellore_con = primary_info.get("districts", {}).get("Vellore", {})
        history_points = [
            {"date": item["display_date"], "value": item["value"]}
            for item in vellore_con.get("history", [])
        ]
        return _normalized_response(config, con_payload.get("records", []), {
            "source": con_payload.get("source"),
            "total": con_payload.get("total_records", 0),
            "count": len(con_payload.get("records", [])),
            "required_fields": list(config.fields),
            "supported_filters": config.filters,
            "summary": con_payload.get("summary"),
            "analytics_data": con_payload,
            "metric": {
                "name": "C&D Debris Generation & Aggregates (Tons)",
                "unit": config.unit,
                "current_value": vellore_con.get("current_value", 145.0),
                "average_10_days": vellore_con.get("average_10_days", 130.4),
                "high_10_days": vellore_con.get("high_10_days", 148.0),
                "low_10_days": vellore_con.get("low_10_days", 60.0),
                "percentage_change": vellore_con.get("percentage_change", 0.0),
                "trend": vellore_con.get("trend", "STABLE"),
                "periods_available": len(history_points),
                "history": history_points,
            },
        })

    if config.component == "Public procurement items and green government contracts":
        proc_payload = get_procurement_data()
        primary_info = proc_payload.get("primary", {})
        vellore_proc = primary_info.get("districts", {}).get("Vellore", {})
        history_points = [
            {"date": item["display_date"], "value": item["value"]}
            for item in vellore_proc.get("history", [])
        ]
        return _normalized_response(config, proc_payload.get("records", []), {
            "source": proc_payload.get("source"),
            "total": proc_payload.get("total_records", 0),
            "count": len(proc_payload.get("records", [])),
            "required_fields": list(config.fields),
            "supported_filters": config.filters,
            "summary": proc_payload.get("summary"),
            "analytics_data": proc_payload,
            "metric": {
                "name": "Public Procurement & Green Contracts (₹ Cr)",
                "unit": config.unit,
                "current_value": vellore_proc.get("current_value", 2.45),
                "average_10_days": vellore_proc.get("average_10_days", 1.99),
                "high_10_days": vellore_proc.get("high_10_days", 2.50),
                "low_10_days": vellore_proc.get("low_10_days", 0.0),
                "percentage_change": vellore_proc.get("percentage_change", 0.0),
                "trend": vellore_proc.get("trend", "STABLE"),
                "periods_available": len(history_points),
                "history": history_points,
            },
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
