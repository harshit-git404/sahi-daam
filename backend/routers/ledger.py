"""
Calculation Ledger Router for Sahi Daam.

Provides endpoints for:
1. Paginated calculation history.
2. Single calculation inspection.
3. Cryptographic JSON export of individual calculation records.
4. Global SHA-256 hash-chain verification.
5. Checkpoint creation and retrieval.
"""

import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.services.ledger_service import (
    CalculationLedgerService,
    LedgerVerificationResult,
    LedgerCheckpoint,
)


router = APIRouter(tags=["Calculation Ledger"])


class CalculationSummaryDTO(BaseModel):
    id: str
    sequence_number: int
    commodity_id: str
    locality_id: Optional[str] = None
    status: str
    algorithm_version: str
    schema_version: str
    previous_record_hash: str
    current_record_hash: str
    is_mock: bool
    created_at: str

    class Config:
        from_attributes = True


class CalculationListResponse(BaseModel):
    calculations: List[CalculationSummaryDTO]
    total_count: int
    limit: int
    offset: int


class CalculationDetailResponse(BaseModel):
    id: str
    sequence_number: int
    commodity_id: str
    locality_id: Optional[str] = None
    status: str
    algorithm_version: str
    schema_version: str
    previous_record_hash: str
    current_record_hash: str
    is_mock: bool
    created_at: str
    evidence: Dict[str, Any]


# ---------------------------------------------------------------------------
# History Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/calculations",
    response_model=CalculationListResponse,
    summary="List calculation records with pagination",
)
@router.get(
    "/api/calculations",
    response_model=CalculationListResponse,
    include_in_schema=False,
)
def list_calculations(
    commodity_id: Optional[str] = Query(None, description="Filter by commodity ID"),
    locality_id: Optional[str] = Query(None, description="Filter by locality ID"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
) -> CalculationListResponse:
    records, total = CalculationLedgerService.list_calculations(
        session=db,
        commodity_id=commodity_id,
        locality_id=locality_id,
        limit=limit,
        offset=offset,
    )
    summaries = [
        CalculationSummaryDTO(
            id=r.id,
            sequence_number=r.sequence_number,
            commodity_id=r.commodity_id,
            locality_id=r.locality_id,
            status=r.status,
            algorithm_version=r.algorithm_version,
            schema_version=r.schema_version,
            previous_record_hash=r.previous_record_hash,
            current_record_hash=r.current_record_hash,
            is_mock=r.is_mock,
            created_at=r.created_at.isoformat() if hasattr(r.created_at, "isoformat") else str(r.created_at),
        )
        for r in records
    ]
    return CalculationListResponse(
        calculations=summaries,
        total_count=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/calculations/{calculation_id}",
    response_model=CalculationDetailResponse,
    summary="Get full details and evidence for a specific calculation",
)
@router.get(
    "/api/calculations/{calculation_id}",
    response_model=CalculationDetailResponse,
    include_in_schema=False,
)
def get_calculation_detail(
    calculation_id: str,
    db: Session = Depends(get_db),
) -> CalculationDetailResponse:
    record = CalculationLedgerService.get_calculation(db, calculation_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Calculation with ID '{calculation_id}' not found.")

    evidence = json.loads(record.serialized_details)
    return CalculationDetailResponse(
        id=record.id,
        sequence_number=record.sequence_number,
        commodity_id=record.commodity_id,
        locality_id=record.locality_id,
        status=record.status,
        algorithm_version=record.algorithm_version,
        schema_version=record.schema_version,
        previous_record_hash=record.previous_record_hash,
        current_record_hash=record.current_record_hash,
        is_mock=record.is_mock,
        created_at=record.created_at.isoformat() if hasattr(record.created_at, "isoformat") else str(record.created_at),
        evidence=evidence,
    )


# ---------------------------------------------------------------------------
# Cryptographic JSON Export
# ---------------------------------------------------------------------------

@router.get(
    "/calculations/{calculation_id}/export",
    summary="Download canonical calculation evidence and SHA-256 hash envelope as JSON",
)
@router.get(
    "/api/calculations/{calculation_id}/export",
    include_in_schema=False,
)
def export_calculation(
    calculation_id: str,
    db: Session = Depends(get_db),
):
    try:
        exported_data = CalculationLedgerService.export_calculation_json(db, calculation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    content = json.dumps(exported_data, indent=2, sort_keys=True)
    filename = f"sahi_daam_{calculation_id}.json"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "application/json",
    }
    return Response(content=content, media_type="application/json", headers=headers)


# ---------------------------------------------------------------------------
# Global Hash-Chain Verification & Checkpoints
# ---------------------------------------------------------------------------

@router.get(
    "/ledger/verify",
    response_model=LedgerVerificationResult,
    summary="Verify the cryptographic integrity of the global hash chain",
)
@router.get(
    "/api/ledger/verify",
    response_model=LedgerVerificationResult,
    include_in_schema=False,
)
def verify_ledger(
    db: Session = Depends(get_db),
) -> LedgerVerificationResult:
    return CalculationLedgerService.verify_ledger(db)


@router.post(
    "/ledger/checkpoint",
    response_model=LedgerCheckpoint,
    status_code=status.HTTP_201_CREATED,
    summary="Create a trusted checkpoint snapshot at current ledger height",
)
@router.post(
    "/api/ledger/checkpoint",
    response_model=LedgerCheckpoint,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_checkpoint(
    sequence_number: Optional[int] = Query(None, description="Optional target sequence number"),
    db: Session = Depends(get_db),
) -> LedgerCheckpoint:
    try:
        return CalculationLedgerService.create_checkpoint(db, sequence_number=sequence_number)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/ledger/checkpoint",
    response_model=LedgerCheckpoint,
    summary="Retrieve the latest trusted checkpoint for the ledger",
)
@router.get(
    "/api/ledger/checkpoint",
    response_model=LedgerCheckpoint,
    include_in_schema=False,
)
def get_latest_checkpoint(
    db: Session = Depends(get_db),
) -> LedgerCheckpoint:
    try:
        return CalculationLedgerService.create_checkpoint(db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
