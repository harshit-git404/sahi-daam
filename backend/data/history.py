from collections import defaultdict
from datetime import datetime
from typing import Any, Callable


def normalize_date(value: Any) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def analyze_distinct_history(
    records: list[dict[str, Any]],
    date_field: str,
    value_field: str,
    *,
    limit: int = 10,
    aggregate: Callable[[list[float]], float] = lambda values: sum(values) / len(values),
    stable_threshold_pct: float = 1.0,
) -> dict[str, Any]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for record in records:
        date = normalize_date(record.get(date_field))
        value = record.get(value_field)
        if date is None or value is None:
            continue
        try:
            grouped[date].append(float(value))
        except (TypeError, ValueError):
            continue

    dates = sorted(grouped, reverse=True)[:limit]
    history = [{"date": date, "value": round(aggregate(grouped[date]), 2)} for date in dates]
    values = [entry["value"] for entry in history]
    if not values:
        return {
            "current_value": None,
            "average_10_days": None,
            "high_10_days": None,
            "low_10_days": None,
            "percentage_change": None,
            "trend": "UNAVAILABLE",
            "history": [],
            "periods_available": 0,
        }

    current = values[0]
    average = sum(values) / len(values)
    change = ((current - average) / average) * 100 if average else None
    if change is None:
        trend = "UNAVAILABLE"
    elif abs(change) < stable_threshold_pct:
        trend = "STABLE"
    elif change > 0:
        trend = "UP"
    else:
        trend = "DOWN"
    return {
        "current_value": round(current, 2),
        "average_10_days": round(average, 2),
        "high_10_days": round(max(values), 2),
        "low_10_days": round(min(values), 2),
        "percentage_change": round(change, 2) if change is not None else None,
        "trend": trend,
        "history": history,
        "periods_available": len(history),
    }
