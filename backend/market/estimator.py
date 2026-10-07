"""Weighted Market Price Estimator.

Fuses multi-source market evidence into a consolidated wholesale price benchmark
and computes explicit market uncertainty reflecting source agreement, age, and coverage.
"""

import math
from typing import List
from config import settings
from core.schemas import MarketEvidenceRecord, WeightedMarketPriceEstimate
from market.reliability import MarketReliabilityScorer


class WeightedMarketPriceEstimator:
    """Combines scored market evidence into a reliability-weighted benchmark."""

    def __init__(self, scorer: MarketReliabilityScorer = None):
        self.scorer = scorer or MarketReliabilityScorer()

    def estimate_market_price(
        self,
        records: List[MarketEvidenceRecord],
        commodity: str = "tomato"
    ) -> WeightedMarketPriceEstimate:
        if not records:
            return WeightedMarketPriceEstimate(
                commodity=commodity,
                estimated_price_per_kg=22.0,
                market_uncertainty=0.85,
                confidence=0.15,
                evidence_count=0,
                sources=["None"],
                weights={},
                evidence_records=[],
            )

        # Ensure records are scored
        scored_records = self.scorer.score_evidence(records)

        # Filter positive prices
        valid_records = [r for r in scored_records if r.price_per_kg > 0]
        if not valid_records:
            return WeightedMarketPriceEstimate(
                commodity=commodity,
                estimated_price_per_kg=22.0,
                market_uncertainty=0.80,
                confidence=0.20,
                evidence_count=0,
                sources=["None"],
                weights={},
                evidence_records=[],
            )

        total_weight = sum(r.source_reliability for r in valid_records)
        if total_weight <= 0:
            total_weight = 1.0

        # Weighted Mean Price: Σ(w_i * P_i) / Σ(w_i)
        weighted_sum = sum(r.source_reliability * r.price_per_kg for r in valid_records)
        weighted_price = round(weighted_sum / total_weight, 2)

        # Compute Dispersion / Source Disagreement
        # Weighted variance: Σ w_i * (P_i - P_hat)^2 / Σ w_i
        weighted_sq_diff = sum(
            r.source_reliability * ((r.price_per_kg - weighted_price) ** 2)
            for r in valid_records
        )
        weighted_var = weighted_sq_diff / total_weight
        weighted_std = math.sqrt(weighted_var)

        # Coefficient of variation (dispersion relative to price level)
        cv = (weighted_std / weighted_price) if weighted_price > 0 else 0.5
        disagreement_penalty = min(0.60, cv * settings.DISAGREEMENT_PENALTY_SCALE)

        # Average age penalty
        avg_age_hours = sum(r.freshness_hours for r in valid_records) / len(valid_records)
        age_penalty = min(0.35, (avg_age_hours / settings.MAX_ACCEPTABLE_DATA_AGE_HOURS) * 0.35)

        # Sparsity penalty (fewer observations increase uncertainty)
        if len(valid_records) == 1:
            sparsity_penalty = 0.30
        elif len(valid_records) == 2:
            sparsity_penalty = 0.15
        elif len(valid_records) >= 5:
            sparsity_penalty = 0.02
        else:
            sparsity_penalty = 0.08

        # Compound Market Uncertainty
        # Multiple strong sources in close agreement yield low uncertainty (~0.10)
        # High disagreement or single old source yields high uncertainty (~0.60-0.85)
        raw_market_unc = 0.08 + disagreement_penalty + age_penalty + sparsity_penalty
        market_uncertainty = round(max(0.08, min(0.95, raw_market_unc)), 3)
        confidence = round(1.0 - market_uncertainty, 3)

        source_names = list(set(r.source for r in valid_records))
        weights_dict = {r.evidence_id: round(r.source_reliability, 3) for r in valid_records}

        return WeightedMarketPriceEstimate(
            commodity=commodity,
            estimated_price_per_kg=weighted_price,
            market_uncertainty=market_uncertainty,
            confidence=confidence,
            evidence_count=len(valid_records),
            sources=source_names,
            weights=weights_dict,
            evidence_records=valid_records,
        )
