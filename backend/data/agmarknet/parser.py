from typing import Dict, Any, Optional

def parse_price(price_val: Any) -> float:
    try:
        if price_val is None or str(price_val).strip() == "" or str(price_val).upper() == "NA":
            return 0.0
        return float(price_val)
    except (ValueError, TypeError):
        return 0.0

def normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes a single record from data.gov.in API.
    Converts prices from Rs/Quintal to Rs/Kg.
    """
    # The new API returns TitleCase keys: Arrival_Date, Commodity, District, Market, Max_Price, Min_Price, Modal_Price, State, Variety
    min_price_quintal = parse_price(record.get("Min_Price", record.get("min_price", 0)))
    max_price_quintal = parse_price(record.get("Max_Price", record.get("max_price", 0)))
    modal_price_quintal = parse_price(record.get("Modal_Price", record.get("modal_price", 0)))

    return {
        "commodity": record.get("Commodity", record.get("commodity", "")).lower(),
        "variety": record.get("Variety", record.get("variety", "")),
        "state": record.get("State", record.get("state", "")),
        "district": record.get("District", record.get("district", "")),
        "market": record.get("Market", record.get("market", "")).strip(),
        "arrival_date": record.get("Arrival_Date", record.get("arrival_date", "")),
        "min_price_per_kg": min_price_quintal / 100.0 if min_price_quintal > 0 else 0.0,
        "max_price_per_kg": max_price_quintal / 100.0 if max_price_quintal > 0 else 0.0,
        "modal_price_per_kg": modal_price_quintal / 100.0 if modal_price_quintal > 0 else 0.0,
        "source": "data.gov.in/agmarknet"
    }
