import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SNAPSHOT_PATH = Path(__file__).resolve().parent / "quickcommerce_snapshot.json"
SUPPORTED_COMMODITIES = {"tomato", "potato", "onion", "carrot", "cucumber", "brinjal", "cauliflower", "cabbage", "banana", "papaya"}


def _load_snapshot() -> dict[str, Any]:
    try:
        return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def get_retail_prices(commodity: str, location: str | None = None) -> dict[str, Any]:
    commodity_id = commodity.strip().lower().replace(" ", "_")
    if commodity_id not in SUPPORTED_COMMODITIES:
        return {"status": "UNAVAILABLE", "commodity": commodity_id, "location": location, "products": [], "message": "Retail comparison unavailable for this item."}

    products: list[dict[str, Any]] = []
    for platform, dated_values in _load_snapshot().get(commodity_id, {}).items():
        for collected_date, value in dated_values.items():
            try:
                price = float(value["price"])
                unit = str(value.get("unit", "kg"))
            except (KeyError, TypeError, ValueError):
                continue
            quantity_kg = 1.0 if unit.lower() in {"kg", "kilogram"} else None
            if quantity_kg is None:
                continue
            products.append({
                "platform": platform.lower(),
                "commodity": commodity_id,
                "product_name": commodity_id.replace("_", " ").title(),
                "variant": "regular",
                "quantity": unit,
                "quantity_kg": quantity_kg,
                "price": price,
                "mrp": None,
                "price_per_kg": round(price / quantity_kg, 2),
                "location": location,
                "collected_at": collected_date,
            })

    if not products:
        return {"status": "UNAVAILABLE", "commodity": commodity_id, "location": location, "products": [], "message": "No current cached retailer prices are available."}
    return {
        "status": "AVAILABLE",
        "commodity": commodity_id,
        "location": location,
        "products": products,
        "collected_at": max(product["collected_at"] for product in products),
        "source": "cached retail snapshot; refresh via authorized provider",
    }
