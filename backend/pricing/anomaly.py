"""Price-Quality Anomaly Detector and Confidence-Aware Negotiation Engine.

Prevents premature or false-certainty classifications by making deal verdicts
downstream of valuation uncertainty.
"""

from typing import Optional, Dict, Any
from config import settings
from core.schemas import (
    ValuationResult,
    AnomalyAnalysisResult,
    AnomalyState,
    SeverityLevel,
    NegotiationStrategy,
)


class PriceQualityAnomalyDetector:
    """
    Evaluates vendor asking prices against fair valuation intervals, visual freshness,
    and compound valuation confidence.
    """

    def analyze_price_anomaly(
        self,
        valuation: ValuationResult,
        asking_price: float,
        quickcommerce_ref_price: Optional[float] = None
    ) -> AnomalyAnalysisResult:
        f_min = valuation.fair_min
        f_max = valuation.fair_max
        f_mid = valuation.fair_mid
        confidence = valuation.confidence
        uncertainty = valuation.valuation_uncertainty
        quality_score = valuation.quality_estimate.quality_score
        quality_class = valuation.quality_estimate.quality_class

        # 1. Check if valuation confidence is insufficient
        is_confident = confidence >= settings.INSUFFICIENT_CONFIDENCE_THRESHOLD

        # Calculate deviation percentage relative to relevant fair bound
        if asking_price > f_max:
            deviation_pct = round(((asking_price - f_max) / f_max) * 100.0, 1)
            position = "ABOVE"
        elif asking_price < f_min:
            deviation_pct = round(((f_min - asking_price) / f_min) * 100.0, 1)
            position = "BELOW"
        else:
            deviation_pct = 0.0
            position = "WITHIN"

        # Classify Severity Level
        if deviation_pct == 0.0:
            severity = SeverityLevel.NONE
        elif not is_confident:
            severity = SeverityLevel.UNCERTAIN
        elif deviation_pct <= settings.SLIGHT_DEVIATION_THRESHOLD_PCT:
            severity = SeverityLevel.SLIGHT
        elif deviation_pct <= settings.SIGNIFICANT_DEVIATION_THRESHOLD_PCT:
            severity = SeverityLevel.MODERATE
        else:
            severity = SeverityLevel.SIGNIFICANT

        # 2. Decision Logic
        quality_caution: Optional[str] = None

        if not is_confident:
            # Low confidence guard: Do not output confident binary OVERPRICED claims
            decision = AnomalyState.INSUFFICIENT_CONFIDENCE
            action = "VERIFY_FIRST"
            headline = "Valuation confidence is currently low."
            explanation = (
                f"Vendor asks ₹{asking_price}/kg. Our estimated range is ₹{f_min}–₹{f_max}/kg, "
                f"but valuation uncertainty is elevated ({uncertainty:.2f}). "
                "Confirm item grade and weight before negotiating aggressively."
            )
            strategy = NegotiationStrategy(
                starting_offer=round(f_mid, 1),
                target_price=round(min(asking_price, f_max), 1),
                maximum_reasonable_price=asking_price,
                potential_saving=0.0,
                below_fair_amount=0.0,
                confidence_caution="High uncertainty; proceed cautiously.",
            )

        elif position == "WITHIN":
            decision = AnomalyState.FAIR_PRICE
            action = "BUY"
            headline = "Asking price is within the expected fair range."
            explanation = f"₹{asking_price}/kg falls cleanly within the estimated fair range of ₹{f_min}–₹{f_max}/kg."
            strategy = NegotiationStrategy(
                starting_offer=asking_price,
                target_price=asking_price,
                maximum_reasonable_price=f_max,
                potential_saving=0.0,
                below_fair_amount=0.0,
            )

        elif position == "ABOVE":
            if severity == SeverityLevel.SLIGHT:
                decision = AnomalyState.SLIGHTLY_HIGH
                action = "NEGOTIATE"
                headline = f"Slightly above fair range (₹{round(asking_price - f_max, 1)} above max)."
                explanation = f"Asking price is {deviation_pct}% above the estimated fair ceiling of ₹{f_max}/kg. A polite discount is reasonable."
                strategy = NegotiationStrategy(
                    starting_offer=round(f_mid, 1),
                    target_price=round(f_max, 1),
                    maximum_reasonable_price=asking_price,
                    potential_saving=round(max(0.0, asking_price - f_max), 1),
                    below_fair_amount=0.0,
                )
            else:
                decision = AnomalyState.OVERPRICED
                action = "NEGOTIATE"
                headline = f"Asking price is overpriced by {deviation_pct}%."
                explanation = f"₹{asking_price}/kg exceeds the fair ceiling (₹{f_max}/kg) by {deviation_pct}%. Active counter-offer recommended."
                strategy = NegotiationStrategy(
                    starting_offer=round(f_min, 1),
                    target_price=round(f_mid, 1),
                    maximum_reasonable_price=round(f_max, 1),
                    potential_saving=round(max(0.0, asking_price - f_max), 1),
                    below_fair_amount=0.0,
                )

        else:  # position == "BELOW"
            if quality_score < settings.UNUSUALLY_CHEAP_QUALITY_THRESHOLD or "overripe" in quality_class.lower():
                decision = AnomalyState.UNUSUALLY_CHEAP
                action = "CHECK_QUALITY"
                headline = "Price is unusually low — inspect for decay."
                quality_caution = "Produce exhibits observable quality decay. Buy only if using immediately."
                explanation = (
                    f"₹{asking_price}/kg is {deviation_pct}% below wholesale-fair minimum (₹{f_min}/kg), "
                    "but physical inspection indicates significant aging or decay."
                )
                strategy = NegotiationStrategy(
                    starting_offer=asking_price,
                    target_price=asking_price,
                    maximum_reasonable_price=round(f_max, 1),
                    potential_saving=0.0,
                    below_fair_amount=round(f_min - asking_price, 1),
                    confidence_caution="Inspect produce carefully before paying.",
                )
            else:
                decision = AnomalyState.GOOD_DEAL
                action = "BUY"
                headline = f"Genuine good deal — ₹{round(f_min - asking_price, 1)} below fair minimum."
                explanation = f"₹{asking_price}/kg is {deviation_pct}% below expected fair minimum (₹{f_min}/kg), and visual freshness is verified."
                strategy = NegotiationStrategy(
                    starting_offer=asking_price,
                    target_price=asking_price,
                    maximum_reasonable_price=round(f_max, 1),
                    potential_saving=0.0,
                    below_fair_amount=round(f_min - asking_price, 1),
                )

        # Quick-Commerce Reference comparison
        if quickcommerce_ref_price and quickcommerce_ref_price > 0:
            if asking_price > quickcommerce_ref_price and asking_price > f_max:
                explanation += f" Vendor is more expensive than quick-commerce (₹{quickcommerce_ref_price}/kg)."
            elif asking_price <= quickcommerce_ref_price and asking_price > f_max:
                explanation += f" Vendor is cheaper than quick-commerce (₹{quickcommerce_ref_price}/kg) but above local mandi fair range."

        return AnomalyAnalysisResult(
            decision=decision,
            severity=severity,
            deviation_pct=deviation_pct,
            is_confidence_sufficient=is_confident,
            asking_price=asking_price,
            fair_min=f_min,
            fair_max=f_max,
            strategy=strategy,
            recommendation_action=action,
            recommendation_headline=headline,
            recommendation_explanation=explanation,
            reasoning=explanation,
            quality_caution=quality_caution,
        )
