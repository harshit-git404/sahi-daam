import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from .commodity_rules import SUPPORTED_COMMODITY_IDS
except ImportError:
    from commodity_rules import SUPPORTED_COMMODITY_IDS

logger = logging.getLogger(__name__)
SNAPSHOT_PATH = Path(__file__).resolve().parent / "quickcommerce_snapshot.json"


def _load_snapshot() -> dict[str, Any]:
    try:
        return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not load retail snapshot: %s", exc)
        return {}


def _normalize_commodity_id(commodity: str) -> str:
    """Normalize a commodity string to a snapshot key."""
    return commodity.strip().lower().replace(" ", "_").replace("-", "_")


def get_retail_prices(commodity: str, location: str | None = None) -> dict[str, Any]:
    """
    Return normalized retail prices from Blinkit and Zepto for the given commodity.

    Args:
        commodity: The produce name or ID (e.g. 'tomato', 'Tomato', 'bell_pepper').
        location: The user's selected location string (informational; data may be cached
                  from a different location; this is surfaced in the response for transparency).

    Returns:
        A dict with status AVAILABLE | UNAVAILABLE and a list of normalized product records.
    """
    commodity_id = _normalize_commodity_id(commodity)

    if commodity_id not in SUPPORTED_COMMODITY_IDS:
        logger.info("Retail prices not available for commodity: %s", commodity_id)
        return {
            "status": "UNAVAILABLE",
            "commodity": commodity_id,
            "location": location,
            "products": [],
            "message": (
                f"Retail comparison is not available for '{commodity}'. "
                "Supported commodities include tomato, potato, onion, and others."
            ),
        }

    snapshot = _load_snapshot()
    commodity_data = snapshot.get(commodity_id, {})
    if not commodity_data:
        logger.info("No snapshot data found for commodity: %s", commodity_id)
        return {
            "status": "UNAVAILABLE",
            "commodity": commodity_id,
            "location": location,
            "products": [],
            "message": "No current retail data is available for this commodity. Run the collector to refresh.",
        }

    products: list[dict[str, Any]] = []
    latest_collected_at = ""

    for platform, entries in commodity_data.items():
        platform_lower = platform.strip().lower()
        # entries is a list of normalized product records
        if isinstance(entries, list):
            records = entries
        elif isinstance(entries, dict):
            # Legacy format: {date: {price, unit}} — try to convert
            records = []
            for collected_date, value in entries.items():
                try:
                    price = float(value["price"])
                    unit = str(value.get("unit", "kg"))
                    quantity_kg = 1.0 if unit.lower() in {"kg", "kilogram"} else None
                    if quantity_kg is None:
                        continue
                    records.append({
                        "product_name": commodity_id.replace("_", " ").title(),
                        "variant": "regular",
                        "quantity": unit,
                        "quantity_kg": quantity_kg,
                        "price": price,
                        "mrp": None,
                        "price_per_kg": round(price / quantity_kg, 2),
                        "collected_at": collected_date,
                    })
                except (KeyError, TypeError, ValueError) as exc:
                    logger.warning("Skipping malformed legacy snapshot entry: %s", exc)
        else:
            logger.warning("Unknown snapshot format for %s/%s", commodity_id, platform)
            continue

        for record in records:
            try:
                qty_kg = record.get("quantity_kg")
                price = record.get("price")
                if qty_kg is None or price is None:
                    continue
                qty_kg = float(qty_kg)
                price = float(price)
                if qty_kg <= 0:
                    continue
                price_per_kg = record.get("price_per_kg") or round(price / qty_kg, 2)
                collected_at = record.get("collected_at", "")
                if collected_at > latest_collected_at:
                    latest_collected_at = collected_at

                # Location note: data may have been collected from a fixed location
                data_location = record.get("location") or location
                location_note = None
                if location and data_location and data_location.lower() != (location or "").lower():
                    location_note = (
                        f"Prices collected from {data_location}; "
                        "actual prices may vary in your location."
                    )

                products.append({
                    "platform": platform_lower,
                    "commodity": commodity_id,
                    "product_name": record.get("product_name", commodity_id.replace("_", " ").title()),
                    "variant": record.get("variant", "regular"),
                    "quantity": record.get("quantity", "1 kg"),
                    "quantity_kg": qty_kg,
                    "price": price,
                    "mrp": record.get("mrp"),
                    "price_per_kg": round(price_per_kg, 2),
                    "location": data_location,
                    "location_note": location_note,
                    "collected_at": collected_at,
                })
            except (TypeError, ValueError) as exc:
                logger.warning("Skipping malformed retail record for %s/%s: %s", commodity_id, platform, exc)

    if not products:
        return {
            "status": "UNAVAILABLE",
            "commodity": commodity_id,
            "location": location,
            "products": [],
            "message": "No valid retail entries found in the current snapshot. Run the collector to refresh.",
        }

    # Sort by price_per_kg ascending so the best deal comes first
    products.sort(key=lambda p: p["price_per_kg"])

    return {
        "status": "AVAILABLE",
        "commodity": commodity_id,
        "location": location,
        "products": products,
        "best_price_per_kg": products[0]["price_per_kg"],
        "best_platform": products[0]["platform"],
        "collected_at": latest_collected_at or datetime.now().isoformat(),
        "source": "cached retail snapshot — refresh via offline collector",
    }
