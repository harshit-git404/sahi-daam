"""
API Integration Tests for Phase 7:
Locality/Mandi selection, Transport-Aware Pricing, Adaptive Community Reconciliation,
Calculation Ledger, and Cryptographic Hash-Chain APIs.
"""

import base64
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.models import Base
from backend.database.connection import get_db, init_db
from backend.database.seed import seed_database
from backend.main import app
from backend.services.ledger_service import CalculationLedgerService, calculate_sha256_hash


TINY_JPEG_B64 = (
    "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////"
    "////////////////////////////////////////////////////wgALCAABAAEBAREA"
    "/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="
)


class TestAPIIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create an isolated temporary SQLite database for testing
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db.close()
        cls.db_url = f"sqlite:///{cls.temp_db.name}"
        cls.engine = create_engine(cls.db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(cls.engine)
        cls.TestingSessionLocal = sessionmaker(bind=cls.engine, autocommit=False, autoflush=False)

        # Seed the temporary database
        with cls.TestingSessionLocal() as session:
            seed_database(session)
            CalculationLedgerService.append_calculation(
                session=session,
                calculation_id="calc_seed_001",
                commodity_id="tomato",
                locality_id="loc_katpadi",
                status="COMPLETED",
                evidence={"wholesale_price": 20.0, "step": "seed"},
                is_mock=True,
            )

        # Override FastAPI get_db dependency
        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()
        if os.path.exists(cls.temp_db.name):
            try:
                os.remove(cls.temp_db.name)
            except OSError:
                pass

    # -----------------------------------------------------------------------
    # Locality & Mandi endpoints
    # -----------------------------------------------------------------------
    def test_get_localities_and_pincode_filter(self):
        """GET /localities and /api/localities should list localities and support pincode filtering."""
        res = self.client.get("/localities")
        self.assertEqual(res.status_code, 200)
        items = res.json()
        self.assertGreaterEqual(len(items), 5)

        # Direct path /api/localities should return identical list
        res_api = self.client.get("/api/localities")
        self.assertEqual(res_api.status_code, 200)
        self.assertEqual(len(res_api.json()), len(items))

        # Filter by Katpadi pincode
        res_pin = self.client.get("/localities?pincode=632014")
        self.assertEqual(res_pin.status_code, 200)
        pin_items = res_pin.json()
        self.assertTrue(any(loc["id"] == "loc_katpadi" for loc in pin_items))

    def test_get_mandis(self):
        """GET /mandis and /api/mandis list mandis with reference distances."""
        res = self.client.get("/mandis")
        self.assertEqual(res.status_code, 200)
        mandis = res.json()
        self.assertTrue(any(m["id"] == "mandi_vellore" for m in mandis))
        self.assertTrue(any(m["id"] == "mandi_katpadi" for m in mandis))

    def test_recommend_mandi_endpoint(self):
        """GET /mandis/recommendation provides explainable mandi recommendation."""
        res = self.client.get("/mandis/recommendation?locality_id=loc_katpadi&commodity_id=tomato")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["has_recommendation"])
        self.assertIsNotNone(data["suggested_mandi"])
        self.assertEqual(data["suggested_mandi"]["id"], "mandi_katpadi")
        self.assertEqual(data["suggested_mandi"]["distance_km_reference"], 2.2)
        self.assertIn("Configured reference distance", data["reason"])

    # -----------------------------------------------------------------------
    # Scan with Locality & Transport Integration
    # -----------------------------------------------------------------------
    @patch("backend.routers.scan.get_retail_prices")
    @patch("backend.routers.scan.get_mandi_prices")
    @patch("backend.routers.scan.analyze_with_gemini")
    def test_scan_with_locality_generates_pricing_breakdown_and_ledger_record(
        self, mock_gemini, mock_mandi, mock_retail
    ):
        """Scan with pincode and locality calculates transport, reconciles price, and appends to ledger."""
        mock_gemini.return_value = {
            "produce_type": "Tomato",
            "produce_confidence": 98.0,
            "freshness_label": "Fresh",
            "freshness_percent": 95,
            "freshness_note": "Firm, excellent condition",
            "quality_adjustment": 0,
            "quality_adjustment_label": "No deduction",
        }
        mock_mandi.return_value = {
            "records": [
                {
                    "commodity": "tomato",
                    "market": "Vellore",
                    "district": "Vellore",
                    "arrival_date": "22/10/2026",
                    "modal_price_per_kg": 25.0,
                }
            ]
        }
        mock_retail.return_value = {"status": "UNAVAILABLE", "products": []}

        payload = {
            "image": TINY_JPEG_B64,
            "pincode": "632014",
            "locality_id": "loc_katpadi",
            "mandi_id": "mandi_vellore",
        }

        res = self.client.post("/scan-produce", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Check existing fields preserved
        self.assertEqual(data["produce_type"], "Tomato")
        self.assertEqual(data["wholesale_price"], 25.0)
        self.assertIsNotNone(data["fair_price_range"])

        # Check additive fields
        self.assertIn("pricing_breakdown", data)
        breakdown = data["pricing_breakdown"]
        self.assertIn("cost_basis_per_kg", breakdown)
        self.assertGreaterEqual(breakdown["cost_basis_per_kg"], 25.0)  # wholesale + transport
        self.assertIn("baseline_range", breakdown)
        self.assertIn("reconciled_range", breakdown)

        # Check ledger metadata
        self.assertIsNotNone(data["calculation_id"])
        self.assertIsNotNone(data["sequence_number"])
        self.assertIsNotNone(data["record_hash"])
        self.assertTrue(len(data["record_hash"]) == 64)
        self.assertTrue(data["is_mock"])

        # Check calculation is retrievable via ledger API
        calc_id = data["calculation_id"]
        res_calc = self.client.get(f"/calculations/{calc_id}")
        self.assertEqual(res_calc.status_code, 200)
        calc_data = res_calc.json()
        self.assertEqual(calc_data["id"], calc_id)
        self.assertEqual(calc_data["sequence_number"], data["sequence_number"])
        self.assertEqual(calc_data["current_record_hash"], data["record_hash"])

    # -----------------------------------------------------------------------
    # Ledger listing, JSON export, and Chain Verification
    # -----------------------------------------------------------------------
    def test_list_calculations_and_pagination(self):
        """GET /calculations returns paginated calculations list."""
        res = self.client.get("/calculations?limit=10&offset=0")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("calculations", data)
        self.assertIn("total_count", data)

    def test_export_calculation_json(self):
        """GET /calculations/{id}/export downloads verifiable JSON evidence."""
        # Query list to get an existing calculation ID
        res_list = self.client.get("/calculations")
        calcs = res_list.json()["calculations"]
        if not calcs:
            self.skipTest("No calculations in ledger yet.")

        calc_id = calcs[0]["id"]
        res_export = self.client.get(f"/calculations/{calc_id}/export")
        self.assertEqual(res_export.status_code, 200)
        self.assertIn("attachment; filename=", res_export.headers.get("content-disposition", ""))

        exported_json = res_export.json()
        self.assertEqual(exported_json["calculation_id"], calc_id)
        self.assertIn("current_record_hash", exported_json)

        # Verify exported record cryptographically
        valid, err = CalculationLedgerService.verify_exported_record(exported_json)
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_verify_ledger_endpoint(self):
        """GET /ledger/verify confirms sequence continuity and cryptographic hashes."""
        res = self.client.get("/ledger/verify")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_valid"])
        self.assertEqual(len(data["errors"]), 0)
        self.assertGreaterEqual(data["total_records"], 1)

    def test_checkpoint_creation_and_retrieval(self):
        """POST /ledger/checkpoint and GET /ledger/checkpoint capture height snapshot."""
        res_post = self.client.post("/ledger/checkpoint")
        self.assertEqual(res_post.status_code, 201)
        ckpt_data = res_post.json()
        self.assertIn("checkpoint_id", ckpt_data)
        self.assertGreaterEqual(ckpt_data["last_verified_sequence"], 1)
        self.assertIsNotNone(ckpt_data["last_record_hash"])

        res_get = self.client.get("/ledger/checkpoint")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["last_record_hash"], ckpt_data["last_record_hash"])

    # -----------------------------------------------------------------------
    # Haggle check endpoint with proxy compatibility
    # -----------------------------------------------------------------------
    def test_haggle_check_api_prefix(self):
        """POST /api/haggle-check should succeed identically to /haggle-check."""
        payload = {
            "asking_price": 40.0,
            "fair_price_min": 25.0,
            "fair_price_max": 35.0,
            "purchase_type": "street_vendor",
        }
        res = self.client.post("/api/haggle-check", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["verdict"], "HIGH")


if __name__ == "__main__":
    unittest.main()
