"""
Transport-Cost Service for Sahi Daam.

Calculates the deterministic transport contribution in ₹/kg based on:
1. Vehicle and operating-cost mechanics (fuel consumption, fuel price, operating costs, effective load).
2. Explicitly configured transport rates (per-trip or per-kilogram) when vehicle parameters are unavailable.

Guarantees:
- Strictly deterministic calculation.
- Explicit status handling (available, estimated, unavailable).
- No invented or fabricated costs.
- Zero-division and invalid-input protection.
- Correct single accounting of trip direction (no double-counting return trips).
"""

from enum import Enum
import math
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class TripDirection(str, Enum):
    ONE_WAY = "one_way"
    ROUND_TRIP = "round_trip"


class CalculationStatus(str, Enum):
    AVAILABLE = "available"
    ESTIMATED = "estimated"
    UNAVAILABLE = "unavailable"


class TransportMethod(str, Enum):
    VEHICLE_OPERATING_COST = "vehicle_operating_cost"
    CONFIGURED_TRIP_RATE = "configured_trip_rate"
    CONFIGURED_PER_KG_RATE = "configured_per_kg_rate"


class TransportCalculationInput(BaseModel):
    """Structured input parameters for transport cost calculation."""

    # Route and distance inputs
    source_mandi_id: Optional[str] = None
    destination_locality_id: Optional[str] = None
    distance_km: Optional[float] = None
    distance_provenance: Optional[str] = None  # "verified", "configured", "user_entered", "unknown"
    trip_direction: TripDirection = TripDirection.ONE_WAY
    distance_is_round_trip: bool = False  # True if the provided distance_km is already round-trip

    # Vehicle-specific parameters
    vehicle_type: Optional[str] = None
    fuel_consumption_litres_per_km: Optional[float] = None
    fuel_economy_km_per_litre: Optional[float] = None  # Alternative specification (km/L)
    fuel_price_per_litre: Optional[float] = None
    base_rate_per_km: Optional[float] = 0.0
    driver_allowance: Optional[float] = 0.0
    loading_unloading_fee: Optional[float] = 0.0
    flat_fee: Optional[float] = 0.0
    other_operating_costs: Optional[float] = 0.0

    # Load parameters
    effective_load_kg: Optional[float] = None

    # Fallback rate configuration
    configured_trip_cost: Optional[float] = None
    configured_per_kg_rate: Optional[float] = None
    rate_provenance: Optional[str] = None

    # Metadata
    assumptions: List[str] = Field(default_factory=list)


class TransportCalculationResult(BaseModel):
    """Structured, deterministic result of transport cost calculation."""

    status: CalculationStatus
    transport_method: Optional[TransportMethod] = None
    cost_per_kg: Optional[float] = None
    total_trip_cost: Optional[float] = None
    distance_km: Optional[float] = None
    distance_traversed_km: Optional[float] = None
    trip_direction: TripDirection = TripDirection.ONE_WAY
    effective_load_kg: Optional[float] = None
    cost_breakdown: Optional[Dict[str, float]] = None
    input_units: Dict[str, str] = Field(
        default_factory=lambda: {
            "currency": "INR",
            "distance": "km",
            "load": "kg",
            "fuel_consumption": "litres_per_km",
            "fuel_price": "INR/litre",
            "cost_per_kg": "INR/kg",
        }
    )
    source: Optional[str] = None
    provenance: Optional[str] = None
    assumptions: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class TransportCostService:
    """Dedicated deterministic transport-cost calculation service."""

    @classmethod
    def calculate(cls, data: TransportCalculationInput) -> TransportCalculationResult:
        """
        Execute deterministic calculation following the prioritized evaluation flow:
        1. Validate numerical inputs for sanity and non-negativity.
        2. Attempt Vehicle / Operating-Cost calculation.
        3. Attempt Configured Transport Rate calculation (trip or per-kg rate).
        4. Return explicit UNAVAILABLE status with actionable warnings if inputs are insufficient.
        """
        warnings: List[str] = []
        assumptions: List[str] = list(data.assumptions)

        # -------------------------------------------------------------------
        # Step 1: Input Sanity & Validity Validation
        # -------------------------------------------------------------------
        validation_error = cls._validate_inputs(data)
        if validation_error:
            return TransportCalculationResult(
                status=CalculationStatus.UNAVAILABLE,
                trip_direction=data.trip_direction,
                effective_load_kg=data.effective_load_kg,
                warnings=[validation_error],
                assumptions=assumptions,
            )

        # -------------------------------------------------------------------
        # Step 2: Attempt Vehicle / Operating-Cost Calculation
        # -------------------------------------------------------------------
        vehicle_res = cls._calculate_vehicle_method(data, assumptions, warnings)
        if vehicle_res is not None:
            return vehicle_res

        # -------------------------------------------------------------------
        # Step 3: Attempt Configured Transport Rate Fallback
        # -------------------------------------------------------------------
        rate_res = cls._calculate_configured_rate_method(data, assumptions, warnings)
        if rate_res is not None:
            return rate_res

        # -------------------------------------------------------------------
        # Step 4: Neither Method Had Adequate Inputs -> Explicit UNAVAILABLE
        # -------------------------------------------------------------------
        if not warnings:
            warnings.append(
                "Insufficient transport inputs: neither vehicle parameters "
                "(distance, fuel/operating costs, load) nor configured transport "
                "rates (per-trip or per-kg) were adequately supplied."
            )

        return TransportCalculationResult(
            status=CalculationStatus.UNAVAILABLE,
            trip_direction=data.trip_direction,
            distance_km=data.distance_km,
            effective_load_kg=data.effective_load_kg,
            warnings=warnings,
            assumptions=assumptions,
        )

    # -----------------------------------------------------------------------
    # Internal Calculation Methods
    # -----------------------------------------------------------------------

    @classmethod
    def _validate_inputs(cls, data: TransportCalculationInput) -> Optional[str]:
        """Check for NaN, Inf, and invalid negative values."""
        numeric_fields = {
            "distance_km": data.distance_km,
            "fuel_consumption_litres_per_km": data.fuel_consumption_litres_per_km,
            "fuel_economy_km_per_litre": data.fuel_economy_km_per_litre,
            "fuel_price_per_litre": data.fuel_price_per_litre,
            "base_rate_per_km": data.base_rate_per_km,
            "driver_allowance": data.driver_allowance,
            "loading_unloading_fee": data.loading_unloading_fee,
            "flat_fee": data.flat_fee,
            "other_operating_costs": data.other_operating_costs,
            "effective_load_kg": data.effective_load_kg,
            "configured_trip_cost": data.configured_trip_cost,
            "configured_per_kg_rate": data.configured_per_kg_rate,
        }

        for name, val in numeric_fields.items():
            if val is not None:
                if math.isnan(val) or math.isinf(val):
                    return f"Invalid numeric value in '{name}': NaN or Infinite values are not permitted."
                if val < 0:
                    return f"Invalid numeric value in '{name}': negative values ({val}) are not permitted."

        return None

    @classmethod
    def _calculate_vehicle_method(
        cls,
        data: TransportCalculationInput,
        assumptions: List[str],
        warnings: List[str],
    ) -> Optional[TransportCalculationResult]:
        """Calculate transport cost using vehicle physics and operating costs."""
        # Check prerequisites
        if data.distance_km is None:
            # Cannot calculate vehicle method without distance
            return None

        # Resolve litres per km
        litres_per_km = data.fuel_consumption_litres_per_km
        if litres_per_km is None and data.fuel_economy_km_per_litre is not None:
            if data.fuel_economy_km_per_litre <= 0:
                warnings.append("Vehicle fuel economy must be greater than zero.")
                return None
            litres_per_km = 1.0 / data.fuel_economy_km_per_litre
            assumptions.append(
                f"Fuel consumption derived from economy ({data.fuel_economy_km_per_litre} km/L -> {litres_per_km:.4f} L/km)."
            )

        has_fuel_specs = (
            litres_per_km is not None and data.fuel_price_per_litre is not None
        )
        has_km_rate = (data.base_rate_per_km or 0.0) > 0.0
        has_fixed_costs = (
            (data.driver_allowance or 0.0)
            + (data.loading_unloading_fee or 0.0)
            + (data.flat_fee or 0.0)
            + (data.other_operating_costs or 0.0)
        ) > 0.0

        # We must have at least fuel specs OR km rate OR operating cost to proceed
        if not (has_fuel_specs or has_km_rate or has_fixed_costs):
            return None

        # Effective load check
        if data.effective_load_kg is None or data.effective_load_kg <= 0:
            warnings.append(
                f"Vehicle transport calculation requires a positive effective load, got {data.effective_load_kg}."
            )
            return None

        # Distance traversed calculation: account for trip direction exactly once
        base_distance = data.distance_km
        if data.trip_direction == TripDirection.ROUND_TRIP:
            if data.distance_is_round_trip:
                traversed_km = base_distance
                assumptions.append("Input distance is already specified as round-trip; not doubled.")
            else:
                traversed_km = base_distance * 2.0
                assumptions.append("Round-trip journey configured; one-way distance doubled.")
        else:
            if data.distance_is_round_trip:
                traversed_km = base_distance / 2.0
                assumptions.append("One-way journey configured from round-trip distance input.")
            else:
                traversed_km = base_distance

        # 1. Fuel cost
        if has_fuel_specs:
            fuel_cost = traversed_km * litres_per_km * data.fuel_price_per_litre
        else:
            fuel_cost = 0.0
            if not has_km_rate:
                warnings.append("Fuel price or consumption rate not configured; fuel cost evaluated as 0.")

        # 2. Distance operating cost (wear/maintenance/base km charge)
        km_operating_cost = traversed_km * (data.base_rate_per_km or 0.0)

        # 3. Fixed operating costs
        fixed_operating_costs = (
            (data.driver_allowance or 0.0)
            + (data.loading_unloading_fee or 0.0)
            + (data.flat_fee or 0.0)
            + (data.other_operating_costs or 0.0)
        )

        total_trip_cost = fuel_cost + km_operating_cost + fixed_operating_costs
        cost_per_kg = total_trip_cost / data.effective_load_kg

        # Determine status
        status = cls._determine_status(data.distance_provenance, is_estimated=False)

        cost_breakdown = {
            "fuel_cost": round(fuel_cost, 4),
            "km_operating_cost": round(km_operating_cost, 4),
            "fixed_operating_costs": round(fixed_operating_costs, 4),
            "total_allocated_trip_cost": round(total_trip_cost, 4),
            "effective_load_kg": data.effective_load_kg,
            "cost_per_kg": round(cost_per_kg, 4),
        }

        provenance = (
            f"vehicle_physics ({data.vehicle_type or 'unspecified_vehicle'}) | "
            f"distance_provenance: {data.distance_provenance or 'unspecified'}"
        )

        return TransportCalculationResult(
            status=status,
            transport_method=TransportMethod.VEHICLE_OPERATING_COST,
            cost_per_kg=round(cost_per_kg, 2),
            total_trip_cost=round(total_trip_cost, 2),
            distance_km=round(base_distance, 2),
            distance_traversed_km=round(traversed_km, 2),
            trip_direction=data.trip_direction,
            effective_load_kg=data.effective_load_kg,
            cost_breakdown=cost_breakdown,
            source=data.vehicle_type or "vehicle_profile",
            provenance=provenance,
            assumptions=assumptions,
            warnings=warnings,
        )

    @classmethod
    def _calculate_configured_rate_method(
        cls,
        data: TransportCalculationInput,
        assumptions: List[str],
        warnings: List[str],
    ) -> Optional[TransportCalculationResult]:
        """Calculate transport cost using configured per-trip or per-kilogram rates."""
        # 1. Configured flat per-trip rate
        if data.configured_trip_cost is not None:
            if data.effective_load_kg is None or data.effective_load_kg <= 0:
                warnings.append(
                    "Configured trip cost was provided, but effective load is missing or non-positive; "
                    "cannot allocate per-kilogram cost."
                )
                return None

            total_cost = data.configured_trip_cost
            cost_per_kg = total_cost / data.effective_load_kg
            status = cls._determine_status(data.rate_provenance, is_estimated=False)

            cost_breakdown = {
                "total_allocated_trip_cost": round(total_cost, 4),
                "effective_load_kg": data.effective_load_kg,
                "cost_per_kg": round(cost_per_kg, 4),
            }

            return TransportCalculationResult(
                status=status,
                transport_method=TransportMethod.CONFIGURED_TRIP_RATE,
                cost_per_kg=round(cost_per_kg, 2),
                total_trip_cost=round(total_cost, 2),
                distance_km=data.distance_km,
                distance_traversed_km=data.distance_km,
                trip_direction=data.trip_direction,
                effective_load_kg=data.effective_load_kg,
                cost_breakdown=cost_breakdown,
                source="configured_trip_rate",
                provenance=data.rate_provenance or "configured_benchmark",
                assumptions=assumptions,
                warnings=warnings,
            )

        # 2. Configured direct per-kilogram rate
        if data.configured_per_kg_rate is not None:
            cost_per_kg = data.configured_per_kg_rate
            total_trip_cost = (
                round(cost_per_kg * data.effective_load_kg, 2)
                if data.effective_load_kg and data.effective_load_kg > 0
                else None
            )
            status = cls._determine_status(data.rate_provenance, is_estimated=False)

            cost_breakdown = {
                "cost_per_kg": round(cost_per_kg, 4),
            }
            if total_trip_cost is not None:
                cost_breakdown["total_allocated_trip_cost"] = round(total_trip_cost, 4)
                cost_breakdown["effective_load_kg"] = data.effective_load_kg

            return TransportCalculationResult(
                status=status,
                transport_method=TransportMethod.CONFIGURED_PER_KG_RATE,
                cost_per_kg=round(cost_per_kg, 2),
                total_trip_cost=total_trip_cost,
                distance_km=data.distance_km,
                trip_direction=data.trip_direction,
                effective_load_kg=data.effective_load_kg,
                cost_breakdown=cost_breakdown,
                source="configured_per_kg_rate",
                provenance=data.rate_provenance or "configured_rate_schedule",
                assumptions=assumptions,
                warnings=warnings,
            )

        return None

    @classmethod
    def _determine_status(
        cls,
        provenance: Optional[str],
        is_estimated: bool = False,
    ) -> CalculationStatus:
        """Assign available vs estimated based on provenance quality."""
        if is_estimated:
            return CalculationStatus.ESTIMATED
        if not provenance:
            return CalculationStatus.ESTIMATED
        prov_lower = provenance.lower()
        if "verified" in prov_lower or "configured" in prov_lower or "benchmark" in prov_lower:
            return CalculationStatus.AVAILABLE
        return CalculationStatus.ESTIMATED

    # -----------------------------------------------------------------------
    # Database Integration Helper (Optional convenience)
    # -----------------------------------------------------------------------

    @classmethod
    def calculate_from_database_profile(
        cls,
        session: Any,
        vehicle_type: str,
        mandi_id: Optional[str] = None,
        distance_km: Optional[float] = None,
        effective_load_kg: Optional[float] = None,
        trip_direction: TripDirection = TripDirection.ONE_WAY,
    ) -> TransportCalculationResult:
        """
        Convenience builder resolving parameters from database models (TransportConfiguration and Mandi).
        Keeps SQL out of calculation formulas.
        """
        from backend.database.repositories import TransportConfigRepository, MandiRepository

        config = TransportConfigRepository.get_by_vehicle_type(session, vehicle_type)
        if not config:
            return TransportCalculationResult(
                status=CalculationStatus.UNAVAILABLE,
                trip_direction=trip_direction,
                warnings=[f"No active transport configuration found for vehicle type '{vehicle_type}'."],
            )

        # Resolve distance if not provided
        resolved_distance = distance_km
        distance_prov = "user_entered" if distance_km is not None else "unknown"
        if resolved_distance is None and mandi_id:
            mandi = MandiRepository.get_by_id(session, mandi_id)
            if mandi and mandi.distance_km_reference:
                resolved_distance = mandi.distance_km_reference
                distance_prov = "configured"

        # Resolve load
        resolved_load = effective_load_kg or config.effective_load_kg or config.capacity_kg

        input_data = TransportCalculationInput(
            source_mandi_id=mandi_id,
            distance_km=resolved_distance,
            distance_provenance=distance_prov,
            trip_direction=trip_direction,
            vehicle_type=config.vehicle_type,
            fuel_economy_km_per_litre=config.fuel_consumption_km_per_l,
            fuel_price_per_litre=config.fuel_price_per_l,
            base_rate_per_km=config.base_rate_per_km,
            driver_allowance=config.driver_allowance,
            loading_unloading_fee=config.loading_unloading_fee,
            flat_fee=config.flat_fee,
            effective_load_kg=resolved_load,
        )

        return cls.calculate(input_data)
