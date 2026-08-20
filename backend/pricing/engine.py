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

from typing import Dict, Optional, Any

def analyze_purchase_decision(
    fair_price_min: float,
    fair_price_max: float,
    asking_price: float,
    quality_info: Optional[str] = None,
    quickcommerce_price: Optional[Dict[str, Any]] = None
) -> dict:
    """
    Analyzes the purchase decision based on asking price, fair price range, quality, and alternatives.
    Returns a structured decision object.
    """
    f_min = fair_price_min
    f_max = fair_price_max
    
    # Calculate Deviation
    if asking_price > f_max:
        deviation_pct = ((asking_price - f_max) / f_max) * 100
    elif asking_price < f_min:
        deviation_pct = ((f_min - asking_price) / f_min) * 100
    else:
        deviation_pct = 0.0

    # Decision Matrix
    if asking_price > f_max:
        decision = "OVERPRICED"
        action = "NEGOTIATE"
        headline = "You're paying above the fair range."
        explanation = f"Vendor is asking ₹{asking_price}/kg, while the estimated fair range for this produce is ₹{f_min}–{f_max}/kg. The asking price is about {round(deviation_pct)}% above the fair maximum."
    elif asking_price < f_min:
        # Check if quality is good enough to be a GOOD DEAL
        if quality_info and quality_info.lower() == "fresh":
            decision = "GOOD_DEAL"
            action = "BUY"
            headline = "You're getting this below the estimated fair price."
            explanation = f"₹{asking_price}/kg is below the estimated fair range (₹{f_min}–{f_max}/kg) while the produce is classified as fresh."
        else:
            decision = "UNUSUALLY_CHEAP"
            action = "CHECK QUALITY"
            headline = "This price is unusually low."
            explanation = f"₹{asking_price}/kg is below the expected fair range of ₹{f_min}–{f_max}/kg. Check freshness and quality before buying."
    else:
        decision = "FAIR_PRICE"
        action = "BUY"
        headline = "This asking price is within the expected range."
        explanation = f"₹{asking_price}/kg is within the estimated fair range of ₹{f_min}–{f_max}/kg."
        
    # Negotiation Math
    suggested_starting_offer = round(f_min, 1)
    maximum_reasonable_price = round(f_max, 1)
    potential_saving = max(0.0, round(asking_price - f_max, 1)) if asking_price > f_max else 0.0

    # For legacy phrasebook compatibility
    if decision == "OVERPRICED":
        legacy_verdict = "Overpriced"
    elif decision == "UNUSUALLY_CHEAP":
        legacy_verdict = "Suspiciously Cheap"
    elif decision == "GOOD_DEAL":
        legacy_verdict = "Fair Price" # Fallback so phrasebook doesn't break
    else:
        legacy_verdict = "Fair Price"

    result = {
        "verdict": legacy_verdict,
        "decision": decision,
        "deviation_pct": round(deviation_pct, 1),
        "suggested_price": suggested_starting_offer if decision == "OVERPRICED" else asking_price,
        "maximum_reasonable_price": maximum_reasonable_price,
        "potential_saving": potential_saving,
        "reasoning": explanation,
        "recommendation": {
            "action": action,
            "headline": headline,
            "explanation": explanation
        }
    }
    
    if quickcommerce_price:
        qc_price = quickcommerce_price.get("price")
        if qc_price:
            qc_source = quickcommerce_price.get("source", "Quick-commerce")
            qc_unit = quickcommerce_price.get("unit", "kg")
            
            qc_comparison = ""
            if asking_price > qc_price and asking_price > f_max:
                qc_comparison = f" {qc_source} is cheaper at ₹{qc_price}/{qc_unit}, making the vendor the worst option."
            elif asking_price < qc_price and asking_price > f_max:
                qc_comparison = f" Vendor is still cheaper than {qc_source} (₹{qc_price}/{qc_unit}), but slightly above fair."
            elif asking_price > qc_price:
                qc_comparison = f" You can get it cheaper on {qc_source} for ₹{qc_price}/{qc_unit}."
            
            if qc_comparison:
                result["recommendation"]["explanation"] += qc_comparison
                result["reasoning"] += qc_comparison
                
        result["alternatives"] = {
            "quickcommerce": quickcommerce_price
        }

    return result
