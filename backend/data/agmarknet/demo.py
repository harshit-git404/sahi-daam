import asyncio
import httpx
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv(Path(__file__).resolve().parents[3] / ".env")
API_KEY = os.getenv("DATA_GOV_API_KEY", "").strip()
BASE_URL = "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"

async def test_endpoint(name, params):
    print(f"\nSTEP: {name}")
    print(f"URL Params: {json.dumps({k: v for k, v in params.items() if k != 'api-key'})}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }
    async with httpx.AsyncClient(timeout=30.0, verify=False, headers=headers) as client:
        try:
            resp = await client.get(BASE_URL, params=params)
            print(f"Status: {resp.status_code}")
            resp.raise_for_status()
            data = resp.json()
            records = data.get("records", [])
            print(f"Records returned: {len(records)} (Total in DB: {data.get('total', 0)})")
            if records:
                print("Sample record Market:")
                markets = set(r.get('Market', '') for r in records[:50])
                print(f"  {markets}")
                return records
        except Exception as e:
            print(f"Error: {repr(e)}")
            return []

async def main():
    print("========================================")
    print("AGMARKNET API DIAGNOSTIC")
    print("========================================")
    
    if not API_KEY:
        print("ERROR: DATA_GOV_API_KEY is not set.")
        return

    base_params = {"api-key": API_KEY, "format": "json", "offset": 0, "limit": 50}

    # Test A
    await test_endpoint("No filters", base_params)

    # Test B
    params_b = {**base_params, "filters[Commodity]": "Tomato"}
    await test_endpoint("Commodity = Tomato", params_b)

    # Test C
    params_c = {**params_b, "filters[State]": "Tamil Nadu"}
    await test_endpoint("State = Tamil Nadu, Commodity = Tomato", params_c)

    # Test D
    params_d = {**params_c, "filters[District]": "Vellore"}
    records_d = await test_endpoint("District = Vellore", params_d)

    print("\n========================================")
    print("RESULTS FOR VELLORE (First 3 records)")
    print("========================================")
    if records_d:
        # Print the first 3 records nicely formatted
        print(json.dumps(records_d[:3], indent=2))
        if len(records_d) > 3:
            print(f"... and {len(records_d) - 3} more records.")
    else:
        print("No records found for Vellore.")

if __name__ == "__main__":
    asyncio.run(main())
