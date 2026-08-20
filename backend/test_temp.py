import sys
import os
import asyncio
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.agmarknet.client import fetch_market_data

async def main():
    load_dotenv()
    # Fetch all commodities for Vellore
    res = await fetch_market_data(commodity="", state="Tamil Nadu", district="Vellore", limit=100)
    
    if "records" in res:
        commodities = set([r.get("Commodity") for r in res["records"]])
        print(f"Found {len(res['records'])} records.")
        print(f"Commodities available: {commodities}")
    else:
        print(res)

if __name__ == "__main__":
    asyncio.run(main())
