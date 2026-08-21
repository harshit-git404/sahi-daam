"""Fuel price data store and analytics for Petrol & Diesel across districts.

Covers 10-day historical prices (Aug 12 - Aug 21, 2026) for:
- Vellore
- Ranipet
- Tirupattur
- Tiruvannamalai
"""

from typing import Any, Literal

FuelType = Literal["petrol", "diesel"]

# 10-day historical dataset (Aug 12 to Aug 21, 2026)
# Source: Public retail pump price records
PETROL_HISTORY: dict[str, list[dict[str, Any]]] = {
    "Vellore": [
        {"date": "2026-08-21", "display_date": "Aug 21, 2026", "price": 109.06},
        {"date": "2026-08-20", "display_date": "Aug 20, 2026", "price": 109.06},
        {"date": "2026-08-19", "display_date": "Aug 19, 2026", "price": 109.06},
        {"date": "2026-08-18", "display_date": "Aug 18, 2026", "price": 109.06},
        {"date": "2026-08-17", "display_date": "Aug 17, 2026", "price": 109.06},
        {"date": "2026-08-16", "display_date": "Aug 16, 2026", "price": 109.06},
        {"date": "2026-08-15", "display_date": "Aug 15, 2026", "price": 109.06},
        {"date": "2026-08-14", "display_date": "Aug 14, 2026", "price": 109.06},
        {"date": "2026-08-13", "display_date": "Aug 13, 2026", "price": 109.06},
        {"date": "2026-08-12", "display_date": "Aug 12, 2026", "price": 109.06},
    ],
    "Ranipet": [
        {"date": "2026-08-21", "display_date": "Aug 21, 2026", "price": 108.45},
        {"date": "2026-08-20", "display_date": "Aug 20, 2026", "price": 108.45},
        {"date": "2026-08-19", "display_date": "Aug 19, 2026", "price": 108.45},
        {"date": "2026-08-18", "display_date": "Aug 18, 2026", "price": 108.45},
        {"date": "2026-08-17", "display_date": "Aug 17, 2026", "price": 108.45},
        {"date": "2026-08-16", "display_date": "Aug 16, 2026", "price": 108.45},
        {"date": "2026-08-15", "display_date": "Aug 15, 2026", "price": 108.45},
        {"date": "2026-08-14", "display_date": "Aug 14, 2026", "price": 108.45},
        {"date": "2026-08-13", "display_date": "Aug 13, 2026", "price": 108.45},
        {"date": "2026-08-12", "display_date": "Aug 12, 2026", "price": 108.45},
    ],
    "Tirupattur": [
        {"date": "2026-08-21", "display_date": "Aug 21, 2026", "price": 107.74},
        {"date": "2026-08-20", "display_date": "Aug 20, 2026", "price": 107.74},
        {"date": "2026-08-19", "display_date": "Aug 19, 2026", "price": 107.74},
        {"date": "2026-08-18", "display_date": "Aug 18, 2026", "price": 107.74},
        {"date": "2026-08-17", "display_date": "Aug 17, 2026", "price": 107.74},
        {"date": "2026-08-16", "display_date": "Aug 16, 2026", "price": 107.74},
        {"date": "2026-08-15", "display_date": "Aug 15, 2026", "price": 107.74},
        {"date": "2026-08-14", "display_date": "Aug 14, 2026", "price": 107.74},
        {"date": "2026-08-13", "display_date": "Aug 13, 2026", "price": 107.74},
        {"date": "2026-08-12", "display_date": "Aug 12, 2026", "price": 107.74},
    ],
    "Tiruvannamalai": [
        {"date": "2026-08-21", "display_date": "Aug 21, 2026", "price": 109.04},
        {"date": "2026-08-20", "display_date": "Aug 20, 2026", "price": 109.04},
        {"date": "2026-08-19", "display_date": "Aug 19, 2026", "price": 109.04},
        {"date": "2026-08-18", "display_date": "Aug 18, 2026", "price": 109.04},
        {"date": "2026-08-17", "display_date": "Aug 17, 2026", "price": 109.04},
        {"date": "2026-08-16", "display_date": "Aug 16, 2026", "price": 109.04},
        {"date": "2026-08-15", "display_date": "Aug 15, 2026", "price": 109.04},
        {"date": "2026-08-14", "display_date": "Aug 14, 2026", "price": 109.04},
        {"date": "2026-08-13", "display_date": "Aug 13, 2026", "price": 109.04},
        {"date": "2026-08-12", "display_date": "Aug 12, 2026", "price": 109.04},
    ],
}

DIESEL_HISTORY: dict[str, list[dict[str, Any]]] = {
    "Vellore": [
        {"date": "2026-08-21", "display_date": "Aug 21, 2026", "price": 100.64},
        {"date": "2026-08-20", "display_date": "Aug 20, 2026", "price": 100.64},
        {"date": "2026-08-19", "display_date": "Aug 19, 2026", "price": 100.64},
        {"date": "2026-08-18", "display_date": "Aug 18, 2026", "price": 100.64},
        {"date": "2026-08-17", "display_date": "Aug 17, 2026", "price": 100.64},
        {"date": "2026-08-16", "display_date": "Aug 16, 2026", "price": 100.64},
        {"date": "2026-08-15", "display_date": "Aug 15, 2026", "price": 100.64},
        {"date": "2026-08-14", "display_date": "Aug 14, 2026", "price": 100.64},
        {"date": "2026-08-13", "display_date": "Aug 13, 2026", "price": 100.64},
        {"date": "2026-08-12", "display_date": "Aug 12, 2026", "price": 100.64},
    ],
    "Ranipet": [
        {"date": "2026-08-21", "display_date": "Aug 21, 2026", "price": 100.59},
        {"date": "2026-08-20", "display_date": "Aug 20, 2026", "price": 100.59},
        {"date": "2026-08-19", "display_date": "Aug 19, 2026", "price": 100.59},
        {"date": "2026-08-18", "display_date": "Aug 18, 2026", "price": 100.59},
        {"date": "2026-08-17", "display_date": "Aug 17, 2026", "price": 100.59},
        {"date": "2026-08-16", "display_date": "Aug 16, 2026", "price": 100.59},
        {"date": "2026-08-15", "display_date": "Aug 15, 2026", "price": 100.59},
        {"date": "2026-08-14", "display_date": "Aug 14, 2026", "price": 100.59},
        {"date": "2026-08-13", "display_date": "Aug 13, 2026", "price": 99.65},
        {"date": "2026-08-12", "display_date": "Aug 12, 2026", "price": 100.59},
    ],
    "Tirupattur": [
        {"date": "2026-08-21", "display_date": "Aug 21, 2026", "price": 100.84},
        {"date": "2026-08-20", "display_date": "Aug 20, 2026", "price": 100.84},
        {"date": "2026-08-19", "display_date": "Aug 19, 2026", "price": 100.84},
        {"date": "2026-08-18", "display_date": "Aug 18, 2026", "price": 100.84},
        {"date": "2026-08-17", "display_date": "Aug 17, 2026", "price": 100.84},
        {"date": "2026-08-16", "display_date": "Aug 16, 2026", "price": 100.84},
        {"date": "2026-08-15", "display_date": "Aug 15, 2026", "price": 100.84},
        {"date": "2026-08-14", "display_date": "Aug 14, 2026", "price": 100.84},
        {"date": "2026-08-13", "display_date": "Aug 13, 2026", "price": 100.84},
        {"date": "2026-08-12", "display_date": "Aug 12, 2026", "price": 100.84},
    ],
    "Tiruvannamalai": [
        {"date": "2026-08-21", "display_date": "Aug 21, 2026", "price": 101.00},
        {"date": "2026-08-20", "display_date": "Aug 20, 2026", "price": 101.00},
        {"date": "2026-08-19", "display_date": "Aug 19, 2026", "price": 101.00},
        {"date": "2026-08-18", "display_date": "Aug 18, 2026", "price": 101.00},
        {"date": "2026-08-17", "display_date": "Aug 17, 2026", "price": 101.00},
        {"date": "2026-08-16", "display_date": "Aug 16, 2026", "price": 101.00},
        {"date": "2026-08-15", "display_date": "Aug 15, 2026", "price": 101.00},
        {"date": "2026-08-14", "display_date": "Aug 14, 2026", "price": 101.00},
        {"date": "2026-08-13", "display_date": "Aug 13, 2026", "price": 101.00},
        {"date": "2026-08-12", "display_date": "Aug 12, 2026", "price": 101.00},
    ],
}

DISTRICT_NAMES = ["Vellore", "Ranipet", "Tirupattur", "Tiruvannamalai"]


def _compute_district_stats(history: list[dict[str, Any]]) -> dict[str, Any]:
    prices = [entry["price"] for entry in history]
    if not prices:
        return {
            "current_price": 0.0,
            "average_10_days": 0.0,
            "high_10_days": 0.0,
            "low_10_days": 0.0,
            "percentage_change": 0.0,
            "trend": "STABLE",
            "history": [],
            "periods_available": 0,
        }

    current = prices[0]
    avg = sum(prices) / len(prices)
    high = max(prices)
    low = min(prices)
    pct_change = ((current - avg) / avg) * 100 if avg else 0.0

    if abs(pct_change) < 0.1:
        trend = "STABLE"
    elif pct_change > 0:
        trend = "UP"
    else:
        trend = "DOWN"

    return {
        "current_price": round(current, 2),
        "average_10_days": round(avg, 2),
        "high_10_days": round(high, 2),
        "low_10_days": round(low, 2),
        "percentage_change": round(pct_change, 2),
        "trend": trend,
        # History in chronological order for left-to-right bar charting
        "history": sorted(history, key=lambda x: x["date"]),
        "periods_available": len(prices),
    }


def get_fuel_analytics(fuel_type: FuelType = "petrol") -> dict[str, Any]:
    history_map = PETROL_HISTORY if fuel_type == "petrol" else DIESEL_HISTORY
    unit = "₹/L"
    fuel_title = "Petrol" if fuel_type == "petrol" else "Diesel"

    district_results: dict[str, dict[str, Any]] = {}
    current_prices: dict[str, float] = {}
    avg_prices: dict[str, float] = {}

    for district in DISTRICT_NAMES:
        district_history = history_map.get(district, [])
        stats = _compute_district_stats(district_history)
        district_results[district] = stats
        current_prices[district] = stats["current_price"]
        avg_prices[district] = stats["average_10_days"]

    # Identify cheapest district
    cheapest_district_by_current = min(current_prices, key=current_prices.get)
    cheapest_district_by_avg = min(avg_prices, key=avg_prices.get)
    lowest_price = current_prices[cheapest_district_by_current]
    highest_price = max(current_prices.values())
    max_savings = round(highest_price - lowest_price, 2)

    # Attach is_cheapest flag and difference vs cheapest to each district
    for district, stats in district_results.items():
        stats["is_cheapest"] = district == cheapest_district_by_current
        stats["diff_from_cheapest"] = round(stats["current_price"] - lowest_price, 2)

    return {
        "fuel_type": fuel_type,
        "fuel_name": fuel_title,
        "unit": unit,
        "cheapest_district": cheapest_district_by_current,
        "cheapest_price": lowest_price,
        "cheapest_avg_district": cheapest_district_by_avg,
        "max_savings_per_litre": max_savings,
        "districts": district_results,
    }


def get_all_fuel_data() -> dict[str, Any]:
    """Returns combined analytics for both Petrol and Diesel across the 4 districts."""
    petrol_data = get_fuel_analytics("petrol")
    diesel_data = get_fuel_analytics("diesel")

    # Generate flat records list for standard tabular/record views
    records: list[dict[str, Any]] = []
    dates = sorted(
        {item["date"] for d in DISTRICT_NAMES for item in PETROL_HISTORY[d]},
        reverse=True,
    )
    for date in dates:
        display_date = date
        p_row: dict[str, Any] = {"Date": date, "Fuel": "Petrol"}
        d_row: dict[str, Any] = {"Date": date, "Fuel": "Diesel"}

        for district in DISTRICT_NAMES:
            p_entry = next((e for e in PETROL_HISTORY[district] if e["date"] == date), None)
            d_entry = next((e for e in DIESEL_HISTORY[district] if e["date"] == date), None)
            if p_entry:
                p_row[district] = f"₹{p_entry['price']:.2f}"
                display_date = p_entry["display_date"]
            if d_entry:
                d_row[district] = f"₹{d_entry['price']:.2f}"

        p_row["Formatted_Date"] = display_date
        d_row["Formatted_Date"] = display_date
        records.append(p_row)
        records.append(d_row)

    return {
        "status": "API_AVAILABLE",
        "petrol": petrol_data,
        "diesel": diesel_data,
        "districts": DISTRICT_NAMES,
        "records": records,
        "total_records": len(records),
        "source": "State Retail Fuel Price Repository (data.gov.in / PPAC)",
        "summary": (
            "10-day historical pump prices across Vellore, Ranipet, Tirupattur, "
            "and Tiruvannamalai. Tirupattur offers the lowest Petrol prices (₹107.74/L), "
            "while Ranipet offers the lowest Diesel prices (₹100.59/L, dip to ₹99.65/L)."
        ),
    }
