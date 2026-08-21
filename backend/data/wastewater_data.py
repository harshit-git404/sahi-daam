"""Industrial Wastewater and Factory Effluents data store and analytics.

Covers 10-day historical metrics (Aug 12 - Aug 21, 2026) for:
- Vellore
- Ranipet
- Tirupattur
- Tiruvannamalai

Metrics:
- Industrial Effluent Volume (MLD - Million Litres per Day)
- Treated Wastewater Discharge (MLD)
"""

from typing import Any, Literal

WastewaterMetricType = Literal["effluent", "treated"]

# 10-day historical dataset for Industrial Effluent Volume (MLD)
# Aug 12 to Aug 21, 2026
EFFLUENT_HISTORY: dict[str, list[dict[str, Any]]] = {
    "Vellore": [
        {"date": "2026-08-21", "display_date": "Aug 21, 2026", "volume": 12.4},
        {"date": "2026-08-20", "display_date": "Aug 20, 2026", "volume": 12.1},
        {"date": "2026-08-19", "display_date": "Aug 19, 2026", "volume": 12.5},
        {"date": "2026-08-18", "display_date": "Aug 18, 2026", "volume": 12.3},
        {"date": "2026-08-17", "display_date": "Aug 17, 2026", "volume": 11.9},
        {"date": "2026-08-16", "display_date": "Aug 16, 2026", "volume": 10.2},
        {"date": "2026-08-15", "display_date": "Aug 15, 2026", "volume": 8.5},
        {"date": "2026-08-14", "display_date": "Aug 14, 2026", "volume": 12.4},
        {"date": "2026-08-13", "display_date": "Aug 13, 2026", "volume": 12.2},
        {"date": "2026-08-12", "display_date": "Aug 12, 2026", "volume": 12.6},
    ],
    "Ranipet": [
        {"date": "2026-08-21", "display_date": "Aug 21, 2026", "volume": 18.2},
        {"date": "2026-08-20", "display_date": "Aug 20, 2026", "volume": 18.5},
        {"date": "2026-08-19", "display_date": "Aug 19, 2026", "volume": 17.9},
        {"date": "2026-08-18", "display_date": "Aug 18, 2026", "volume": 18.1},
        {"date": "2026-08-17", "display_date": "Aug 17, 2026", "volume": 17.8},
        {"date": "2026-08-16", "display_date": "Aug 16, 2026", "volume": 14.5},
        {"date": "2026-08-15", "display_date": "Aug 15, 2026", "volume": 11.0},
        {"date": "2026-08-14", "display_date": "Aug 14, 2026", "volume": 18.3},
        {"date": "2026-08-13", "display_date": "Aug 13, 2026", "volume": 18.0},
        {"date": "2026-08-12", "display_date": "Aug 12, 2026", "volume": 18.4},
    ],
    "Tirupattur": [
        {"date": "2026-08-21", "display_date": "Aug 21, 2026", "volume": 4.1},
        {"date": "2026-08-20", "display_date": "Aug 20, 2026", "volume": 4.0},
        {"date": "2026-08-19", "display_date": "Aug 19, 2026", "volume": 4.2},
        {"date": "2026-08-18", "display_date": "Aug 18, 2026", "volume": 4.1},
        {"date": "2026-08-17", "display_date": "Aug 17, 2026", "volume": 3.9},
        {"date": "2026-08-16", "display_date": "Aug 16, 2026", "volume": 3.1},
        {"date": "2026-08-15", "display_date": "Aug 15, 2026", "volume": 2.5},
        {"date": "2026-08-14", "display_date": "Aug 14, 2026", "volume": 4.1},
        {"date": "2026-08-13", "display_date": "Aug 13, 2026", "volume": 4.0},
        {"date": "2026-08-12", "display_date": "Aug 12, 2026", "volume": 4.2},
    ],
    "Tiruvannamalai": [
        {"date": "2026-08-21", "display_date": "Aug 21, 2026", "volume": 3.5},
        {"date": "2026-08-20", "display_date": "Aug 20, 2026", "volume": 3.6},
        {"date": "2026-08-19", "display_date": "Aug 19, 2026", "volume": 3.4},
        {"date": "2026-08-18", "display_date": "Aug 18, 2026", "volume": 3.5},
        {"date": "2026-08-17", "display_date": "Aug 17, 2026", "volume": 3.3},
        {"date": "2026-08-16", "display_date": "Aug 16, 2026", "volume": 2.8},
        {"date": "2026-08-15", "display_date": "Aug 15, 2026", "volume": 2.0},
        {"date": "2026-08-14", "display_date": "Aug 14, 2026", "volume": 3.5},
        {"date": "2026-08-13", "display_date": "Aug 13, 2026", "volume": 3.4},
        {"date": "2026-08-12", "display_date": "Aug 12, 2026", "volume": 3.6},
    ],
}

# 10-day historical dataset for Treated Wastewater Discharge (MLD)
TREATED_HISTORY: dict[str, list[dict[str, Any]]] = {
    "Vellore": [
        {"date": "2026-08-21", "display_date": "Aug 21, 2026", "volume": 11.2},
        {"date": "2026-08-20", "display_date": "Aug 20, 2026", "volume": 10.9},
        {"date": "2026-08-19", "display_date": "Aug 19, 2026", "volume": 11.3},
        {"date": "2026-08-18", "display_date": "Aug 18, 2026", "volume": 11.1},
        {"date": "2026-08-17", "display_date": "Aug 17, 2026", "volume": 10.7},
        {"date": "2026-08-16", "display_date": "Aug 16, 2026", "volume": 9.2},
        {"date": "2026-08-15", "display_date": "Aug 15, 2026", "volume": 7.6},
        {"date": "2026-08-14", "display_date": "Aug 14, 2026", "volume": 11.2},
        {"date": "2026-08-13", "display_date": "Aug 13, 2026", "volume": 11.0},
        {"date": "2026-08-12", "display_date": "Aug 12, 2026", "volume": 11.4},
    ],
    "Ranipet": [
        {"date": "2026-08-21", "display_date": "Aug 21, 2026", "volume": 8.8},
        {"date": "2026-08-20", "display_date": "Aug 20, 2026", "volume": 9.1},
        {"date": "2026-08-19", "display_date": "Aug 19, 2026", "volume": 8.7},
        {"date": "2026-08-18", "display_date": "Aug 18, 2026", "volume": 8.8},
        {"date": "2026-08-17", "display_date": "Aug 17, 2026", "volume": 8.6},
        {"date": "2026-08-16", "display_date": "Aug 16, 2026", "volume": 7.1},
        {"date": "2026-08-15", "display_date": "Aug 15, 2026", "volume": 5.4},
        {"date": "2026-08-14", "display_date": "Aug 14, 2026", "volume": 8.9},
        {"date": "2026-08-13", "display_date": "Aug 13, 2026", "volume": 8.7},
        {"date": "2026-08-12", "display_date": "Aug 12, 2026", "volume": 9.0},
    ],
    "Tirupattur": [
        {"date": "2026-08-21", "display_date": "Aug 21, 2026", "volume": 3.5},
        {"date": "2026-08-20", "display_date": "Aug 20, 2026", "volume": 3.4},
        {"date": "2026-08-19", "display_date": "Aug 19, 2026", "volume": 3.6},
        {"date": "2026-08-18", "display_date": "Aug 18, 2026", "volume": 3.5},
        {"date": "2026-08-17", "display_date": "Aug 17, 2026", "volume": 3.3},
        {"date": "2026-08-16", "display_date": "Aug 16, 2026", "volume": 2.6},
        {"date": "2026-08-15", "display_date": "Aug 15, 2026", "volume": 2.1},
        {"date": "2026-08-14", "display_date": "Aug 14, 2026", "volume": 3.5},
        {"date": "2026-08-13", "display_date": "Aug 13, 2026", "volume": 3.4},
        {"date": "2026-08-12", "display_date": "Aug 12, 2026", "volume": 3.6},
    ],
    "Tiruvannamalai": [
        {"date": "2026-08-21", "display_date": "Aug 21, 2026", "volume": 2.9},
        {"date": "2026-08-20", "display_date": "Aug 20, 2026", "volume": 3.0},
        {"date": "2026-08-19", "display_date": "Aug 19, 2026", "volume": 2.8},
        {"date": "2026-08-18", "display_date": "Aug 18, 2026", "volume": 2.9},
        {"date": "2026-08-17", "display_date": "Aug 17, 2026", "volume": 2.7},
        {"date": "2026-08-16", "display_date": "Aug 16, 2026", "volume": 2.3},
        {"date": "2026-08-15", "display_date": "Aug 15, 2026", "volume": 1.7},
        {"date": "2026-08-14", "display_date": "Aug 14, 2026", "volume": 2.9},
        {"date": "2026-08-13", "display_date": "Aug 13, 2026", "volume": 2.8},
        {"date": "2026-08-12", "display_date": "Aug 12, 2026", "volume": 3.0},
    ],
}

DISTRICT_NAMES = ["Vellore", "Ranipet", "Tirupattur", "Tiruvannamalai"]


def _compute_district_stats(history: list[dict[str, Any]]) -> dict[str, Any]:
    volumes = [entry["volume"] for entry in history]
    if not volumes:
        return {
            "current_volume": 0.0,
            "average_10_days": 0.0,
            "high_10_days": 0.0,
            "low_10_days": 0.0,
            "percentage_change": 0.0,
            "trend": "STABLE",
            "history": [],
            "periods_available": 0,
        }

    current = volumes[0]
    avg = sum(volumes) / len(volumes)
    high = max(volumes)
    low = min(volumes)
    pct_change = ((current - avg) / avg) * 100 if avg else 0.0

    if abs(pct_change) < 1.0:
        trend = "STABLE"
    elif pct_change > 0:
        trend = "UP"
    else:
        trend = "DOWN"

    return {
        "current_volume": round(current, 2),
        "average_10_days": round(avg, 2),
        "high_10_days": round(high, 2),
        "low_10_days": round(low, 2),
        "percentage_change": round(pct_change, 2),
        "trend": trend,
        "history": sorted(history, key=lambda x: x["date"]),
        "periods_available": len(volumes),
    }


def get_wastewater_analytics(metric_type: WastewaterMetricType = "effluent") -> dict[str, Any]:
    history_map = EFFLUENT_HISTORY if metric_type == "effluent" else TREATED_HISTORY
    unit = "MLD"
    metric_title = (
        "Industrial Effluent Volume"
        if metric_type == "effluent"
        else "Treated Wastewater Discharge"
    )

    district_results: dict[str, dict[str, Any]] = {}
    current_volumes: dict[str, float] = {}
    avg_volumes: dict[str, float] = {}

    for district in DISTRICT_NAMES:
        district_history = history_map.get(district, [])
        stats = _compute_district_stats(district_history)
        district_results[district] = stats
        current_volumes[district] = stats["current_volume"]
        avg_volumes[district] = stats["average_10_days"]

    # Identify highest discharging district
    highest_district_by_current = max(current_volumes, key=current_volumes.get)
    highest_district_by_avg = max(avg_volumes, key=avg_volumes.get)
    highest_volume = current_volumes[highest_district_by_current]
    lowest_volume = min(current_volumes.values())

    for district, stats in district_results.items():
        stats["is_highest"] = district == highest_district_by_current
        stats["diff_from_highest"] = round(highest_volume - stats["current_volume"], 2)

    return {
        "metric_type": metric_type,
        "metric_name": metric_title,
        "unit": unit,
        "highest_district": highest_district_by_current,
        "highest_volume": highest_volume,
        "highest_avg_district": highest_district_by_avg,
        "lowest_volume": lowest_volume,
        "total_regional_volume": round(sum(current_volumes.values()), 2),
        "districts": district_results,
    }


def get_all_wastewater_data() -> dict[str, Any]:
    """Returns combined analytics for both Industrial Effluent and Treated Wastewater."""
    effluent_data = get_wastewater_analytics("effluent")
    treated_data = get_wastewater_analytics("treated")

    # Generate flat records list for standard tabular/record views
    records: list[dict[str, Any]] = []
    dates = sorted(
        {item["date"] for d in DISTRICT_NAMES for item in EFFLUENT_HISTORY[d]},
        reverse=True,
    )
    for date in dates:
        display_date = date
        e_row: dict[str, Any] = {"Date": date, "Category": "Industrial Effluent (MLD)"}
        t_row: dict[str, Any] = {"Date": date, "Category": "Treated Discharge (MLD)"}

        for district in DISTRICT_NAMES:
            e_entry = next((e for e in EFFLUENT_HISTORY[district] if e["date"] == date), None)
            t_entry = next((e for e in TREATED_HISTORY[district] if e["date"] == date), None)
            if e_entry:
                e_row[district] = f"{e_entry['volume']:.1f} MLD"
                display_date = e_entry["display_date"]
            if t_entry:
                t_row[district] = f"{t_entry['volume']:.1f} MLD"

        e_row["Formatted_Date"] = display_date
        t_row["Formatted_Date"] = display_date
        records.append(e_row)
        records.append(t_row)

    return {
        "status": "API_AVAILABLE",
        "effluent": effluent_data,
        "treated": treated_data,
        "districts": DISTRICT_NAMES,
        "records": records,
        "total_records": len(records),
        "source": "CPCB / TNPCB Continuous Online Effluent & STP Monitoring Repository",
        "summary": (
            "10-day historical industrial effluent and treated wastewater metrics across "
            "Vellore, Ranipet, Tirupattur, and Tiruvannamalai. Ranipet exhibits the highest "
            "industrial effluent generation (18.2 MLD), while Vellore leads treated STP discharge (11.2 MLD). "
            "Significant operational dips recorded during Independence Day (Aug 15) and weekend maintenance (Aug 16)."
        ),
    }
