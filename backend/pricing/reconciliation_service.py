"""
Adaptive Community-Price Reconciliation Service for Sahi Daam.

Reconciles cost-based pricing baselines (wholesale + transport + markup + freshness)
with empirical community price observations using a robust, bounded adaptive weighting policy.

Guarantees:
- Pure, decoupled business logic.
- Baseline range is fully preserved alongside reconciled outputs.
- Provisional wholesale-based baseline is explicitly distinguished from transport-aware estimates.
- Minimum independent sample threshold (default: 10 reports) strictly enforced (alpha = 0 when threshold is not met).
- Flagged duplicates do not count toward the sample threshold.
- No arbitrary scientific certainty claims.
"""

from datetime import datetime, timezone, timedelta
import math
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field

from backend.services.community_service import (
    CommunityPriceService,
    WEIGHT_UNITS,
    COUNT_OR_BUNCH_UNITS,
)


class ReconciliationPolicy(BaseModel):
    """Configurable reconciliation policy parameters."""
    window_days: int = Field(default=2, description="Rolling observation window in days")
    min_sample_size: int = Field(default=10, description="Minimum independent reports required to activate reconciliation")
    base_alpha: float = Field(default=0.20, description="Initial weight at minimum sample threshold")
    alpha_per_additional_sample: float = Field(default=0.02, description="Weight increment per additional sample above minimum")
    max_alpha: float = Field(default=0.40, description="Maximum allowable community weight cap")
    markup_min_pct: float = Field(default=30.0, description="Retail minimum markup percentage")
    markup_max_pct: float = Field(default=45.0, description="Retail maximum markup percentage")


class EligibleObservationsBreakdown(BaseModel):
    """Detailed accounting of community observations considered for reconciliation."""
    total_found: int = 0
    eligible_count: int = 0
    excluded_duplicates_count: int = 0
    excluded_stale_count: int = 0
    excluded_non_weight_unit_count: int = 0
    excluded_invalid_count: int = 0
    eligible_prices: List[float] = Field(default_factory=list)
    community_median: Optional[float] = None
    community_mean: Optional[float] = None
    community_min: Optional[float] = None
    community_max: Optional[float] = None


class PriceRange(BaseModel):
    min: float
    max: float
    mid: float
    unit: str = "kg"


class ReconciliationResult(BaseModel):
    """Comprehensive, explainable output of baseline construction and reconciliation."""
    commodity_id: str
    locality_id: Optional[str] = None
    calculation_status: str  # TRANSPORT_AWARE_RECONCILED | TRANSPORT_AWARE_BASELINE | PROVISIONAL_WHOLESALE_RECONCILED | PROVISIONAL_WHOLESALE_BASELINE | UNAVAILABLE

    # Cost Basis Components
    wholesale_price_per_kg: Optional[float] = None
    transport_cost_per_kg: Optional[float] = None
    transport_status: str = "unavailable"  # available | unavailable | unattempted
    transport_method: Optional[str] = None
    cost_basis_per_kg: Optional[float] = None
    is_provisional_wholesale_only: bool = False

    # Markup & Freshness
    markup_min_pct: float = 30.0
    markup_max_pct: float = 45.0
    quality_adjustment: int = 0
    quality_adjustment_meaning: str = "No freshness deduction"

    # Baseline Range (always fully preserved)
    baseline_range: Optional[PriceRange] = None

    # Community Data & Weight
    community_sample_size: int = 0
    community_estimate: Optional[float] = None
    reconciliation_weight_alpha: float = 0.0
    is_sample_sufficient: bool = False

    # Final Reconciled Range
    reconciled_range: Optional[PriceRange] = None
    suggested_price: Optional[float] = None

    # Full Observation Breakdown & Auditing
    observation_breakdown: EligibleObservationsBreakdown = Field(default_factory=EligibleObservationsBreakdown)
    warnings: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class PricingReconciliationService:
    """Core domain service for cost basis construction and community reconciliation."""

    @classmethod
    def filter_eligible_observations(
        cls,
        observations: List[Any],
        window_days: int = 2,
        test_clock: Optional[datetime] = None,
    ) -> EligibleObservationsBreakdown:
        """
        Filter community observations according to strict eligibility rules:
        1. Observation must fall within the rolling observation window.
        2. Price must be positive and finite.
        3. Unit must be weight-normalized (kg, g, etc.). Non-weight units (piece, bunch) excluded.
        4. Flagged duplicates (is_duplicate=True) excluded from independent sample count.
        5. Valid unusual prices (outliers) are PRESERVED and included.
        """
        ref_time = test_clock or datetime.now(timezone.utc)
        window_start = ref_time - timedelta(days=window_days)

        breakdown = EligibleObservationsBreakdown(total_found=len(observations))
        valid_prices: List[float] = []

        for obs in observations:
            # Check price validity
            price = getattr(obs, "price", None)
            if price is None or math.isnan(price) or math.isinf(price) or price <= 0:
                breakdown.excluded_invalid_count += 1
                continue

            # Check timestamp window
            obs_time = getattr(obs, "observed_at", None)
            if obs_time is not None:
                if obs_time.tzinfo is None:
                    obs_time = obs_time.replace(tzinfo=timezone.utc)
                if obs_time < window_start:
                    breakdown.excluded_stale_count += 1
                    continue

            # Check duplicate status (flagged duplicates do not count toward independent sample)
            is_dup = getattr(obs, "is_duplicate", False)
            if is_dup:
                breakdown.excluded_duplicates_count += 1
                continue

            # Check unit & resolve normalized price per kg
            unit = getattr(obs, "unit", "kg").lower().strip()
            if unit in COUNT_OR_BUNCH_UNITS:
                # Do not blindly convert piece/bunch/count to kg
                breakdown.excluded_non_weight_unit_count += 1
                continue

            norm_price = getattr(obs, "normalized_price_per_kg", None)
            if norm_price is None:
                if unit in WEIGHT_UNITS:
                    factor = WEIGHT_UNITS[unit]
                    norm_price = round(price / factor, 2)
                else:
                    breakdown.excluded_invalid_count += 1
                    continue

            valid_prices.append(norm_price)

        breakdown.eligible_count = len(valid_prices)
        breakdown.eligible_prices = valid_prices

        if valid_prices:
            sorted_prices = sorted(valid_prices)
            n = len(sorted_prices)
            breakdown.community_median = (
                sorted_prices[n // 2]
                if n % 2 != 0
                else round((sorted_prices[n // 2 - 1] + sorted_prices[n // 2]) / 2.0, 2)
            )
            breakdown.community_mean = round(sum(sorted_prices) / n, 2)
            breakdown.community_min = sorted_prices[0]
            breakdown.community_max = sorted_prices[-1]

        return breakdown

    @classmethod
    def calculate_adaptive_alpha(
        cls,
        sample_size: int,
        policy: ReconciliationPolicy,
    ) -> Tuple[float, bool]:
        """
        Calculate provisional adaptive weight alpha:
        - alpha = 0.0 when sample_size < policy.min_sample_size (default 10).
        - alpha = min(max_alpha, base_alpha + step * (sample_size - min_sample_size)) when >= min_sample_size.
        """
        if sample_size < policy.min_sample_size:
            return 0.0, False

        additional_samples = sample_size - policy.min_sample_size
        alpha = policy.base_alpha + (policy.alpha_per_additional_sample * additional_samples)
        clamped_alpha = round(min(policy.max_alpha, max(0.0, alpha)), 4)
        return clamped_alpha, True

    @classmethod
    def reconcile(
        cls,
        commodity_id: str,
        wholesale_price: Optional[float],
        transport_cost: Optional[float] = None,
        transport_status: str = "unavailable",
        transport_method: Optional[str] = None,
        quality_adjustment: int = 0,
        quality_adjustment_meaning: str = "No freshness deduction",
        community_observations: Optional[List[Any]] = None,
        locality_id: Optional[str] = None,
        policy: Optional[ReconciliationPolicy] = None,
        test_clock: Optional[datetime] = None,
    ) -> ReconciliationResult:
        """
        Execute full cost-basis construction and community reconciliation.
        """
        pol = policy or ReconciliationPolicy()
        warnings: List[str] = []
        notes: List[str] = []

        # -------------------------------------------------------------------
        # Step 1: Check Wholesale Price Availability
        # -------------------------------------------------------------------
        if wholesale_price is None or math.isnan(wholesale_price) or wholesale_price <= 0:
            return ReconciliationResult(
                commodity_id=commodity_id,
                locality_id=locality_id,
                calculation_status="UNAVAILABLE",
                wholesale_price_per_kg=None,
                transport_cost_per_kg=None,
                transport_status="unavailable",
                cost_basis_per_kg=None,
                is_provisional_wholesale_only=False,
                markup_min_pct=pol.markup_min_pct,
                markup_max_pct=pol.markup_max_pct,
                quality_adjustment=quality_adjustment,
                quality_adjustment_meaning=quality_adjustment_meaning,
                warnings=["Wholesale price observation is missing or invalid; fair price cannot be fabricated."],
            )

        # -------------------------------------------------------------------
        # Step 2: Establish Cost Basis & Transport Status
        # -------------------------------------------------------------------
        has_valid_transport = (
            transport_status == "available"
            and transport_cost is not None
            and not math.isnan(transport_cost)
            and transport_cost >= 0
        )

        if has_valid_transport:
            cost_basis = wholesale_price + transport_cost
            effective_transport_status = "available"
            is_provisional = False
        else:
            cost_basis = wholesale_price
            effective_transport_status = "unavailable"
            is_provisional = True
            warnings.append(
                "Transport cost is unavailable or unconfigured; returning a provisional wholesale-based baseline."
            )

        # -------------------------------------------------------------------
        # Step 3: Construct Baseline Fair-Price Range
        # -------------------------------------------------------------------
        # Formula: cost_basis * (1 + markup) + quality_adjustment
        raw_min = cost_basis * (1.0 + pol.markup_min_pct / 100.0) + quality_adjustment
        baseline_min = round(max(0.0, raw_min), 2)

        raw_max = cost_basis * (1.0 + pol.markup_max_pct / 100.0) + quality_adjustment
        baseline_max = round(max(baseline_min, raw_max), 2)
        baseline_mid = round((baseline_min + baseline_max) / 2.0, 2)

        baseline_range = PriceRange(min=baseline_min, max=baseline_max, mid=baseline_mid)

        # -------------------------------------------------------------------
        # Step 4: Community Observations Evaluation
        # -------------------------------------------------------------------
        obs_breakdown = cls.filter_eligible_observations(
            observations=community_observations or [],
            window_days=pol.window_days,
            test_clock=test_clock,
        )

        alpha, is_sufficient = cls.calculate_adaptive_alpha(
            sample_size=obs_breakdown.eligible_count,
            policy=pol,
        )

        if not is_sufficient:
            notes.append(
                f"Community sample size ({obs_breakdown.eligible_count}) is below minimum threshold ({pol.min_sample_size}); "
                "reconciliation weight is 0.0."
            )
        else:
            notes.append(
                f"Sufficient community sample ({obs_breakdown.eligible_count} independent reports); "
                f"provisional adaptive weight alpha={alpha:.2f} applied."
            )

        # -------------------------------------------------------------------
        # Step 5: Adaptive Range Reconciliation
        # -------------------------------------------------------------------
        if alpha > 0.0 and obs_breakdown.community_median is not None:
            # Reconcile midpoint
            reconciled_mid = round(
                (1.0 - alpha) * baseline_mid + alpha * obs_breakdown.community_median, 2
            )
            delta = reconciled_mid - baseline_mid
            reconciled_min = round(max(0.0, baseline_min + delta), 2)
            reconciled_max = round(max(reconciled_min, baseline_max + delta), 2)

            reconciled_range = PriceRange(min=reconciled_min, max=reconciled_max, mid=reconciled_mid)
            suggested_price = reconciled_mid

            if is_provisional:
                calc_status = "PROVISIONAL_WHOLESALE_RECONCILED"
            else:
                calc_status = "TRANSPORT_AWARE_RECONCILED"
        else:
            # Alpha == 0: baseline remains the active reference
            reconciled_range = PriceRange(min=baseline_min, max=baseline_max, mid=baseline_mid)
            suggested_price = baseline_mid

            if is_provisional:
                calc_status = "PROVISIONAL_WHOLESALE_BASELINE"
            else:
                calc_status = "TRANSPORT_AWARE_BASELINE"

        return ReconciliationResult(
            commodity_id=commodity_id,
            locality_id=locality_id,
            calculation_status=calc_status,
            wholesale_price_per_kg=round(wholesale_price, 2),
            transport_cost_per_kg=round(transport_cost, 2) if has_valid_transport else None,
            transport_status=effective_transport_status,
            transport_method=transport_method if has_valid_transport else None,
            cost_basis_per_kg=round(cost_basis, 2),
            is_provisional_wholesale_only=is_provisional,
            markup_min_pct=pol.markup_min_pct,
            markup_max_pct=pol.markup_max_pct,
            quality_adjustment=quality_adjustment,
            quality_adjustment_meaning=quality_adjustment_meaning,
            baseline_range=baseline_range,
            community_sample_size=obs_breakdown.eligible_count,
            community_estimate=obs_breakdown.community_median,
            reconciliation_weight_alpha=alpha,
            is_sample_sufficient=is_sufficient,
            reconciled_range=reconciled_range,
            suggested_price=suggested_price,
            observation_breakdown=obs_breakdown,
            warnings=warnings,
            notes=notes,
        )

    @classmethod
    def reconcile_fair_price(
        cls,
        session: Any,
        commodity_id: str,
        wholesale_price: Optional[float],
        transport_result: Optional[Any] = None,
        locality_id: Optional[str] = None,
        quality_adjustment: int = 0,
        quality_adjustment_meaning: str = "No freshness deduction",
        policy: Optional[ReconciliationPolicy] = None,
        test_clock: Optional[datetime] = None,
    ) -> ReconciliationResult:
        """
        Database-backed convenience facade that loads community observations from SQLite
        and executes reconciliation.
        """
        from backend.database.repositories import CommunityPriceRepository

        observations = []
        if session is not None and locality_id:
            try:
                obs_list, _ = CommunityPriceRepository.query_observations(
                    session=session,
                    commodity_id=commodity_id,
                    locality_id=locality_id,
                    exclude_duplicates=False,
                    limit=100,
                )
                observations = obs_list
            except Exception:
                observations = []

        transport_cost = None
        transport_status = "unavailable"
        transport_method = None
        if transport_result is not None:
            transport_cost = getattr(transport_result, "cost_per_kg", None)
            stat = getattr(transport_result, "status", None)
            transport_status = stat.value if hasattr(stat, "value") else str(stat or "unavailable")
            meth = getattr(transport_result, "transport_method", None)
            transport_method = meth.value if hasattr(meth, "value") else str(meth or "")

        return cls.reconcile(
            commodity_id=commodity_id,
            wholesale_price=wholesale_price,
            transport_cost=transport_cost,
            transport_status=transport_status,
            transport_method=transport_method,
            quality_adjustment=quality_adjustment,
            quality_adjustment_meaning=quality_adjustment_meaning,
            community_observations=observations,
            locality_id=locality_id,
            policy=policy,
            test_clock=test_clock,
        )
