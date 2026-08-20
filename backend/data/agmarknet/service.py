import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, date

from .client import fetch_market_data
from .parser import normalize_record

DEFAULT_STATE = os.getenv("DEFAULT_STATE", "Tamil Nadu")
CACHE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _get_cache_path() -> str:
    today_str = date.today().isoformat()
    return os.path.join(CACHE_DIR, f"prices_{today_str}.json")

def _load_cache() -> Dict[str, Any]:
    cache_path = _get_cache_path()
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_cache(data: Dict[str, Any]):
    cache_path = _get_cache_path()
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

async def refresh_all_mandi_prices() -> Dict[str, Any]:
    """Force fetch live data for all commodities in the default region and update the daily cache."""
    # We load existing cache to not overwrite anything else if we want, but usually we just overwrite
    cache = _load_cache()
    
    district = os.getenv("DEFAULT_DISTRICT", "Vellore")
    
    try:
        # Fetch 500 records for the district to get as many commodities as possible
        raw_data = await fetch_market_data(
            commodity="", # Empty string means fetch all
            state=DEFAULT_STATE,
            district=district,
            limit=500
        )
        
        if "error" not in raw_data:
            records = raw_data.get("records", [])
            normalized_records = [normalize_record(r) for r in records]
            
            # Group records by commodity
            grouped_records = {}
            for r in normalized_records:
                comm = r.get("commodity", "").lower()
                if not comm:
                    continue
                if comm not in grouped_records:
                    grouped_records[comm] = []
                grouped_records[comm].append(r)
                
            def parse_date(date_str: str) -> datetime:
                try:
                    return datetime.strptime(date_str, "%d/%m/%Y")
                except ValueError:
                    return datetime.min
            
            for comm, comm_records in grouped_records.items():
                comm_records.sort(key=lambda r: parse_date(r["arrival_date"]), reverse=True)
                
                cache[comm] = {
                    "commodity": comm,
                    "source": "data.gov.in/agmarknet",
                    "records": comm_records,
                    "updated_at": datetime.now().isoformat()
                }
        else:
            raise Exception(f"API Error: {raw_data.get('details', raw_data.get('error'))}")
            
    except Exception as e:
        print(f"Error fetching bulk data for {district}: {e}. Falling back to mock data.")
        # HACKATHON FALLBACK: If the API is rate-limiting us, inject realistic mock data so the demo doesn't crash!
        fallback_commodities = {
            "tomato": 22.5, "onion": 35.0, "potato": 18.0, 
            "banana": 40.0, "coconut": 25.0, "coriander": 12.0, "ginger": 150.0
        }
        today_str = date.today().strftime("%d/%m/%Y")
        for comm, price in fallback_commodities.items():
            cache[comm] = {
                "commodity": comm,
                "source": "data.gov.in/agmarknet (Mock Fallback)",
                "records": [{
                    "commodity": comm.capitalize(),
                    "state": DEFAULT_STATE,
                    "district": district,
                    "market": "Katpadi(Uzhavar Santhai)",
                    "arrival_date": today_str,
                    "min_price": price * 90, # mock wholesale per quintal
                    "max_price": price * 110,
                    "modal_price": price * 100,
                    "modal_price_per_kg": price
                }],
                "updated_at": datetime.now().isoformat()
            }
        
    _save_cache(cache)
    return cache

async def get_mandi_prices(
    commodity: str,
    state: Optional[str] = None,
    district: Optional[str] = None,
    market: Optional[str] = None,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Fetch, normalize, filter and return the latest mandi price data.
    Uses daily JSON cache to prevent excessive live calls.
    """
    comm_lower = commodity.lower()
    
    if not force_refresh:
        cache = _load_cache()
        if comm_lower in cache:
            cached_data = cache[comm_lower]
            # We can still apply market filtering dynamically
            records = cached_data.get("records", [])
            if market:
                market_lower = market.lower()
                records = [r for r in records if r["market"] and market_lower in r["market"].lower()]
                
            return {
                "commodity": comm_lower,
                "source": "data.gov.in/agmarknet (cached)",
                "records": records
            }

    # If not in cache or forced refresh, fetch live
    actual_state = state if state else (DEFAULT_STATE if not district else None)
    
    raw_data = await fetch_market_data(
        commodity=commodity.capitalize(),
        state=actual_state,
        district=district,
        limit=100
    )
    
    if "error" in raw_data:
        return {
            "commodity": comm_lower,
            "source": "data.gov.in/agmarknet",
            "error": raw_data["error"],
            "details": raw_data.get("details", ""),
            "records": []
        }
    
    records = raw_data.get("records", [])
    normalized_records = [normalize_record(r) for r in records]
    
    def parse_date(date_str: str) -> datetime:
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            return datetime.min

    normalized_records.sort(key=lambda r: parse_date(r["arrival_date"]), reverse=True)
    
    # Save to cache so next time it's fast
    cache = _load_cache()
    cache[comm_lower] = {
        "commodity": comm_lower,
        "source": "data.gov.in/agmarknet",
        "records": normalized_records,
        "updated_at": datetime.now().isoformat()
    }
    _save_cache(cache)
    
    # Filter by market if provided
    if market:
        market_lower = market.lower()
        normalized_records = [
            r for r in normalized_records 
            if r["market"] and market_lower in r["market"].lower()
        ]
        
    return {
        "commodity": comm_lower,
        "source": "data.gov.in/agmarknet",
        "records": normalized_records
    }

async def resolve_wholesale_price(
    commodity: str,
    state: str = DEFAULT_STATE,
    district: str = "Vellore",
    target_market: str = "Katpadi"
) -> Dict[str, Any]:
    today_str = date.today().strftime("%d/%m/%Y")
    today_iso = date.today().strftime("%Y-%m-%d")

    # Fetch live/cached data for the whole state (avoids extra live calls if we already cached Tamil Nadu, 
    # but currently get_mandi_prices fetches state if district is missing).
    # To keep it efficient, let's first check the local cache or fetch for the whole state.
    state_data = await get_mandi_prices(commodity, state=state, district=None)
    records = state_data.get("records", [])
    
    # Filter out mock records from the 'live' search space
    real_records = [r for r in records if "Mock Fallback" not in r.get("source", state_data.get("source", ""))]
    
    def format_obs(r):
        try:
            d, m, y = r["arrival_date"].split("/")
            return {"date": f"{y}-{m}-{d}", "price": r["modal_price_per_kg"]}
        except:
            return {"date": today_iso, "price": r["modal_price_per_kg"]}

    market_lower = target_market.lower()
    local_history = [format_obs(r) for r in real_records if market_lower in r["market"].lower()][:30]
    regional_history = [format_obs(r) for r in real_records][:30]
    mock_history = [format_obs(r) for r in records if "Mock Fallback" in r.get("source", state_data.get("source", ""))][:30]

    # Tier A: Today's price for exact market
    tier_a = [r for r in real_records if market_lower in r["market"].lower() and r["arrival_date"] == today_str]
    if tier_a:
        return {
            "wholesale_price": tier_a[0]["modal_price_per_kg"],
            "data_date": today_iso,
            "data_confidence": "High",
            "price_source": "live_local",
            "used_markets": [tier_a[0]["market"]],
            "historical_observations": local_history
        }
        
    # Tier B: Today's price averaged across other markets in the state
    tier_b = [r for r in real_records if r["arrival_date"] == today_str]
    if tier_b:
        avg_price = sum(r["modal_price_per_kg"] for r in tier_b) / len(tier_b)
        used_markets = list(set(r["market"] for r in tier_b))
        return {
            "wholesale_price": round(avg_price, 2),
            "data_date": today_iso,
            "data_confidence": "Medium",
            "price_source": "live_regional_average",
            "used_markets": used_markets,
            "historical_observations": regional_history
        }
        
    # Tier C: Most recent previous day's price for exact market
    tier_c = [r for r in real_records if market_lower in r["market"].lower()]
    if tier_c:
        # already sorted by date descending in get_mandi_prices
        latest = tier_c[0]
        # format date
        d, m, y = latest["arrival_date"].split("/")
        return {
            "wholesale_price": latest["modal_price_per_kg"],
            "data_date": f"{y}-{m}-{d}",
            "data_confidence": "Low",
            "price_source": "cached_previous_day",
            "used_markets": [latest["market"]],
            "historical_observations": local_history
        }
        
    # Tier D: Mock Fallback
    mock_records = [r for r in records if "Mock Fallback" in r.get("source", state_data.get("source", ""))]
    if mock_records:
        latest = mock_records[0]
        d, m, y = latest["arrival_date"].split("/")
        return {
            "wholesale_price": latest["modal_price_per_kg"],
            "data_date": f"{y}-{m}-{d}",
            "data_confidence": "Estimated",
            "price_source": "fallback_mock",
            "used_markets": [latest["market"]],
            "historical_observations": mock_history
        }
        
    # Absolute Fallback if even mock fails
    return {
        "wholesale_price": 22.0,
        "data_date": today_iso,
        "data_confidence": "Estimated",
        "price_source": "fallback_mock",
        "used_markets": ["None"],
        "historical_observations": []
    }
