import os
from pathlib import Path
import httpx
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

API_KEY = os.getenv("DATA_GOV_API_KEY")
RESOURCE_ID = os.getenv("AGMARKNET_RESOURCE_ID", "35985678-0d79-46b4-9ed6-6f13308a1d24").strip()
BASE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

async def fetch_market_data(
    commodity: str,
    state: Optional[str] = None,
    district: Optional[str] = None,
    arrival_date: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Fetch market data from data.gov.in API.
    """
    if not API_KEY:
        raise ValueError("DATA_GOV_API_KEY environment variable is not set")

    params = {
        "api-key": API_KEY.strip() if API_KEY else "",
        "format": "json",
        "limit": limit,
        "filters[Commodity]": commodity
    }
    
    if state:
        params["filters[State]"] = state
    if district:
        params["filters[District]"] = district
    if arrival_date:
        params["filters[Arrival_Date]"] = arrival_date

    # data.gov.in actively drops/blocks default Python User-Agents, causing ReadTimeouts
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }

    # Increase timeout significantly as data.gov.in can be slow
    async with httpx.AsyncClient(timeout=60.0, headers=headers) as client:
        try:
            print(f"[AGMARKNET] Fetching data for {commodity} in {district}, {state}...")
            debug_url = BASE_URL + "?filters[Commodity]=" + commodity
            safe_params = {key: value for key, value in params.items() if key != "api-key"}
            print(f"[AGMARKNET] URL: {debug_url} (params: {safe_params})")
            
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "records" not in data:
                return {"error": "INVALID_RESPONSE_FORMAT", "details": str(data)}
                
            print(f"[AGMARKNET] Received {len(data.get('records', []))} records.")
            return data
        except httpx.HTTPStatusError as e:
            print(f"[AGMARKNET] HTTP error occurred: {repr(e)}")
            return {"error": "HTTP_ERROR", "details": repr(e), "status_code": e.response.status_code}
        except httpx.RequestError as e:
            print(f"[AGMARKNET] Request error occurred: {repr(e)}")
            return {"error": "NETWORK_ERROR", "details": repr(e)}
        except Exception as e:
            print(f"[AGMARKNET] An unexpected error occurred: {repr(e)}")
            return {"error": "UNKNOWN_ERROR", "details": repr(e)}
