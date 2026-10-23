"""
Community Price Router for Sahi Daam.

Provides endpoints for community-sourced price submissions and queries.
Compatible with direct API calls and the Vite dev-server proxy rewrite.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.schemas import (
    CommunityPriceSubmission,
    CommunityPriceSubmissionResponse,
    CommunityPriceListResponse,
)
from backend.services.community_service import CommunityPriceService

router = APIRouter(tags=["Community Prices"])


# ---------------------------------------------------------------------------
# Submission Endpoints (supporting both /community-prices and /api/community-prices)
# ---------------------------------------------------------------------------

@router.post(
    "/community-prices",
    response_model=CommunityPriceSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a community price observation",
)
@router.post(
    "/api/community-prices",
    response_model=CommunityPriceSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def submit_community_price(
    submission: CommunityPriceSubmission,
    db: Session = Depends(get_db),
) -> CommunityPriceSubmissionResponse:
    """
    Submit a crowd-sourced produce price observation.

    Validates:
    - Supported commodity identifier or alias.
    - Valid locality (existing ID or on-the-fly resolution via name).
    - Positive finite price.
    - Explicit supported unit (rejects ambiguous units like box, bag, crate).
    - Accurate timestamp (rejects timestamps in the future).
    - Source type (customer or vendor).

    Performs conservative duplicate detection while always preserving the original report.
    """
    try:
        return CommunityPriceService.process_submission(session=db, submission=submission)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# Retrieval Endpoints (supporting both /community-prices and /api/community-prices)
# ---------------------------------------------------------------------------

@router.get(
    "/community-prices",
    response_model=CommunityPriceListResponse,
    summary="List community price observations with metrics",
)
@router.get(
    "/api/community-prices",
    response_model=CommunityPriceListResponse,
    include_in_schema=False,
)
def get_community_prices(
    commodity_id: Optional[str] = Query(None, description="Commodity identifier or alias (e.g. tomato, onion)"),
    locality_id: Optional[str] = Query(None, description="Locality identifier (e.g. loc_katpadi)"),
    source_type: Optional[str] = Query(None, description="Source type filter: 'customer' or 'vendor'"),
    window_days: Optional[int] = Query(2, ge=1, le=365, description="Rolling observation window in days (default 2)"),
    exclude_duplicates: bool = Query(True, description="Exclude flagged duplicates from results and sample metrics"),
    limit: int = Query(50, ge=1, le=100, description="Safe maximum items to return"),
    offset: int = Query(0, ge=0, description="Result offset for pagination"),
    db: Session = Depends(get_db),
) -> CommunityPriceListResponse:
    """
    Retrieve community price observations within the configured temporal window.

    Returns:
    - Paginated list of observations with outlier tags.
    - Statistical summary metrics (sample count, average, median, min, max, duplicate count).
    """
    return CommunityPriceService.list_observations(
        session=db,
        commodity_id=commodity_id,
        locality_id=locality_id,
        source_type=source_type,
        window_days=window_days,
        exclude_duplicates=exclude_duplicates,
        limit=limit,
        offset=offset,
    )
