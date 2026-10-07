"""Quality-to-Price Adjustment Model.

Replaces fixed rigid rupee deductions with a parameterized, commodity-aware,
market-grounded quality deduction function with explicit adjustment uncertainty.
"""

from typing import Optional, Dict, Any
from core.schemas import QualityPriceAdjustment, QualityEstimate


class QualityPriceAdjustmentModel:
    """
    Computes market-relative quality deductions and propagates adjustment uncertainty.
    
    Formula:
    --------
    Deduction is proportional to relative quality deficit and baseline market price:
    
      Deficit = max(0.0, 1.0 - quality_score)
      
      For minor aging (quality >= 0.80):
          adj = 0.0
      For moderate aging (0.50 <= quality < 0.80):
          adj = -1.0 * (Deficit * 0.30 * P_market)
      For severe decay (quality < 0.50):
          adj = -1.0 * (Deficit * 0.60 * P_market)
    """

    def compute_adjustment(
        self,
        quality_estimate: QualityEstimate,
        market_price: float,
        commodity: str = "tomato",
        commodity_params: Optional[Dict[str, Any]] = None
    ) -> QualityPriceAdjustment:
        p_market = max(1.0, market_price)
        q_score = quality_estimate.quality_score
        q_class = quality_estimate.quality_class.lower()

        # Commodity perishability multiplier (e.g. leafy greens decay faster than potatoes)
        perishability_factors = {
            "spinach": 1.3,
            "coriander": 1.3,
            "tomato": 1.1,
            "banana": 1.0,
            "onion": 0.7,
            "potato": 0.6,
        }
        factor = perishability_factors.get(commodity.lower(), 1.0)

        deficit = max(0.0, 1.0 - q_score)

        if q_score >= 0.82 and "overripe" not in q_class:
            adj = 0.0
            rationale = "Quality is prime; no economic deduction applied."
            adj_unc = round(quality_estimate.uncertainty * 0.5, 3)
        elif q_score >= 0.50:
            # Moderate softening / aging: up to 10-15% deduction
            raw_deduction = deficit * 0.28 * p_market * factor
            adj = -1.0 * round(raw_deduction, 2)
            rationale = f"Moderate aging detected; deducting {abs(adj)} ₹/kg based on condition deficit."
            adj_unc = round(min(0.85, quality_estimate.uncertainty * 1.1), 3)
        else:
            # Severe degradation: steep 25-50% deduction
            raw_deduction = (0.20 + deficit * 0.45) * p_market * factor
            adj = -1.0 * round(raw_deduction, 2)
            rationale = f"Substantial degradation detected; steep markdown of {abs(adj)} ₹/kg recommended."
            adj_unc = round(min(0.95, quality_estimate.uncertainty * 1.3), 3)

        # Cap deduction so price cannot become negative
        max_possible_deduction = -0.75 * p_market
        adj = max(max_possible_deduction, adj)

        confidence = round(max(0.1, 1.0 - adj_unc), 3)

        return QualityPriceAdjustment(
            commodity=commodity,
            base_market_price=p_market,
            adjustment_per_kg=round(adj, 2),
            adjustment_uncertainty=adj_unc,
            method="market_proportional_quality_decay",
            confidence=confidence,
            rationale=rationale,
        )
