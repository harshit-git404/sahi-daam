"""
Persistent JSON Calculation Ledger and Global SHA-256 Hash Chain Service for Sahi Daam.

Guarantees:
1. All calculations belong to one single, global contiguous sequence (1, 2, 3, ...).
2. Genesis record links to 64 zeros ("0" * 64).
3. Every subsequent record links cryptographically to the exact SHA-256 hash of its predecessor.
4. Canonical JSON serialization is strictly deterministic (sorted keys, compact separators, UTF-8, NaN/Inf rejection).
5. Record hash is computed over canonical JSON of the evidence excluding its own hash.
6. Atomic persistence with SQLite transaction locking to protect against race conditions.
7. Verification utility checks sequence continuity, hash links, content integrity, and trusted checkpoints.
8. Standalone JSON export preserves complete stored evidence and hash-envelope.
"""

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.database.models import CalculationRecord


GENESIS_HASH = "0" * 64
ALGORITHM_VERSION = "v2.0-locality-reconciled"
SCHEMA_VERSION = "1.0.0"


def _check_finite_numbers(obj: Any) -> None:
    """Recursively ensure no NaN or Infinite floats exist in the payload."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            raise ValueError(f"Cannot canonically serialize invalid float value: {obj}")
    elif isinstance(obj, dict):
        for v in obj.values():
            _check_finite_numbers(v)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _check_finite_numbers(item)


def canonical_json(data: Any) -> str:
    """
    Produce strictly deterministic canonical JSON string:
    - Rejects NaN and +/- Infinity.
    - Keys sorted alphabetically.
    - Compact separators (',', ':') with zero extraneous whitespace.
    - UTF-8 clean.
    """
    _check_finite_numbers(data)
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def calculate_sha256_hash(payload_dict: Dict[str, Any]) -> str:
    """
    Compute SHA-256 hex digest over canonical JSON representation of the record.
    The current_record_hash field is excluded from its own hash calculation.
    """
    hashable_copy = {k: v for k, v in payload_dict.items() if k != "current_record_hash"}
    canonical_str = canonical_json(hashable_copy)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


class LedgerVerificationResult(BaseModel):
    is_valid: bool
    total_records: int
    last_sequence_number: Optional[int] = None
    last_record_hash: Optional[str] = None
    tampered_sequences: List[int] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    checkpoint_verified: bool = False
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LedgerCheckpoint(BaseModel):
    checkpoint_id: str
    last_verified_sequence: int
    last_record_hash: str
    record_count: int
    created_at: datetime
    ledger_schema_version: str = SCHEMA_VERSION
    algorithm_version: str = ALGORITHM_VERSION


class CalculationLedgerService:
    """Core domain service for appending, verifying, and exporting the calculation ledger."""

    @classmethod
    def append_calculation(
        cls,
        session: Session,
        calculation_id: str,
        commodity_id: str,
        locality_id: Optional[str],
        status: str,
        evidence: Dict[str, Any],
        is_mock: bool = True,
        max_retries: int = 3,
    ) -> CalculationRecord:
        """
        Atomically append a calculation to the global ledger and link it to the hash chain.
        """
        evidence_dict = dict(evidence)
        evidence_dict["calculation_id"] = calculation_id
        evidence_dict["commodity_id"] = commodity_id
        evidence_dict["locality_id"] = locality_id
        evidence_dict["status"] = status
        evidence_dict["algorithm_version"] = ALGORITHM_VERSION
        evidence_dict["schema_version"] = SCHEMA_VERSION
        evidence_dict["is_mock"] = is_mock

        if "created_at" not in evidence_dict:
            evidence_dict["created_at"] = datetime.now(timezone.utc).isoformat()

        # Atomic retry loop in case of concurrent sequence number collisions
        for attempt in range(max_retries):
            try:
                # Query the latest tip in transaction
                tip_stmt = (
                    select(CalculationRecord)
                    .order_by(CalculationRecord.sequence_number.desc())
                    .limit(1)
                )
                tip = session.scalars(tip_stmt).first()

                if tip is None:
                    next_seq = 1
                    prev_hash = GENESIS_HASH
                else:
                    next_seq = tip.sequence_number + 1
                    prev_hash = tip.current_record_hash

                evidence_dict["sequence_number"] = next_seq
                evidence_dict["previous_record_hash"] = prev_hash

                # Compute current record hash over canonical JSON excluding current_record_hash
                current_hash = calculate_sha256_hash(evidence_dict)
                evidence_dict["current_record_hash"] = current_hash

                # Store full serialized canonical details
                canonical_str = canonical_json(evidence_dict)

                record = CalculationRecord(
                    id=calculation_id,
                    sequence_number=next_seq,
                    commodity_id=commodity_id,
                    locality_id=locality_id,
                    status=status,
                    algorithm_version=ALGORITHM_VERSION,
                    schema_version=SCHEMA_VERSION,
                    serialized_details=canonical_str,
                    previous_record_hash=prev_hash,
                    current_record_hash=current_hash,
                    is_mock=is_mock,
                )

                session.add(record)
                session.commit()
                session.refresh(record)
                return record

            except IntegrityError:
                session.rollback()
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed to append calculation record {calculation_id} after {max_retries} attempts.")
            except Exception:
                session.rollback()
                raise

        raise RuntimeError("Unexpected failure to commit calculation record.")

    @classmethod
    def get_calculation(cls, session: Session, calculation_id: str) -> Optional[CalculationRecord]:
        """Fetch a calculation record by its unique ID."""
        return session.get(CalculationRecord, calculation_id)

    @classmethod
    def list_calculations(
        cls,
        session: Session,
        commodity_id: Optional[str] = None,
        locality_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[CalculationRecord], int]:
        """List calculations with safe pagination and total count."""
        conditions = []
        if commodity_id:
            conditions.append(CalculationRecord.commodity_id == commodity_id)
        if locality_id:
            conditions.append(CalculationRecord.locality_id == locality_id)

        where_clause = and_(*conditions) if conditions else True

        total = session.scalar(select(func.count(CalculationRecord.id)).where(where_clause)) or 0
        stmt = (
            select(CalculationRecord)
            .where(where_clause)
            .order_by(CalculationRecord.sequence_number.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list(session.scalars(stmt).all())
        return items, total

    @classmethod
    def verify_ledger(
        cls,
        session: Session,
        trusted_checkpoint: Optional[Dict[str, Any]] = None,
    ) -> LedgerVerificationResult:
        """
        Verify the integrity of the entire global hash chain:
        1. Sequence continuity: sequence numbers must be 1, 2, ..., N without gaps or duplicates.
        2. Genesis hash check: sequence 1 must link to GENESIS_HASH.
        3. Cryptographic link check: record[i].previous_record_hash == record[i-1].current_record_hash.
        4. Content integrity check: SHA-256 of canonical JSON matches current_record_hash.
        5. Trusted checkpoint check: if provided, verified sequence and hash must match checkpoint.
        """
        stmt = select(CalculationRecord).order_by(CalculationRecord.sequence_number.asc())
        records = list(session.scalars(stmt).all())

        if not records:
            return LedgerVerificationResult(
                is_valid=True,
                total_records=0,
                last_sequence_number=None,
                last_record_hash=None,
            )

        errors: List[str] = []
        tampered_seqs: List[int] = []
        expected_prev_hash = GENESIS_HASH

        checkpoint_verified = False
        target_checkpoint_seq = (
            trusted_checkpoint.get("last_verified_sequence") if trusted_checkpoint else None
        )
        target_checkpoint_hash = (
            trusted_checkpoint.get("last_record_hash") if trusted_checkpoint else None
        )

        for i, record in enumerate(records):
            expected_seq = i + 1

            # 1. Sequence Continuity
            if record.sequence_number != expected_seq:
                errors.append(
                    f"Sequence break: expected sequence #{expected_seq}, found #{record.sequence_number} on record {record.id}."
                )
                tampered_seqs.append(record.sequence_number)

            # 2. Previous Hash Link
            if record.previous_record_hash != expected_prev_hash:
                errors.append(
                    f"Broken hash link at sequence #{record.sequence_number}: previous_record_hash "
                    f"'{record.previous_record_hash}' does not match expected predecessor hash '{expected_prev_hash}'."
                )
                tampered_seqs.append(record.sequence_number)

            # 3. Content Integrity & Hash Recomputation
            try:
                details = json.loads(record.serialized_details)
                recomputed_hash = calculate_sha256_hash(details)
                if recomputed_hash != record.current_record_hash:
                    errors.append(
                        f"Content tampering detected at sequence #{record.sequence_number}: stored hash "
                        f"'{record.current_record_hash}' does not match recomputed hash '{recomputed_hash}'."
                    )
                    tampered_seqs.append(record.sequence_number)
            except Exception as exc:
                errors.append(
                    f"JSON parsing error at sequence #{record.sequence_number}: {exc}"
                )
                tampered_seqs.append(record.sequence_number)

            # 4. Checkpoint height validation
            if target_checkpoint_seq is not None and record.sequence_number == target_checkpoint_seq:
                if record.current_record_hash == target_checkpoint_hash:
                    checkpoint_verified = True
                else:
                    errors.append(
                        f"Checkpoint mismatch at sequence #{target_checkpoint_seq}: chain hash '{record.current_record_hash}' "
                        f"does not match trusted checkpoint hash '{target_checkpoint_hash}'."
                    )

            expected_prev_hash = record.current_record_hash

        if target_checkpoint_seq is not None and not checkpoint_verified:
            if target_checkpoint_seq > len(records):
                errors.append(
                    f"Checkpoint sequence #{target_checkpoint_seq} exceeds current ledger height ({len(records)})."
                )

        is_valid = len(errors) == 0
        last_rec = records[-1]

        return LedgerVerificationResult(
            is_valid=is_valid,
            total_records=len(records),
            last_sequence_number=last_rec.sequence_number,
            last_record_hash=last_rec.current_record_hash,
            tampered_sequences=sorted(list(set(tampered_seqs))),
            errors=errors,
            checkpoint_verified=checkpoint_verified,
        )

    @classmethod
    def create_checkpoint(cls, session: Session, sequence_number: Optional[int] = None) -> LedgerCheckpoint:
        """Create a verifiable trusted checkpoint snapshot of the ledger at current height."""
        if sequence_number is not None:
            record = session.scalar(select(CalculationRecord).where(CalculationRecord.sequence_number == sequence_number))
            if not record:
                raise ValueError(f"No calculation record found at sequence #{sequence_number}.")
        else:
            record = session.scalar(select(CalculationRecord).order_by(CalculationRecord.sequence_number.desc()).limit(1))
            if not record:
                raise ValueError("Cannot create checkpoint on an empty ledger.")

        count = session.scalar(select(func.count(CalculationRecord.id))) or 0

        checkpoint_id = f"ckpt_seq_{record.sequence_number}_{record.current_record_hash[:8]}"
        return LedgerCheckpoint(
            checkpoint_id=checkpoint_id,
            last_verified_sequence=record.sequence_number,
            last_record_hash=record.current_record_hash,
            record_count=count,
            created_at=datetime.now(timezone.utc),
            ledger_schema_version=SCHEMA_VERSION,
            algorithm_version=ALGORITHM_VERSION,
        )

    @classmethod
    def export_calculation_json(cls, session: Session, calculation_id: str) -> Dict[str, Any]:
        """
        Export complete calculation evidence for downloadable inspection.
        Guarantees that exported content corresponds directly to the stored canonical evidence.
        """
        record = cls.get_calculation(session, calculation_id)
        if not record:
            raise ValueError(f"Calculation with ID '{calculation_id}' not found.")

        payload = json.loads(record.serialized_details)
        # Ensure envelope fields are explicitly synced
        payload["sequence_number"] = record.sequence_number
        payload["previous_record_hash"] = record.previous_record_hash
        payload["current_record_hash"] = record.current_record_hash
        payload["algorithm_version"] = record.algorithm_version
        payload["schema_version"] = record.schema_version
        payload["is_mock"] = record.is_mock
        return payload

    @classmethod
    def verify_exported_record(cls, exported_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Verify the cryptographic authenticity of an exported calculation file."""
        if "current_record_hash" not in exported_data:
            return False, "Missing 'current_record_hash' in exported record."

        expected_hash = exported_data["current_record_hash"]
        try:
            recomputed = calculate_sha256_hash(exported_data)
            if recomputed == expected_hash:
                return True, None
            return False, f"Hash mismatch: stored '{expected_hash}' vs recomputed '{recomputed}'."
        except Exception as exc:
            return False, f"Serialization or verification error: {exc}"
