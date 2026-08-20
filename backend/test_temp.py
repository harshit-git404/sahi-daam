import sys
import os
import asyncio
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.agmarknet.client import fetch_market_data

async def main():
    load_dotenv()
    res = await fetch_market_data("Tomato", state="Tamil Nadu", limit=5)
    print(res)

if __name__ == "__main__":
    asyncio.run(main())
