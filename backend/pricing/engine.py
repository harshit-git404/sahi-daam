from typing import Dict, Optional, Any

# ============================================================
# DEVIATION SEVERITY THRESHOLDS
# ============================================================
# All thresholds are percentage deviations relative to the
# fair price range boundary — NOT fixed rupee amounts.
# This ensures a ₹5 deviation on ₹20 produce carries a very
# different weight than ₹5 on ₹200 produce.
#
# For prices ABOVE fair_max:
#   SLIGHTLY_HIGH:  0% < deviation <= 10%
#   OVERPRICED:    10% < deviation <= 30%
#   SIGNIFICANTLY_OVERPRICED: deviation > 30%
#
# For prices BELOW fair_min:
#   SLIGHTLY_BELOW: 0% < deviation <= 10%  → always GOOD_DEAL or FAIR_PRICE-adjacent
#   MEANINGFULLY_BELOW: 10%-30%             → GOOD_DEAL (fresh) / UNUSUALLY_CHEAP (not fresh)
#   SUSPICIOUSLY_BELOW: > 30%               → UNUSUALLY_CHEAP (any quality) / GOOD_DEAL only if quality="Fresh"
#
# Rationale for 10% / 30% cutpoints:
#   10%: On a ₹30 fair-max item, this is ₹3 — a meaningful but tolerable deviation.
#   30%: On a ₹30 item, this is ₹9 — clearly worth negotiating aggressively.
#   These align with observed vegetable mandi price volatility in India (10-15% daily
#   fluctuation is normal, >30% is unusual).
SLIGHT_THRESHOLD_PCT = 10.0
SIGNIFICANT_THRESHOLD_PCT = 30.0

def calculate_fair_price(
    wholesale_price: float,
    markup_min_pct: float,
    markup_max_pct: float,
    quality_adjustment: int
) -> Dict[str, float]:
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


def _classify_severity(deviation_pct: float) -> str:
    """Returns severity label for a given percentage deviation from fair boundary."""
    if deviation_pct <= SLIGHT_THRESHOLD_PCT:
        return "SLIGHT"
    elif deviation_pct <= SIGNIFICANT_THRESHOLD_PCT:
        return "MODERATE"
    else:
        return "SIGNIFICANT"


def _negotiation_strategy(
    f_min: float,
    f_max: float,
    asking_price: float,
    severity: str,
    position: str  # "ABOVE" | "WITHIN" | "BELOW"
) -> Dict[str, float]:
    """
    Computes starting_offer, target_price, maximum_reasonable_price.
    
    Strategy rules:
    - WITHIN range  → no aggressive negotiation; max = f_max
    - SLIGHT above  → start at fair midpoint, target at f_max, max at asking (small give)
    - MODERATE above → start at f_min, target at fair midpoint, max at f_max
    - SIGNIFICANT above → start at f_min, target at fair midpoint, max at f_max
    - BELOW range   → action=BUY; starting offer = asking, max = f_max (you're already winning)
    """
    fair_mid = round((f_min + f_max) / 2, 1)
    
    if position == "WITHIN":
        return {
            "starting_offer": round(asking_price, 1),
            "target_price": round(asking_price, 1),
            "maximum_reasonable_price": round(f_max, 1),
        }
    elif position == "BELOW":
        return {
            "starting_offer": round(asking_price, 1),
            "target_price": round(asking_price, 1),
            "maximum_reasonable_price": round(f_max, 1),
        }
    elif severity == "SLIGHT":
        # Only a small reduction needed — polite ask, not a hard negotiation
        return {
            "starting_offer": round(fair_mid, 1),
            "target_price": round(f_max, 1),
            "maximum_reasonable_price": round(asking_price, 1),  # It's close, max is asking
        }
    elif severity == "MODERATE":
        return {
            "starting_offer": round(f_min, 1),
            "target_price": round(fair_mid, 1),
            "maximum_reasonable_price": round(f_max, 1),
        }
    else:  # SIGNIFICANT
        return {
            "starting_offer": round(f_min, 1),
            "target_price": round(fair_mid, 1),
            "maximum_reasonable_price": round(f_max, 1),
        }


def _quality_note(quality_info: Optional[str], position: str, decision: str) -> Optional[str]:
    """
    Returns a quality caution note when quality affects the purchasing decision.
    Returns None if quality doesn't add meaningful context.
    """
    if not quality_info:
        return None
    q = quality_info.lower()
    if q in ("overripe", "slightly aged", "slightly_aged") and position == "BELOW":
        return f"The produce is {quality_info.lower()} — buy only if you plan to use it today."
    if q in ("overripe", "slightly aged", "slightly_aged") and position == "WITHIN":
        return f"Note: produce is {quality_info.lower()} at this price."
    if q == "fresh" and decision == "GOOD_DEAL":
        return "Fresh quality at a below-fair price — a genuine good deal."
    return None


def analyze_purchase_decision(
    fair_price_min: float,
    fair_price_max: float,
    asking_price: float,
    quality_info: Optional[str] = None,
    quickcommerce_price: Optional[Dict[str, Any]] = None
) -> dict:
    """
    Full negotiation intelligence engine.
    
    Determines:
      - decision (user-facing state)
      - severity (SLIGHT / MODERATE / SIGNIFICANT)
      - negotiation strategy (starting_offer, target_price, max_price)
      - quality-aware reasoning
      - quick-commerce comparison
    
    All thresholds are percentage-based relative to the fair range boundary.
    See module-level THRESHOLD constants for rationale.
    """
    f_min = fair_price_min
    f_max = fair_price_max

    # --- Deviation calculation ---
    if asking_price > f_max:
        deviation_pct = ((asking_price - f_max) / f_max) * 100
        position = "ABOVE"
    elif asking_price < f_min:
        deviation_pct = ((f_min - asking_price) / f_min) * 100
        position = "BELOW"
    else:
        deviation_pct = 0.0
        position = "WITHIN"

    severity = _classify_severity(deviation_pct) if deviation_pct > 0 else "NONE"

    # --- Quality normalisation ---
    quality_lower = quality_info.lower().strip() if quality_info else ""
    is_fresh = quality_lower in ("fresh",)
    is_poor = quality_lower in ("overripe", "slightly aged", "slightly_aged")

    # --- Decision matrix ---
    if position == "WITHIN":
        decision = "FAIR_PRICE"
        action = "BUY"
        if severity == "NONE":
            headline = "This asking price is within the expected range."
        else:
            headline = "Asking price is within the fair range."
        explanation = (
            f"Rs{asking_price}/kg is within the estimated fair range of "
            f"Rs{f_min}\u2013{f_max}/kg."
        )

    elif position == "ABOVE":
        if severity == "SLIGHT":
            decision = "SLIGHTLY_HIGH"
            action = "NEGOTIATE"
            headline = f"Only Rs{round(asking_price - f_max, 1)} above the estimated fair range."
            explanation = (
                f"Rs{asking_price}/kg is just {round(deviation_pct, 1)}% above the fair "
                f"maximum (Rs{f_max}/kg). A small ask for a reduction is reasonable."
            )
        elif severity == "MODERATE":
            decision = "OVERPRICED"
            action = "NEGOTIATE"
            headline = "You're paying above the fair range."
            explanation = (
                f"Rs{asking_price}/kg is {round(deviation_pct, 1)}% above the fair maximum "
                f"(Rs{f_max}/kg). The estimated fair range is Rs{f_min}\u2013{f_max}/kg."
            )
        else:  # SIGNIFICANT
            decision = "OVERPRICED"
            action = "NEGOTIATE"
            headline = f"Rs{round(asking_price - f_max, 1)} above the estimated fair maximum."
            explanation = (
                f"Rs{asking_price}/kg is {round(deviation_pct, 1)}% above the fair "
                f"maximum (Rs{f_max}/kg). The estimated fair range is Rs{f_min}\u2013{f_max}/kg. "
                f"Strong negotiation is recommended."
            )

    else:  # BELOW
        if is_fresh and severity in ("MODERATE", "SIGNIFICANT"):
            decision = "GOOD_DEAL"
            action = "BUY"
            headline = "You're getting this below the estimated fair price."
            explanation = (
                f"Rs{asking_price}/kg is {round(deviation_pct, 1)}% below the fair minimum "
                f"(Rs{f_min}/kg), and the produce is classified as fresh."
            )
        elif is_fresh and severity == "SLIGHT":
            decision = "GOOD_DEAL"
            action = "BUY"
            headline = "Slightly below fair range — good buy."
            explanation = (
                f"Rs{asking_price}/kg is just below the fair range of Rs{f_min}\u2013{f_max}/kg, "
                f"and the produce looks fresh."
            )
        elif is_poor:
            decision = "UNUSUALLY_CHEAP"
            action = "CHECK_QUALITY"
            headline = "This price is unusually low."
            explanation = (
                f"Rs{asking_price}/kg is {round(deviation_pct, 1)}% below the expected fair range "
                f"(Rs{f_min}\u2013{f_max}/kg). The produce is also {quality_info} "
                f"\u2014 check freshness carefully before buying."
            )
        else:
            # Unknown or slightly_aged at slight below
            if severity == "SLIGHT":
                decision = "FAIR_PRICE"
                action = "BUY"
                headline = "Slightly below the fair range — reasonable deal."
                explanation = (
                    f"Rs{asking_price}/kg is just below the fair range of "
                    f"Rs{f_min}\u2013{f_max}/kg."
                )
            else:
                decision = "UNUSUALLY_CHEAP"
                action = "CHECK_QUALITY"
                headline = "This price is unusually low."
                explanation = (
                    f"Rs{asking_price}/kg is {round(deviation_pct, 1)}% below the expected "
                    f"fair range (Rs{f_min}\u2013{f_max}/kg). Check freshness and quality."
                )

    # --- Negotiation strategy ---
    neg = _negotiation_strategy(f_min, f_max, asking_price, severity, position)
    starting_offer = neg["starting_offer"]
    target_price = neg["target_price"]
    maximum_reasonable_price = neg["maximum_reasonable_price"]

    # --- Savings ---
    if position == "ABOVE":
        potential_saving = round(asking_price - f_max, 1)
        below_fair_amount = 0.0
    elif position == "BELOW":
        potential_saving = 0.0
        below_fair_amount = round(f_min - asking_price, 1)
    else:
        potential_saving = 0.0
        below_fair_amount = 0.0

    # --- Quality context ---
    quality_caution = _quality_note(quality_info, position, decision)

    # --- Legacy verdict for phrasebook backward compat ---
    legacy_verdict_map = {
        "OVERPRICED": "Overpriced",
        "SLIGHTLY_HIGH": "Overpriced",
        "UNUSUALLY_CHEAP": "Suspiciously Cheap",
        "GOOD_DEAL": "Fair Price",
        "FAIR_PRICE": "Fair Price",
    }
    legacy_verdict = legacy_verdict_map.get(decision, "Fair Price")

    result = {
        # Legacy fields (kept for backward compat)
        "verdict": legacy_verdict,
        "suggested_price": starting_offer,

        # New decision fields
        "decision": decision,
        "severity": severity,
        "deviation_pct": round(deviation_pct, 1),
        "starting_offer": starting_offer,
        "target_price": target_price,
        "maximum_reasonable_price": maximum_reasonable_price,
        "potential_saving": potential_saving,
        "below_fair_amount": below_fair_amount,
        "reasoning": explanation,
        "recommendation": {
            "action": action,
            "headline": headline,
            "explanation": explanation,
        },
        "quality_context": {
            "freshness_label": quality_info,
            "caution": quality_caution,
        },
    }

    # --- Quick-commerce intelligence ---
    if quickcommerce_price:
        qc_price = quickcommerce_price.get("price")
        if qc_price:
            qc_source = quickcommerce_price.get("source", "Quick-commerce")
            qc_unit = quickcommerce_price.get("unit", "kg")

            if asking_price > qc_price and asking_price > f_max:
                qc_note = (
                    f" Quick-commerce reference ({qc_source}) is Rs{qc_price}/{qc_unit} "
                    f"— vendor is currently more expensive than both fair range and quick-commerce."
                )
            elif asking_price <= qc_price and asking_price > f_max:
                qc_note = (
                    f" Vendor is still cheaper than {qc_source} (Rs{qc_price}/{qc_unit}), "
                    f"but above the local fair range."
                )
            elif asking_price <= f_max and asking_price <= f_min:
                qc_note = (
                    f" Vendor is clearly cheaper than {qc_source} "
                    f"(Rs{qc_price}/{qc_unit})."
                )
            elif asking_price <= f_max:
                qc_note = (
                    f" Vendor (Rs{asking_price}/{qc_unit}) is cheaper than "
                    f"{qc_source} (Rs{qc_price}/{qc_unit})."
                )
            else:
                qc_note = ""

            if qc_note:
                result["recommendation"]["explanation"] += qc_note
                result["reasoning"] += qc_note

        result["alternatives"] = {"quickcommerce": quickcommerce_price}

    return result

