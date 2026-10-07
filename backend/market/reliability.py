"""Market Source Reliability Scorer.

Evaluates evidence credibility across temporal recency, geographic specificity,
source authority, and mutual consistency.
"""

from typing import List
from config import settings
from core.schemas import MarketEvidenceRecord


class MarketReliabilityScorer:
    """Computes transparent, configurable reliability scores for market evidence."""

    def __init__(
        self,
        w_recency: float = settings.WEIGHT_RECENCY,
        w_geo: float = settings.WEIGHT_GEOGRAPHY,
        w_source: float = settings.WEIGHT_SOURCE_TYPE,
        w_consistency: float = settings.WEIGHT_CONSISTENCY,
    ):
        self.w_recency = w_recency
        self.w_geo = w_geo
        self.w_source = w_source
        self.w_consistency = w_consistency

    def score_evidence(self, records: List[MarketEvidenceRecord]) -> List[MarketEvidenceRecord]:
        """Scores each record in place and returns the updated list."""
        if not records:
            return []

        # Calculate average price for consistency comparison
        prices = [r.price_per_kg for r in records if r.price_per_kg > 0]
        mean_price = sum(prices) / len(prices) if prices else 1.0

        for r in records:
            # 1. Recency Score: decays with age in hours
            # 0 hrs -> 1.0; 24 hrs -> 0.76; 72 hrs -> 0.28
            hours = max(0.0, r.freshness_hours)
            recency_score = max(0.10, 1.0 - (hours / settings.MAX_ACCEPTABLE_DATA_AGE_HOURS))

            # 2. Geographic Relevance Score
            geo_term = r.distance_or_region.lower()
            if "local_exact" in geo_term:
                geo_score = 1.0
            elif "district" in geo_term:
                geo_score = 0.85
            elif "regional" in geo_term or "state" in geo_term:
                geo_score = 0.65
            elif "proxy" in geo_term:
                geo_score = 0.50
            else:
                geo_score = 0.40

            # 3. Source Authority Score
            source_lower = r.source.lower()
            if "agmarknet" in source_lower and r.is_live:
                source_score = 0.95
            elif "agmarknet" in source_lower:
                source_score = 0.75
            elif "quick-commerce" in source_lower:
                source_score = 0.60
            else:
                source_score = 0.45

            # 4. Consistency Score: divergence from group mean
            if mean_price > 0:
                rel_diff = abs(r.price_per_kg - mean_price) / mean_price
                consistency_score = max(0.20, 1.0 - min(1.0, rel_diff * 1.2))
            else:
                consistency_score = 0.50

            # Composite reliability weight
            reliability = (
                self.w_recency * recency_score
                + self.w_geo * geo_score
                + self.w_source * source_score
                + self.w_consistency * consistency_score
            )
            reliability = round(max(0.05, min(0.99, reliability)), 3)

            r.source_reliability = reliability
            r.uncertainty = round(1.0 - reliability, 3)

        return records
