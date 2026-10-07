"""Core schemas for the Uncertainty-Driven Adaptive Valuation System."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ObservationView(str, Enum):
    FRONT = "front"
    REVERSE_SIDE = "reverse_side"
    CLOSE_UP = "close_up"
    DAMAGE_FOCUS = "damage_focus"
    OVERVIEW = "overview"
    UNKNOWN = "unknown"


class ControllerAction(str, Enum):
    ACQUIRE_ADDITIONAL_OBSERVATION = "ACQUIRE_ADDITIONAL_OBSERVATION"
    FINALIZE_VALUATION = "FINALIZE_VALUATION"


class AnomalyState(str, Enum):
    FAIR_PRICE = "FAIR_PRICE"
    SLIGHTLY_HIGH = "SLIGHTLY_HIGH"
    OVERPRICED = "OVERPRICED"
    GOOD_DEAL = "GOOD_DEAL"
    UNUSUALLY_CHEAP = "UNUSUALLY_CHEAP"
    CHECK_QUALITY = "CHECK_QUALITY"
    INSUFFICIENT_CONFIDENCE = "INSUFFICIENT_CONFIDENCE"


class SeverityLevel(str, Enum):
    NONE = "NONE"
    SLIGHT = "SLIGHT"
    MODERATE = "MODERATE"
    SIGNIFICANT = "SIGNIFICANT"
    UNCERTAIN = "UNCERTAIN"


# ---------------------------------------------------------------------------
# Observation & Input Models
# ---------------------------------------------------------------------------

class Observation(BaseModel):
    observation_id: str
    observation_index: int = 1
    image_b64: Optional[str] = None
    view: ObservationView = ObservationView.FRONT
    timestamp: str
    image_quality_score: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Assessed clarity/sharpness of the captured image."
    )
    lighting_score: float = Field(
        default=0.80,
        ge=0.0,
        le=1.0,
        description="Assessed adequacy of lighting in the image."
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ObservationRequest(BaseModel):
    reason: str
    requested_view: str
    priority: float = Field(ge=0.0, le=1.0)
    expected_information_gain: float = Field(ge=0.0, le=1.0)
    user_guidance: str


# ---------------------------------------------------------------------------
# Quality & Uncertainty Estimation Models
# ---------------------------------------------------------------------------

class QualityEstimate(BaseModel):
    commodity: str
    quality_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall quality index where 1.0 is pristine and 0.0 is severely spoiled."
    )
    freshness_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Freshness metric (0.0=rotten, 1.0=just-harvested/prime)."
    )
    quality_class: str = Field(description="Qualitative label: Fresh, Slightly Aged, Overripe, etc.")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Statistical confidence in this quality estimation."
    )
    uncertainty: float = Field(
        ge=0.0,
        le=1.0,
        description="Estimated epistemic and aleatoric uncertainty (NOT merely 1 - confidence)."
    )
    observations_used: List[str] = Field(
        default_factory=list,
        description="List of observation IDs fused to produce this estimate."
    )
    freshness_percent: int = Field(default=85, ge=0, le=100)
    freshness_note: str = ""
    quality_adjustment_suggested: float = 0.0
    quality_adjustment_label: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Market Evidence & Reliability Models
# ---------------------------------------------------------------------------

class MarketEvidenceRecord(BaseModel):
    evidence_id: str
    source: str
    commodity: str
    market: str
    state: str
    price_per_kg: float
    timestamp: str
    distance_or_region: str = "local"
    freshness_hours: float = 0.0
    source_reliability: float = Field(default=0.8, ge=0.0, le=1.0)
    uncertainty: float = Field(default=0.2, ge=0.0, le=1.0)
    is_live: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WeightedMarketPriceEstimate(BaseModel):
    commodity: str
    estimated_price_per_kg: float
    market_uncertainty: float = Field(
        ge=0.0,
        le=1.0,
        description="Aggregated uncertainty of the market benchmark reflecting source divergence and age."
    )
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_count: int
    sources: List[str]
    weights: Dict[str, float]
    evidence_records: List[MarketEvidenceRecord] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Quality-Price Adjustment & Valuation Models
# ---------------------------------------------------------------------------

class QualityPriceAdjustment(BaseModel):
    commodity: str
    base_market_price: float
    adjustment_per_kg: float
    adjustment_uncertainty: float = Field(ge=0.0, le=1.0)
    method: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


class FairPriceRange(BaseModel):
    min: float
    max: float
    unit: str = "kg"


class ValuationResult(BaseModel):
    commodity: str
    fair_min: float
    fair_max: float
    fair_mid: float
    valuation_uncertainty: float = Field(
        ge=0.0,
        le=1.0,
        description="Propagated compound uncertainty across market, quality, and markup models."
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Composite valuation confidence rating."
    )
    quality_estimate: QualityEstimate
    market_estimate: WeightedMarketPriceEstimate
    quality_adjustment: QualityPriceAdjustment
    markup_range: Dict[str, float]
    components: Dict[str, Any] = Field(default_factory=dict)
    explanation: str


# ---------------------------------------------------------------------------
# Controller Decision Models
# ---------------------------------------------------------------------------

class ControllerDecision(BaseModel):
    decision: ControllerAction
    reason: str
    current_uncertainty: float
    expected_value_of_information: float
    estimated_observation_cost: float
    threshold: float
    observation_request: Optional[ObservationRequest] = None


# ---------------------------------------------------------------------------
# Valuation Session Model (Preserving History Across Iterations)
# ---------------------------------------------------------------------------

class ValuationSession(BaseModel):
    session_id: str
    commodity: str
    status: str = "ACTIVE"
    observation_count: int = 0
    max_observations: int = 3
    observations: List[Observation] = Field(default_factory=list)
    quality_history: List[QualityEstimate] = Field(default_factory=list)
    valuation_history: List[ValuationResult] = Field(default_factory=list)
    controller_history: List[ControllerDecision] = Field(default_factory=list)
    current_quality_estimate: Optional[QualityEstimate] = None
    current_quality_uncertainty: float = 0.0
    current_market_estimate: Optional[WeightedMarketPriceEstimate] = None
    current_market_uncertainty: float = 0.0
    current_valuation: Optional[ValuationResult] = None
    current_fair_range: Optional[FairPriceRange] = None
    current_valuation_uncertainty: float = 0.0
    latest_decision: Optional[ControllerDecision] = None
    decision_trace: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Anomaly Detection & Negotiation Models
# ---------------------------------------------------------------------------

class NegotiationStrategy(BaseModel):
    starting_offer: float
    target_price: float
    maximum_reasonable_price: float
    potential_saving: float = 0.0
    below_fair_amount: float = 0.0
    confidence_caution: Optional[str] = None


class AnomalyAnalysisResult(BaseModel):
    decision: AnomalyState
    severity: SeverityLevel
    deviation_pct: float
    is_confidence_sufficient: bool
    asking_price: float
    fair_min: float
    fair_max: float
    strategy: NegotiationStrategy
    recommendation_action: str
    recommendation_headline: str
    recommendation_explanation: str
    reasoning: str
    quality_caution: Optional[str] = None
