"""Uncertainty-Aware Valuation Engine.

Combines weighted market benchmarks, visual quality assessments, and economic margins.
Propagates compound uncertainty through the valuation to dynamically calibrate
the fair-price interval width.
"""

import math
from typing import Dict, Any, Optional
from config import settings
from core.schemas import (
    QualityEstimate,
    WeightedMarketPriceEstimate,
    QualityPriceAdjustment,
    ValuationResult,
)
from valuation.adjustment import QualityPriceAdjustmentModel


class UncertaintyAwareValuationEngine:
    """
    Computes fair retail price intervals with explicit uncertainty propagation.
    
    Uncertainty Propagation Formulation:
    ------------------------------------
    Total valuation variance sigma_fair^2 is approximated via variance summation:
    
        sigma_fair^2 = w_m * sigma_market^2
                     + w_q * sigma_quality^2
                     + w_a * sigma_adj^2
                     + sigma_model_residual^2
                     
    where:
      - sigma_market: Uncertainty from market source divergence & recency.
      - sigma_quality: Epistemic visual uncertainty (occlusion, blur, confidence).
      - sigma_adj: Elasticity uncertainty in the quality-to-price adjustment.
      
    Interval Expansion:
    -------------------
    The baseline fair interval [base_min, base_max] widens symmetrically:
        Delta_expand = base_mid * sigma_fair * UNCERTAINTY_RANGE_EXPANSION_FACTOR
        fair_min = max(0.0, base_min - Delta_expand)
        fair_max = base_max + Delta_expand
    """

    def __init__(self, adjustment_model: Optional[QualityPriceAdjustmentModel] = None):
        self.adjustment_model = adjustment_model or QualityPriceAdjustmentModel()

    def calculate_valuation(
        self,
        quality_estimate: QualityEstimate,
        market_estimate: WeightedMarketPriceEstimate,
        markup_min_pct: float = settings.MIN_RETAIL_MARKUP_PCT,
        markup_max_pct: float = settings.MAX_RETAIL_MARKUP_PCT,
        commodity: Optional[str] = None
    ) -> ValuationResult:
        comm = (commodity or quality_estimate.commodity).lower()
        p_market = market_estimate.estimated_price_per_kg

        # 1. Quality Price Adjustment
        adj = self.adjustment_model.compute_adjustment(
            quality_estimate=quality_estimate,
            market_price=p_market,
            commodity=comm
        )

        # 2. Uncertainty Propagation
        # Variance addition
        sigma_m = market_estimate.market_uncertainty
        sigma_q = quality_estimate.uncertainty
        sigma_a = adj.adjustment_uncertainty
        sigma_res = 0.05  # model parameterization residual uncertainty

        var_fair = (0.50 * (sigma_m ** 2)) + (0.30 * (sigma_q ** 2)) + (0.20 * (sigma_a ** 2)) + (sigma_res ** 2)
        valuation_uncertainty = round(min(0.95, math.sqrt(var_fair)), 3)
        confidence = round(max(0.05, 1.0 - valuation_uncertainty), 3)

        # 3. Base Fair Bounds
        base_min = p_market * (1.0 + markup_min_pct / 100.0) + adj.adjustment_per_kg
        base_max = p_market * (1.0 + markup_max_pct / 100.0) + adj.adjustment_per_kg
        base_mid = (base_min + base_max) / 2.0

        # 4. Uncertainty-Dependent Range Expansion
        # High uncertainty widens the interval; low uncertainty narrows it.
        expansion = base_mid * valuation_uncertainty * settings.UNCERTAINTY_RANGE_EXPANSION_FACTOR
        
        fair_min = round(max(1.0, base_min - expansion), 1)
        fair_max = round(base_max + expansion, 1)
        fair_mid = round((fair_min + fair_max) / 2.0, 1)

        # 5. Diagnostic Components & Explanation
        explanation = (
            f"Fair range ₹{fair_min}–₹{fair_max}/kg calculated from wholesale benchmark of "
            f"₹{p_market}/kg (uncertainty {sigma_m}), quality adjustment of ₹{adj.adjustment_per_kg}/kg "
            f"(visual uncertainty {sigma_q}), and compound valuation confidence of {int(confidence * 100)}%."
        )

        return ValuationResult(
            commodity=comm.capitalize(),
            fair_min=fair_min,
            fair_max=fair_max,
            fair_mid=fair_mid,
            valuation_uncertainty=valuation_uncertainty,
            confidence=confidence,
            quality_estimate=quality_estimate,
            market_estimate=market_estimate,
            quality_adjustment=adj,
            markup_range={"min_pct": markup_min_pct, "max_pct": markup_max_pct},
            components={
                "base_min_before_expansion": round(base_min, 1),
                "base_max_before_expansion": round(base_max, 1),
                "expansion_delta": round(expansion, 1),
                "market_uncertainty_contrib": round(sigma_m, 3),
                "quality_uncertainty_contrib": round(sigma_q, 3),
                "adjustment_uncertainty_contrib": round(sigma_a, 3),
            },
            explanation=explanation,
        )
