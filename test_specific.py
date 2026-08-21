import asyncio
from backend.data.agmarknet.client import fetch_market_data
from datetime import datetime

async def test_specific():
    # Use today's date in dd/mm/yyyy format (or test without it if it fails)
    today = datetime.now().strftime("%d/%m/%Y")
    print(f"Testing for date: {today}")
    
    data = await fetch_market_data(
        commodity="Tomato",
        state="Tamil Nadu",
        district="Vellore",
        arrival_date=today,
        limit=5
    )
    import json
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    asyncio.run(test_specific())
