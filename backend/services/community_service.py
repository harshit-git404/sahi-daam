"""
Community-Price Service for Sahi Daam.

Handles:
1. Validation of community price submissions (commodity, locality, positive price, units).
2. Normalization of prices to ₹/kg where unit conversion is valid (avoiding blind conversion for count/bunch items).
3. Conservative duplicate detection without rejecting or deleting submissions.
4. Observation temporal windowing and transparent outlier tracking.
"""

from datetime import datetime, timezone, timedelta
import math
import re
import uuid
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.orm import Session

from backend.database.models import CommunityPriceObservation, Locality
from backend.database.repositories import CommunityPriceRepository, LocalityRepository
from backend.database.schemas import (
    CommunityPriceSubmission,
    CommunityPriceSubmissionResponse,
    CommunityPriceObservationRead,
    CommunityPriceListResponse,
)

# Standard supported commodity identifiers and canonical aliases
CANONICAL_COMMODITIES = {
    "tomato": ["tomato", "tamatar", "thakkali"],
    "potato": ["potato", "aloo", "alu"],
    "onion": ["onion", "onions", "pyaz", "pyaaz", "vengayam"],
    "carrot": ["carrot", "carrots", "gajar"],
    "cucumber": ["cucumber", "cucumbers", "kheera", "vellarikka"],
    "brinjal": ["brinjal", "eggplant", "baingan", "aubergine", "kathirikai"],
    "cauliflower": ["cauliflower", "gobi", "gobhi"],
    "cabbage": ["cabbage", "patta gobi", "patta gobhi", "muttakose"],
    "banana": ["banana", "bananas", "kela", "vazhaipazham"],
    "papaya": ["papaya", "papita", "pappali"],
    "apple": ["apple", "apples", "seb", "aappil"],
    "mango": ["mango", "mangoes", "aam", "mambazham"],
    "lemon": ["lemon", "lemons", "nimbu", "elumichai"],
    "capsicum": ["capsicum", "bell pepper", "shimla mirch", "kudaikaai"],
    "lady_finger": ["lady finger", "ladyfinger", "okra", "bhindi", "vendakkai"],
    "spinach": ["spinach", "palak", "keerai"],
    "dragonfruit": ["dragonfruit", "dragon fruit"],
}

# Lookup map from alias to canonical commodity_id
ALIAS_TO_COMMODITY: Dict[str, str] = {}
for canonical, aliases in CANONICAL_COMMODITIES.items():
    ALIAS_TO_COMMODITY[canonical] = canonical
    for a in aliases:
        ALIAS_TO_COMMODITY[a.lower().replace(" ", "_").replace("-", "_")] = canonical
        ALIAS_TO_COMMODITY[a.lower()] = canonical

# Explicitly supported units
WEIGHT_UNITS = {
    "kg": 1.0,
    "kgs": 1.0,
    "kilogram": 1.0,
    "kilograms": 1.0,
    "g": 0.001,
    "gm": 0.001,
    "gms": 0.001,
    "gram": 0.001,
    "grams": 0.001,
    "500g": 0.5,
    "500gm": 0.5,
    "500 gm": 0.5,
    "250g": 0.25,
    "250gm": 0.25,
    "250 gm": 0.25,
    "100g": 0.1,
    "100gm": 0.1,
    "100 gm": 0.1,
}

COUNT_OR_BUNCH_UNITS = {
    "piece",
    "item",
    "count",
    "pc",
    "pcs",
    "dozen",
    "half_dozen",
    "bunch",
    "bundle",  # leaf bundle
    "kattu",
}

AMBIGUOUS_UNITS = {
    "box",
    "bag",
    "packet",
    "basket",
    "crate",
    "carton",
    "sack",
}


class CommunityPriceService:
    """Core domain service for community-sourced price submissions and queries."""

    # -----------------------------------------------------------------------
    # 1. Validation & Normalization Helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def normalize_commodity_id(raw_commodity: str) -> str:
        """Resolve produce aliases to canonical commodity IDs."""
        cleaned = raw_commodity.strip().lower().replace(" ", "_").replace("-", "_")
        if cleaned in ALIAS_TO_COMMODITY:
            return ALIAS_TO_COMMODITY[cleaned]
        # Check raw lowercase
        lower_raw = raw_commodity.strip().lower()
        if lower_raw in ALIAS_TO_COMMODITY:
            return ALIAS_TO_COMMODITY[lower_raw]
        raise ValueError(f"Unsupported or unknown commodity: '{raw_commodity}'.")

    @staticmethod
    def validate_and_normalize_unit(commodity_id: str, price: float, raw_unit: str) -> Tuple[str, Optional[float]]:
        """
        Validate unit and normalize to ₹/kg where dimensionally valid.
        Returns:
            (canonical_unit, normalized_price_per_kg)
        """
        unit_lower = raw_unit.strip().lower()

        # 1. Reject ambiguous units
        if unit_lower in AMBIGUOUS_UNITS:
            raise ValueError(
                f"Ambiguous unit '{raw_unit}' is not accepted because its mass/count is unspecified. "
                "Please specify price in kg, g, 500g, piece, dozen, or bunch."
            )

        # 2. Check weight units -> calculate normalized price per kg
        if unit_lower in WEIGHT_UNITS:
            factor = WEIGHT_UNITS[unit_lower]
            canonical_unit = "kg" if factor == 1.0 else unit_lower
            price_per_kg = round(price / factor, 2)
            return canonical_unit, price_per_kg

        # 3. Check count / bunch units -> do NOT convert blindly to kg!
        if unit_lower in COUNT_OR_BUNCH_UNITS:
            # Special handling for dozen: normalize to piece if desirable or retain unit
            return unit_lower, None

        raise ValueError(
            f"Unsupported unit: '{raw_unit}'. Supported units include: "
            "kg, g, 500g, 250g, 100g, piece, dozen, bunch."
        )

    # -----------------------------------------------------------------------
    # 2. Submission Processing
    # -----------------------------------------------------------------------

    @classmethod
    def process_submission(
        cls,
        session: Session,
        submission: CommunityPriceSubmission,
        test_clock: Optional[datetime] = None,
    ) -> CommunityPriceSubmissionResponse:
        """
        Validate, normalize, check duplicates, and persist a community price observation.
        """
        warnings: List[str] = []

        # 1. Validate Price
        price = submission.price
        if price is None or math.isnan(price) or math.isinf(price) or price <= 0:
            raise ValueError(f"Price must be a positive finite number, got {price}.")

        # 2. Validate Commodity
        canonical_commodity = cls.normalize_commodity_id(submission.commodity_id)

        # 3. Validate Unit & Normalization
        canonical_unit, normalized_price_per_kg = cls.validate_and_normalize_unit(
            canonical_commodity, price, submission.unit
        )

        # 4. Validate Source Type
        source_type = submission.source_type.strip().lower()
        if source_type not in ("customer", "vendor"):
            raise ValueError(f"Invalid source_type '{submission.source_type}'. Must be 'customer' or 'vendor'.")

        # 5. Resolve Locality
        locality_id = submission.locality_id
        if locality_id:
            locality = LocalityRepository.get_by_id(session, locality_id)
            if not locality:
                raise ValueError(f"Locality with ID '{locality_id}' not found.")
        elif submission.locality_name:
            # On-the-fly locality resolution / creation
            slug = submission.locality_name.strip().lower().replace(" ", "_")
            loc_id = f"loc_{slug}"
            locality = LocalityRepository.get_by_id(session, loc_id)
            if not locality:
                locality = LocalityRepository.upsert(
                    session,
                    {
                        "id": loc_id,
                        "name": submission.locality_name.strip().title(),
                        "district": submission.district or "Vellore",
                        "state": submission.state or "Tamil Nadu",
                        "pincode": submission.pincode,
                    },
                )
            locality_id = locality.id
        else:
            raise ValueError("Either 'locality_id' or 'locality_name' must be provided.")

        # 6. Validate Observation Timestamp
        now_utc = test_clock or datetime.now(timezone.utc)
        observed_at = submission.observed_at
        if observed_at is None:
            observed_at = now_utc
        elif observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)

        # Disallow timestamps in the future beyond 2 hours clock skew
        if observed_at > now_utc + timedelta(hours=2):
            raise ValueError(
                f"Observation timestamp ({observed_at.isoformat()}) cannot be in the future relative to server time ({now_utc.isoformat()})."
            )

        # 7. Conservative Duplicate Detection
        dup_match = CommunityPriceRepository.find_potential_duplicate(
            session=session,
            commodity_id=canonical_commodity,
            locality_id=locality_id,
            price=price,
            unit=canonical_unit,
            observed_at=observed_at,
            contributor_id=submission.contributor_id,
            source_type=source_type,
            time_window_hours=12,
        )

        is_dup = False
        duplicate_of_id = None
        duplicate_reason = None

        if dup_match:
            is_dup = True
            duplicate_of_id = dup_match.id
            duplicate_reason = (
                f"Matches existing observation {dup_match.id} with identical price "
                f"(₹{price}/{canonical_unit}) and contributor/source within 12h window."
            )
            warnings.append(
                f"Notice: This report was flagged as a probable duplicate of {dup_match.id}. "
                "It is preserved in the database but excluded from non-duplicate sample aggregations."
            )

        # 8. Outlier Warning Check (Informational, does not reject)
        if normalized_price_per_kg is not None:
            if normalized_price_per_kg > 150.0 or normalized_price_per_kg < 5.0:
                warnings.append(
                    f"Notice: Price of ₹{normalized_price_per_kg:.2f}/kg is unusual for {canonical_commodity}, "
                    "but has been successfully recorded."
                )

        # 9. Persist Original Observation
        obs_id = f"cpo_{uuid.uuid4().hex[:12]}"
        provenance = submission.provenance or "community_submission"

        obs_record = CommunityPriceRepository.create(
            session=session,
            data={
                "id": obs_id,
                "commodity_id": canonical_commodity,
                "price": price,
                "unit": canonical_unit,
                "locality_id": locality_id,
                "source_type": source_type,
                "contributor_id": submission.contributor_id or f"anon_{uuid.uuid4().hex[:8]}",
                "observed_at": observed_at,
                "provenance": provenance,
                "is_duplicate": is_dup,
                "duplicate_of_id": duplicate_of_id,
                "duplicate_reason": duplicate_reason,
                "normalized_price_per_kg": normalized_price_per_kg,
            },
        )

        return CommunityPriceSubmissionResponse(
            status="recorded",
            observation=CommunityPriceObservationRead.model_validate(obs_record),
            is_duplicate=is_dup,
            duplicate_of_id=duplicate_of_id,
            duplicate_reason=duplicate_reason,
            normalized_price_per_kg=normalized_price_per_kg,
            warnings=warnings,
        )

    # -----------------------------------------------------------------------
    # 3. Retrieval & Summary Workflow
    # -----------------------------------------------------------------------

    @classmethod
    def list_observations(
        cls,
        session: Session,
        commodity_id: Optional[str] = None,
        locality_id: Optional[str] = None,
        source_type: Optional[str] = None,
        window_days: Optional[int] = 2,  # Configurable 2-day demo window default
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        exclude_duplicates: bool = True,
        limit: int = 50,
        offset: int = 0,
        test_clock: Optional[datetime] = None,
    ) -> CommunityPriceListResponse:
        """
        Query community observations with safe pagination, duplicate handling, and summary statistics.
        """
        # Normalize commodity if passed
        resolved_commodity = None
        if commodity_id:
            try:
                resolved_commodity = cls.normalize_commodity_id(commodity_id)
            except ValueError:
                resolved_commodity = commodity_id.strip().lower()

        # Compute effective window
        ref_time = test_clock or datetime.now(timezone.utc)
        effective_since = since
        if effective_since is None and window_days is not None and window_days > 0:
            effective_since = ref_time - timedelta(days=window_days)

        # Enforce safe pagination limit (max 100)
        safe_limit = min(max(1, limit), 100)
        safe_offset = max(0, offset)

        items, total_count = CommunityPriceRepository.query_observations(
            session=session,
            commodity_id=resolved_commodity,
            locality_id=locality_id,
            source_type=source_type,
            since=effective_since,
            until=until,
            exclude_duplicates=exclude_duplicates,
            limit=safe_limit,
            offset=safe_offset,
        )

        # Compute summary metrics on retrieved dataset
        summary = cls._compute_summary(items)

        # Convert to Pydantic read models with outlier flags
        read_items = []
        for item in items:
            read_model = CommunityPriceObservationRead.model_validate(item)
            effective_price = (
                item.normalized_price_per_kg
                if item.normalized_price_per_kg is not None
                else item.price
            )
            # Evaluate outlier flag against median
            if summary.get("median_price") is not None and effective_price is not None:
                median = summary["median_price"]
                deviation = abs(effective_price - median) / median if median > 0 else 0
                if deviation > 1.0:  # > 100% deviation from median
                    read_model.is_outlier = True
            read_items.append(read_model)

        return CommunityPriceListResponse(
            total_count=total_count,
            window_days=window_days,
            items=read_items,
            summary=summary,
        )

    @staticmethod
    def _compute_summary(items: List[CommunityPriceObservation]) -> Dict[str, Any]:
        """Compute statistical summary on observations."""
        if not items:
            return {
                "sample_count": 0,
                "average_price": None,
                "median_price": None,
                "min_price": None,
                "max_price": None,
                "duplicate_count": 0,
            }

        # Filter effective normalized prices (fallback to raw price if unit is kg or same)
        prices = [
            (i.normalized_price_per_kg if i.normalized_price_per_kg is not None else i.price)
            for i in items
            if not i.is_duplicate
        ]

        dup_count = sum(1 for i in items if i.is_duplicate)

        if not prices:
            return {
                "sample_count": 0,
                "average_price": None,
                "median_price": None,
                "min_price": None,
                "max_price": None,
                "duplicate_count": dup_count,
            }

        prices_sorted = sorted(prices)
        n = len(prices_sorted)
        avg = sum(prices_sorted) / n
        median = (
            prices_sorted[n // 2]
            if n % 2 != 0
            else (prices_sorted[n // 2 - 1] + prices_sorted[n // 2]) / 2.0
        )

        return {
            "sample_count": n,
            "average_price": round(avg, 2),
            "median_price": round(median, 2),
            "min_price": round(prices_sorted[0], 2),
            "max_price": round(prices_sorted[-1], 2),
            "duplicate_count": dup_count,
        }
