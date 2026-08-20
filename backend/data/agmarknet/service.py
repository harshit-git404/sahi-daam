import os
from typing import Dict, Any, Optional, List
from datetime import datetime

from .client import fetch_market_data
from .parser import normalize_record

DEFAULT_STATE = os.getenv("DEFAULT_STATE", "Tamil Nadu")

async def get_mandi_prices(
    commodity: str,
    state: Optional[str] = None,
    district: Optional[str] = None,
    market: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch, normalize, filter and return the latest mandi price data.
    """
    # Only default state if neither state nor district is provided, to avoid overly broad queries
    # But if state is explicitly provided, we don't need a default.
    actual_state = state if state else (DEFAULT_STATE if not district else None)
    
    raw_data = await fetch_market_data(
        commodity=commodity,
        state=actual_state,
        district=district,
        limit=100
    )
    
    if "error" in raw_data:
        return {
            "commodity": commodity.lower(),
            "source": "data.gov.in/agmarknet",
            "error": raw_data["error"],
            "details": raw_data.get("details", ""),
            "records": []
        }
    
    records = raw_data.get("records", [])
    normalized_records = [normalize_record(r) for r in records]
    
    # Filter by market if provided; fall back to district-level if market yields no records
    if market:
        market_lower = market.lower()
        market_filtered = [
            r for r in normalized_records
            if r["market"] and market_lower in r["market"].lower()
        ]
        if market_filtered:
            normalized_records = market_filtered
        # else: keep district-level records (wider net for 10-day history)

    if not normalized_records:
        return {
            "commodity": commodity.lower(),
            "source": "data.gov.in/agmarknet",
            "records": []
        }
        
    # Sort records by date to find the latest
    # Arrival_Date format is typically DD/MM/YYYY
    def parse_date(date_str: str) -> datetime:
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            # Fallback for unexpected date formats
            return datetime.min

    # Sort descending by date
    normalized_records.sort(key=lambda r: parse_date(r["arrival_date"]), reverse=True)
    
    # After sorting, we may just return all sorted records or group them.
    # The requirement is just to return the records so the router can pick the latest.
    return {
        "commodity": commodity.lower(),
        "source": "data.gov.in/agmarknet",
        "records": normalized_records
    }
