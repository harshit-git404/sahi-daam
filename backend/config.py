"""Centralized configuration for the Uncertainty-Driven Adaptive Valuation System.

All operational thresholds, reliability weights, and observation bounds are
defined here rather than scattered throughout the codebase.
"""

from pydantic import BaseModel, Field


class AdaptiveValuationConfig(BaseModel):
    # --- Quality & Uncertainty Thresholds ---
    MIN_QUALITY_CONFIDENCE: float = Field(
        default=0.75,
        description="Threshold below which quality confidence is considered low."
    )
    MAX_QUALITY_UNCERTAINTY: float = Field(
        default=0.40,
        description="Threshold above which quality is deemed excessively uncertain."
    )
    MAX_VALUATION_UNCERTAINTY: float = Field(
        default=0.35,
        description="Target maximum valuation uncertainty to finalize without additional observation."
    )

    # --- Active Observation & Value of Information (EVI) ---
    MAX_OBSERVATIONS: int = Field(
        default=3,
        description="Maximum number of active observations permitted per valuation session."
    )
    OBSERVATION_COST: float = Field(
        default=0.08,
        description="Normalized cost/burden incurred by requesting an additional user observation."
    )
    MIN_INFORMATION_GAIN_THRESHOLD: float = Field(
        default=0.05,
        description="Minimum net Expected Value of Information (EVI) required to request another observation."
    )
    BASE_EXPECTED_GAIN_SECOND_VIEW: float = Field(
        default=0.30,
        description="Estimated prior information gain from observing an uninspected side/view."
    )
    BASE_EXPECTED_GAIN_THIRD_VIEW: float = Field(
        default=0.15,
        description="Estimated prior information gain from a third visual inspection."
    )

    # --- Market Evidence Reliability Scoring Weights ---
    # Sum of weights should normalize to 1.0
    WEIGHT_RECENCY: float = Field(
        default=0.35,
        description="Weight given to data recency in market source reliability."
    )
    WEIGHT_GEOGRAPHY: float = Field(
        default=0.30,
        description="Weight given to geographic proximity/specificity (local vs regional)."
    )
    WEIGHT_SOURCE_TYPE: float = Field(
        default=0.20,
        description="Weight given to verified source authority (official APMC mandi vs proxy/snapshot)."
    )
    WEIGHT_CONSISTENCY: float = Field(
        default=0.15,
        description="Weight given to consistency with surrounding temporal/regional observations."
    )

    # --- Market Uncertainty Parameters ---
    MAX_ACCEPTABLE_DATA_AGE_HOURS: float = Field(
        default=72.0,
        description="Data older than this incurs maximum recency penalty."
    )
    DISAGREEMENT_PENALTY_SCALE: float = Field(
        default=1.5,
        description="Scaling factor for coefficient of variation across market sources."
    )

    # --- Valuation & Range Width Parameters ---
    MIN_RETAIL_MARKUP_PCT: float = Field(
        default=25.0,
        description="Baseline minimum local retail markup percentage."
    )
    MAX_RETAIL_MARKUP_PCT: float = Field(
        default=45.0,
        description="Baseline maximum local retail markup percentage."
    )
    UNCERTAINTY_RANGE_EXPANSION_FACTOR: float = Field(
        default=0.50,
        description="Degree to which fair price range widens in response to valuation uncertainty."
    )

    # --- Anomaly & Negotiation Thresholds ---
    SLIGHT_DEVIATION_THRESHOLD_PCT: float = Field(default=10.0)
    SIGNIFICANT_DEVIATION_THRESHOLD_PCT: float = Field(default=30.0)
    UNUSUALLY_CHEAP_QUALITY_THRESHOLD: float = Field(
        default=0.60,
        description="Quality score below which low prices trigger UNUSUALLY_CHEAP / CHECK_QUALITY warnings."
    )
    INSUFFICIENT_CONFIDENCE_THRESHOLD: float = Field(
        default=0.50,
        description="Valuation confidence below which binary OVERPRICED claims are withheld."
    )


# Global singleton configuration instance
settings = AdaptiveValuationConfig()
