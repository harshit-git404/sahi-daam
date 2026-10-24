"""
Unit and Integration Tests for Calculation Ledger Service and SHA-256 Hash Chain (Phase 6).
"""

import json
import math
import os
import tempfile
import unittest
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.models import Base, CalculationRecord
from backend.services.ledger_service import (
    CalculationLedgerService,
    canonical_json,
    calculate_sha256_hash,
    GENESIS_HASH,
    ALGORITHM_VERSION,
    SCHEMA_VERSION,
)


class TestLedgerService(unittest.TestCase):
    def setUp(self):
        # Create an isolated temporary SQLite database for each test
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_url = f"sqlite:///{self.temp_db.name}"
        self.engine = create_engine(self.db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def tearDown(self):
        self.engine.dispose()
        if os.path.exists(self.temp_db.name):
            try:
                os.remove(self.temp_db.name)
            except OSError:
                pass

    def test_canonical_json_determinism(self):
        """Keys must be sorted, compact separators used, and output identical regardless of dict insertion order."""
        dict_a = {"z": 1, "a": 2, "m": {"b": 3, "a": 4}, "list": [1, 2, 3]}
        dict_b = {"list": [1, 2, 3], "a": 2, "m": {"a": 4, "b": 3}, "z": 1}

        canon_a = canonical_json(dict_a)
        canon_b = canonical_json(dict_b)

        self.assertEqual(canon_a, canon_b)
        self.assertNotIn(" ", canon_a)  # No extra whitespace

    def test_canonical_json_rejects_nan_and_inf(self):
        """Canonical JSON serialization must strictly reject NaN and positive/negative infinity."""
        with self.assertRaises(ValueError):
            canonical_json({"val": float("nan")})

        with self.assertRaises(ValueError):
            canonical_json({"val": float("inf")})

        with self.assertRaises(ValueError):
            canonical_json({"val": float("-inf")})

        with self.assertRaises(ValueError):
            canonical_json({"nested": [{"val": float("nan")}]})

    def test_hash_calculation_deterministic(self):
        """calculate_sha256_hash produces consistent SHA-256 and excludes current_record_hash."""
        payload1 = {"sequence_number": 1, "commodity": "tomato", "current_record_hash": "dummy_old"}
        payload2 = {"commodity": "tomato", "sequence_number": 1, "current_record_hash": "different_old"}

        hash1 = calculate_sha256_hash(payload1)
        hash2 = calculate_sha256_hash(payload2)

        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)

    def test_single_record_chain_genesis(self):
        """Genesis record must have sequence_number=1 and previous_record_hash=GENESIS_HASH."""
        session = self.SessionLocal()
        try:
            rec = CalculationLedgerService.append_calculation(
                session=session,
                calculation_id="calc-001",
                commodity_id="tomato",
                locality_id="loc-koramangala",
                status="COMPLETED",
                evidence={"wholesale_price": 25.0, "markup_rate": 0.35},
                is_mock=True,
            )

            self.assertEqual(rec.sequence_number, 1)
            self.assertEqual(rec.previous_record_hash, GENESIS_HASH)
            self.assertTrue(len(rec.current_record_hash) == 64)

            # Verify ledger
            verify_res = CalculationLedgerService.verify_ledger(session)
            self.assertTrue(verify_res.is_valid)
            self.assertEqual(verify_res.total_records, 1)
            self.assertEqual(verify_res.last_sequence_number, 1)
            self.assertEqual(verify_res.last_record_hash, rec.current_record_hash)
            self.assertEqual(len(verify_res.errors), 0)
        finally:
            session.close()

    def test_multi_record_chain_continuity(self):
        """Each successive record must increment sequence and link to previous record's hash."""
        session = self.SessionLocal()
        try:
            rec1 = CalculationLedgerService.append_calculation(
                session=session,
                calculation_id="calc-001",
                commodity_id="tomato",
                locality_id="loc-1",
                status="COMPLETED",
                evidence={"wholesale_price": 20.0},
            )
            rec2 = CalculationLedgerService.append_calculation(
                session=session,
                calculation_id="calc-002",
                commodity_id="potato",
                locality_id="loc-2",
                status="COMPLETED",
                evidence={"wholesale_price": 18.0},
            )
            rec3 = CalculationLedgerService.append_calculation(
                session=session,
                calculation_id="calc-003",
                commodity_id="onion",
                locality_id="loc-1",
                status="PROVISIONAL_WHOLESALE_BASELINE",
                evidence={"wholesale_price": 30.0},
            )

            self.assertEqual(rec1.sequence_number, 1)
            self.assertEqual(rec1.previous_record_hash, GENESIS_HASH)

            self.assertEqual(rec2.sequence_number, 2)
            self.assertEqual(rec2.previous_record_hash, rec1.current_record_hash)

            self.assertEqual(rec3.sequence_number, 3)
            self.assertEqual(rec3.previous_record_hash, rec2.current_record_hash)

            verify_res = CalculationLedgerService.verify_ledger(session)
            self.assertTrue(verify_res.is_valid)
            self.assertEqual(verify_res.total_records, 3)
            self.assertEqual(verify_res.last_sequence_number, 3)
            self.assertEqual(verify_res.last_record_hash, rec3.current_record_hash)
        finally:
            session.close()

    def test_detect_content_tampering(self):
        """Modifying serialized_details directly must be detected by verify_ledger."""
        session = self.SessionLocal()
        try:
            rec1 = CalculationLedgerService.append_calculation(
                session=session,
                calculation_id="calc-001",
                commodity_id="tomato",
                locality_id="loc-1",
                status="COMPLETED",
                evidence={"wholesale_price": 20.0},
            )
            rec2 = CalculationLedgerService.append_calculation(
                session=session,
                calculation_id="calc-002",
                commodity_id="potato",
                locality_id="loc-2",
                status="COMPLETED",
                evidence={"wholesale_price": 18.0},
            )

            # Tamper with rec1 content in DB without updating hash
            details = json.loads(rec1.serialized_details)
            details["wholesale_price"] = 999.0  # Tampered!
            rec1.serialized_details = canonical_json(details)
            session.commit()

            verify_res = CalculationLedgerService.verify_ledger(session)
            self.assertFalse(verify_res.is_valid)
            self.assertIn(1, verify_res.tampered_sequences)
            self.assertTrue(any("Content tampering detected" in err for err in verify_res.errors))
        finally:
            session.close()

    def test_detect_broken_previous_hash_link(self):
        """Tampering with previous_record_hash must be caught by verify_ledger."""
        session = self.SessionLocal()
        try:
            rec1 = CalculationLedgerService.append_calculation(
                session=session,
                calculation_id="calc-001",
                commodity_id="tomato",
                locality_id="loc-1",
                status="COMPLETED",
                evidence={"price": 10},
            )
            rec2 = CalculationLedgerService.append_calculation(
                session=session,
                calculation_id="calc-002",
                commodity_id="potato",
                locality_id="loc-2",
                status="COMPLETED",
                evidence={"price": 20},
            )

            rec2.previous_record_hash = "f" * 64
            session.commit()

            verify_res = CalculationLedgerService.verify_ledger(session)
            self.assertFalse(verify_res.is_valid)
            self.assertIn(2, verify_res.tampered_sequences)
            self.assertTrue(any("Broken hash link" in err for err in verify_res.errors))
        finally:
            session.close()

    def test_detect_deleted_record_sequence_gap(self):
        """Deleting a record creates a sequence gap and must be detected."""
        session = self.SessionLocal()
        try:
            rec1 = CalculationLedgerService.append_calculation(
                session=session,
                calculation_id="calc-001",
                commodity_id="tomato",
                locality_id="loc-1",
                status="COMPLETED",
                evidence={"price": 10},
            )
            rec2 = CalculationLedgerService.append_calculation(
                session=session,
                calculation_id="calc-002",
                commodity_id="potato",
                locality_id="loc-2",
                status="COMPLETED",
                evidence={"price": 20},
            )
            rec3 = CalculationLedgerService.append_calculation(
                session=session,
                calculation_id="calc-003",
                commodity_id="onion",
                locality_id="loc-3",
                status="COMPLETED",
                evidence={"price": 30},
            )

            # Delete middle record
            session.delete(rec2)
            session.commit()

            verify_res = CalculationLedgerService.verify_ledger(session)
            self.assertFalse(verify_res.is_valid)
            self.assertTrue(any("Sequence break" in err or "Broken hash link" in err for err in verify_res.errors))
        finally:
            session.close()

    def test_checkpoint_creation_and_verification(self):
        """Checkpoints capture ledger height and detect subsequent whole-chain replacement."""
        session = self.SessionLocal()
        try:
            rec1 = CalculationLedgerService.append_calculation(
                session=session,
                calculation_id="calc-001",
                commodity_id="tomato",
                locality_id="loc-1",
                status="COMPLETED",
                evidence={"price": 10},
            )
            rec2 = CalculationLedgerService.append_calculation(
                session=session,
                calculation_id="calc-002",
                commodity_id="potato",
                locality_id="loc-2",
                status="COMPLETED",
                evidence={"price": 20},
            )

            checkpoint = CalculationLedgerService.create_checkpoint(session)
            self.assertEqual(checkpoint.last_verified_sequence, 2)
            self.assertEqual(checkpoint.last_record_hash, rec2.current_record_hash)

            # Verify ledger with valid checkpoint
            verify_res = CalculationLedgerService.verify_ledger(session, trusted_checkpoint=checkpoint.model_dump())
            self.assertTrue(verify_res.is_valid)
            self.assertTrue(verify_res.checkpoint_verified)

            # Checkpoint with altered hash must fail
            invalid_ckpt = checkpoint.model_dump()
            invalid_ckpt["last_record_hash"] = "e" * 64
            verify_res_bad = CalculationLedgerService.verify_ledger(session, trusted_checkpoint=invalid_ckpt)
            self.assertFalse(verify_res_bad.is_valid)
            self.assertFalse(verify_res_bad.checkpoint_verified)
            self.assertTrue(any("Checkpoint mismatch" in err for err in verify_res_bad.errors))
        finally:
            session.close()

    def test_json_export_and_standalone_verification(self):
        """Exported JSON must match stored canonical details and pass standalone hash verification."""
        session = self.SessionLocal()
        try:
            rec = CalculationLedgerService.append_calculation(
                session=session,
                calculation_id="calc-exp-01",
                commodity_id="tomato",
                locality_id="loc-1",
                status="COMPLETED",
                evidence={"wholesale_price": 24.5, "markup": 0.35, "units": "₹/kg"},
            )

            exported = CalculationLedgerService.export_calculation_json(session, "calc-exp-01")
            self.assertEqual(exported["calculation_id"], "calc-exp-01")
            self.assertEqual(exported["current_record_hash"], rec.current_record_hash)

            # Verify exported record independently
            is_valid, err = CalculationLedgerService.verify_exported_record(exported)
            self.assertTrue(is_valid)
            self.assertIsNone(err)

            # Tampering with exported copy must fail verification
            tampered_export = dict(exported)
            tampered_export["wholesale_price"] = 999.0
            is_valid_bad, err_bad = CalculationLedgerService.verify_exported_record(tampered_export)
            self.assertFalse(is_valid_bad)
            self.assertIn("Hash mismatch", err_bad)
        finally:
            session.close()

    def test_persistence_across_sessions(self):
        """Data and hash chain integrity must be preserved when sessions are closed and reopened."""
        session1 = self.SessionLocal()
        CalculationLedgerService.append_calculation(
            session=session1,
            calculation_id="calc-pers-01",
            commodity_id="tomato",
            locality_id="loc-1",
            status="COMPLETED",
            evidence={"step": 1},
        )
        session1.close()

        # Reopen in new session
        session2 = self.SessionLocal()
        try:
            rec2 = CalculationLedgerService.append_calculation(
                session=session2,
                calculation_id="calc-pers-02",
                commodity_id="potato",
                locality_id="loc-2",
                status="COMPLETED",
                evidence={"step": 2},
            )
            self.assertEqual(rec2.sequence_number, 2)
            verify_res = CalculationLedgerService.verify_ledger(session2)
            self.assertTrue(verify_res.is_valid)
            self.assertEqual(verify_res.total_records, 2)
        finally:
            session2.close()

    def test_incomplete_calculation_persistence(self):
        """Incomplete calculation attempts must be recorded on the global chain with explicit status."""
        session = self.SessionLocal()
        try:
            rec = CalculationLedgerService.append_calculation(
                session=session,
                calculation_id="calc-inc-01",
                commodity_id="onion",
                locality_id=None,
                status="INCOMPLETE_MISSING_WHOLESALE",
                evidence={"error": "No wholesale record found for locality", "missing_inputs": ["wholesale_price"]},
                is_mock=True,
            )

            self.assertEqual(rec.sequence_number, 1)
            self.assertEqual(rec.status, "INCOMPLETE_MISSING_WHOLESALE")
            verify_res = CalculationLedgerService.verify_ledger(session)
            self.assertTrue(verify_res.is_valid)
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()
