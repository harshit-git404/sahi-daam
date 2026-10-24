"""
Locations Router for Sahi Daam.

Provides endpoints for:
1. Locality lookup by pincode or all localities.
2. Mandi options retrieval by district/state or all mandis.
3. Nearest/suggested mandi recommendation for a given locality with explainable provenance.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import Locality, Mandi
from backend.database.repositories import LocalityRepository, MandiRepository, WholesalePriceRepository


router = APIRouter(tags=["Locations & Mandis"])


class LocalityDTO(BaseModel):
    id: str
    name: str
    pincode: Optional[str] = None
    district: str
    state: str

    class Config:
        from_attributes = True


class MandiDTO(BaseModel):
    id: str
    market_name: str
    district: str
    state: str
    distance_km_reference: Optional[float] = None
    provenance_note: Optional[str] = None
    is_mock: bool = True

    class Config:
        from_attributes = True


class MandiRecommendationResponse(BaseModel):
    suggested_mandi: Optional[MandiDTO] = None
    locality: LocalityDTO
    has_recommendation: bool
    confidence: str  # "high", "provisional", "unavailable"
    distance_km: Optional[float] = None
    reason: str
    available_mandis: List[MandiDTO]


# ---------------------------------------------------------------------------
# Locality Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/localities",
    response_model=List[LocalityDTO],
    summary="List localities with optional pincode filtering",
)
@router.get(
    "/api/localities",
    response_model=List[LocalityDTO],
    include_in_schema=False,
)
def get_localities(
    pincode: Optional[str] = Query(None, description="6-digit Indian postal code to filter localities"),
    db: Session = Depends(get_db),
) -> List[LocalityDTO]:
    if pincode:
        clean_pin = pincode.strip()
        localities = LocalityRepository.list_by_pincode(db, clean_pin)
    else:
        localities = LocalityRepository.list_all(db)
    return [LocalityDTO.model_validate(loc) for loc in localities]


# ---------------------------------------------------------------------------
# Mandi Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/mandis",
    response_model=List[MandiDTO],
    summary="List registered mandis with optional district filter",
)
@router.get(
    "/api/mandis",
    response_model=List[MandiDTO],
    include_in_schema=False,
)
def get_mandis(
    district: Optional[str] = Query(None, description="District name to filter mandis"),
    db: Session = Depends(get_db),
) -> List[MandiDTO]:
    if district:
        mandis = MandiRepository.list_by_district(db, district.strip())
    else:
        mandis = MandiRepository.list_all(db)
    return [MandiDTO.model_validate(m) for m in mandis]


# ---------------------------------------------------------------------------
# Mandi Recommendation
# ---------------------------------------------------------------------------

@router.get(
    "/mandis/recommendation",
    response_model=MandiRecommendationResponse,
    summary="Suggest the nearest reliable mandi for a given locality",
)
@router.get(
    "/api/mandis/recommendation",
    response_model=MandiRecommendationResponse,
    include_in_schema=False,
)
def recommend_mandi(
    locality_id: str = Query(..., description="Locality identifier (e.g. loc_katpadi)"),
    commodity_id: Optional[str] = Query(None, description="Optional commodity ID to verify wholesale data availability"),
    db: Session = Depends(get_db),
) -> MandiRecommendationResponse:
    locality = LocalityRepository.get_by_id(db, locality_id)
    if not locality:
        raise HTTPException(status_code=404, detail=f"Locality with ID '{locality_id}' not found.")

    all_mandis = MandiRepository.list_all(db)
    all_dtos = [MandiDTO.model_validate(m) for m in all_mandis]

    # Find mandis in the same district first
    district_mandis = [m for m in all_mandis if m.district.lower() == locality.district.lower()]

    if not district_mandis:
        # Check same state
        district_mandis = [m for m in all_mandis if m.state.lower() == locality.state.lower()]

    if not district_mandis:
        return MandiRecommendationResponse(
            suggested_mandi=None,
            locality=LocalityDTO.model_validate(locality),
            has_recommendation=False,
            confidence="unavailable",
            distance_km=None,
            reason=f"No verified mandis found matching district '{locality.district}' or state '{locality.state}'. Please select a mandi manually.",
            available_mandis=all_dtos,
        )

    # Sort candidates: prioritize those with verified wholesale observations for the requested commodity, then by distance_km_reference
    def score_mandi(m: Mandi) -> tuple:
        has_wholesale = False
        if commodity_id:
            w_obs = WholesalePriceRepository.get_latest(db, commodity_id=commodity_id, mandi_id=m.id)
            has_wholesale = (w_obs is not None)
        dist = m.distance_km_reference if m.distance_km_reference is not None else 9999.0
        # return tuple: (not has_wholesale, dist) so True/has_wholesale comes first, then lowest distance
        return (not has_wholesale, dist)

    sorted_candidates = sorted(district_mandis, key=score_mandi)
    top_mandi = sorted_candidates[0]
    distance = top_mandi.distance_km_reference

    has_wholesale_data = False
    if commodity_id:
        w_obs = WholesalePriceRepository.get_latest(db, commodity_id=commodity_id, mandi_id=top_mandi.id)
        has_wholesale_data = (w_obs is not None)

    reason_parts = [f"Recommended based on geographic alignment with {locality.district}."]
    if distance is not None:
        reason_parts.append(f"Configured reference distance is {distance} km.")
    if commodity_id:
        if has_wholesale_data:
            reason_parts.append(f"Active wholesale records confirmed for {commodity_id}.")
        else:
            reason_parts.append(f"No specific wholesale record recorded for {commodity_id} at this mandi; user selection or override supported.")

    return MandiRecommendationResponse(
        suggested_mandi=MandiDTO.model_validate(top_mandi),
        locality=LocalityDTO.model_validate(locality),
        has_recommendation=True,
        confidence="high" if distance is not None and has_wholesale_data else "provisional",
        distance_km=distance,
        reason=" ".join(reason_parts),
        available_mandis=all_dtos,
    )

