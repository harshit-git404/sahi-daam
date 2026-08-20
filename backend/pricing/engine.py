from typing import Any


def calculate_fair_price(
    wholesale_price: float,
    markup_min_pct: float,
    markup_max_pct: float,
    quality_adjustment: int,
) -> dict[str, float]:
    """Calculate the freshness-adjusted fair retail range in one place."""
    min_price = max(0.0, wholesale_price * (1 + markup_min_pct / 100) + quality_adjustment)
    max_price = max(min_price, wholesale_price * (1 + markup_max_pct / 100) + quality_adjustment)
    return {"min": round(min_price, 2), "max": round(max_price, 2)}


def calculate_haggle_verdict(asking_price: float, fair_price_range: dict[str, float]) -> dict[str, Any]:
    """Compare an asking price with the real fair range and suggest a bounded offer."""
    fair_min = float(fair_price_range["min"])
    fair_max = float(fair_price_range["max"])
    baseline = fair_max if asking_price >= fair_max else fair_min
    deviation_pct = round(((asking_price - baseline) / baseline) * 100, 2) if baseline else 0.0

    if asking_price > fair_max:
        verdict = "HIGH"
        suggested_price = round((fair_min + fair_max) / 2, 2)
        explanation = f"The asking price is {deviation_pct:.1f}% above the upper fair-price boundary."
    elif asking_price < fair_min:
        verdict = "LOW"
        suggested_price = round(asking_price, 2)
        explanation = "The asking price is below the calculated fair-price range — a good deal."
    else:
        verdict = "FAIR"
        suggested_price = round(asking_price, 2)
        explanation = "The asking price is within the verified fair-price range."

    return {
        "verdict": verdict,
        "deviation_pct": deviation_pct,
        "suggested_price": suggested_price,
        "suggested_price_min": round(fair_min, 2),
        "suggested_price_max": round(fair_max, 2),
        "explanation": explanation,
    }
