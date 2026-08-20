from typing import Dict

def calculate_fair_price(wholesale_price: float, markup_min_pct: float, markup_max_pct: float, quality_adjustment: int) -> Dict[str, float]:
    """
    Calculates a fair retail price range based on wholesale data, typical markups, and freshness.
    Returns: {"min": float, "max": float}
    """
    base_min = wholesale_price * (1 + markup_min_pct / 100.0)
    base_max = wholesale_price * (1 + markup_max_pct / 100.0)
    
    # quality_adjustment is a monetary deduction (e.g., -2 rupees per kg)
    adj_min = max(0.0, base_min + quality_adjustment)
    adj_max = max(0.0, base_max + quality_adjustment)
    
    return {"min": round(adj_min, 2), "max": round(adj_max, 2)}

def calculate_haggle_verdict(asking_price: float, fair_price_range: Dict[str, float]) -> dict:
    """
    Checks asking price against fair price range.
    """
    f_min = fair_price_range["min"]
    f_max = fair_price_range["max"]
    
    if asking_price > f_max:
        verdict = "Overpriced"
        deviation_pct = ((asking_price - f_max) / f_max) * 100
        suggested = f_max
        reasoning = f"The vendor's asking price of ₹{asking_price} is {round(deviation_pct)}% above the fair market maximum (₹{f_max}). You should counter-offer around ₹{f_max}."
    elif asking_price < f_min:
        verdict = "Suspiciously Cheap"
        deviation_pct = ((f_min - asking_price) / f_min) * 100
        suggested = asking_price
        reasoning = f"The price is {round(deviation_pct)}% below the wholesale baseline. Check for hidden rot or short-weighting, but if good, it's a steal!"
    else:
        verdict = "Fair Price"
        deviation_pct = 0.0
        suggested = asking_price
        reasoning = f"The asking price of ₹{asking_price} is within the fair market range of ₹{f_min} to ₹{f_max}. No haggling needed."
        
    return {
        "verdict": verdict,
        "deviation_pct": round(deviation_pct, 1),
        "suggested_price": round(suggested, 1),
        "reasoning": reasoning
    }
