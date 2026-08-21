import asyncio
from backend.data.agmarknet.service import get_mandi_prices

async def main():
    result = await get_mandi_prices(commodity="Tomato", state="Tamil Nadu", district="Vellore")
    import json
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
