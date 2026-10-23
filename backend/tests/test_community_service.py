import math
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import unittest
from fastapi.testclient import TestClient

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sqlalchemy.pool import StaticPool
from backend.main import app
from backend.database.connection import init_db, create_engine, sessionmaker, get_db
from backend.database.seed import seed_database
from backend.database.models import CommunityPriceObservation, Locality
from backend.database.schemas import CommunityPriceSubmission
from backend.services.community_service import CommunityPriceService


class TestCommunityPriceService(unittest.TestCase):
    """Unit and API integration tests for Phase 4 Community-Price Service."""

    def setUp(self):
        # Create an isolated in-memory SQLite database with StaticPool to share state across sessions
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
        init_db(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.test_clock = datetime(2026, 10, 23, 12, 0, 0, tzinfo=timezone.utc)

        # Seed reference localities
        seed_database(self.session, base_time=self.test_clock)

        # Override FastAPI DB dependency to use test database
        def override_get_db():
            db = self.Session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.session.close()
        self.engine.dispose()

    # -----------------------------------------------------------------------
    # 1. Valid Submissions
    # -----------------------------------------------------------------------
    def test_valid_customer_submission_kg(self):
        """Submit a standard customer report in kg for Tomato."""
        payload = {
            "commodity_id": "tomato",
            "locality_id": "loc_katpadi",
            "price": 27.5,
            "unit": "kg",
            "source_type": "customer",
            "contributor_id": "cust_mock_test",
            "observed_at": (self.test_clock - timedelta(hours=1)).isoformat(),
        }
        res = self.client.post("/api/community-prices", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()

        self.assertEqual(data["status"], "recorded")
        self.assertFalse(data["is_duplicate"])
        self.assertEqual(data["normalized_price_per_kg"], 27.5)
        self.assertEqual(data["observation"]["commodity_id"], "tomato")
        self.assertEqual(data["observation"]["price"], 27.5)
        self.assertEqual(data["observation"]["unit"], "kg")
        self.assertEqual(data["observation"]["source_type"], "customer")

    def test_valid_vendor_submission_fractional_weight(self):
        """Submit a vendor price for 500g and verify accurate ₹/kg normalization."""
        payload = {
            "commodity_id": "potato",
            "locality_id": "loc_gandhi_nagar",
            "price": 16.0,  # ₹16 for 500g = ₹32/kg
            "unit": "500g",
            "source_type": "vendor",
            "contributor_id": "vend_mock_test",
            "observed_at": (self.test_clock - timedelta(hours=2)).isoformat(),
        }
        res = self.client.post("/community-prices", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()

        self.assertEqual(data["status"], "recorded")
        self.assertEqual(data["normalized_price_per_kg"], 32.0)
        self.assertEqual(data["observation"]["unit"], "500g")
        self.assertEqual(data["observation"]["price"], 16.0)

    def test_valid_count_submission_no_blind_kg_conversion(self):
        """Commodity sold by piece (lemon) must NOT be converted blindly to kg."""
        payload = {
            "commodity_id": "lemon",
            "locality_id": "loc_katpadi",
            "price": 6.0,
            "unit": "piece",
            "source_type": "customer",
            "contributor_id": "cust_mock_test",
            "observed_at": (self.test_clock - timedelta(hours=1)).isoformat(),
        }
        res = self.client.post("/api/community-prices", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()

        self.assertEqual(data["status"], "recorded")
        self.assertIsNone(data["normalized_price_per_kg"])
        self.assertEqual(data["observation"]["unit"], "piece")
        self.assertEqual(data["observation"]["price"], 6.0)

    def test_locality_creation_on_the_fly(self):
        """Submitting a valid locality name creates the locality without error."""
        payload = {
            "commodity_id": "tomato",
            "locality_name": "Ranipet Sipcot",
            "district": "Ranipet",
            "pincode": "632403",
            "price": 26.0,
            "unit": "kg",
            "source_type": "customer",
        }
        res = self.client.post("/api/community-prices", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["observation"]["locality_id"], "loc_ranipet_sipcot")

    # -----------------------------------------------------------------------
    # 2. Invalid Prices & Units Rejections
    # -----------------------------------------------------------------------
    def test_zero_price_rejected(self):
        """Zero price must be rejected with HTTP 422."""
        payload = {
            "commodity_id": "tomato",
            "locality_id": "loc_katpadi",
            "price": 0.0,
            "unit": "kg",
            "source_type": "customer",
        }
        res = self.client.post("/api/community-prices", json=payload)
        self.assertEqual(res.status_code, 422)
        self.assertIn("positive finite number", res.json()["detail"])

    def test_negative_price_rejected(self):
        """Negative price must be rejected with HTTP 422."""
        payload = {
            "commodity_id": "tomato",
            "locality_id": "loc_katpadi",
            "price": -15.0,
            "unit": "kg",
            "source_type": "customer",
        }
        res = self.client.post("/api/community-prices", json=payload)
        self.assertEqual(res.status_code, 422)
        self.assertIn("positive finite number", res.json()["detail"])

    def test_ambiguous_unit_rejected(self):
        """Ambiguous units like 'box', 'bag', 'crate' must be rejected with clear message."""
        for ambiguous in ["box", "bag", "crate", "packet", "carton"]:
            payload = {
                "commodity_id": "tomato",
                "locality_id": "loc_katpadi",
                "price": 100.0,
                "unit": ambiguous,
                "source_type": "customer",
            }
            res = self.client.post("/api/community-prices", json=payload)
            self.assertEqual(res.status_code, 422)
            self.assertIn("Ambiguous unit", res.json()["detail"])

    # -----------------------------------------------------------------------
    # 3. Invalid Commodities & Localities
    # -----------------------------------------------------------------------
    def test_unsupported_commodity_rejected(self):
        """Unsupported commodity must be rejected with HTTP 422."""
        payload = {
            "commodity_id": "unsupported_fruit_xyz",
            "locality_id": "loc_katpadi",
            "price": 50.0,
            "unit": "kg",
            "source_type": "customer",
        }
        res = self.client.post("/api/community-prices", json=payload)
        self.assertEqual(res.status_code, 422)
        self.assertIn("Unsupported or unknown commodity", res.json()["detail"])

    def test_nonexistent_locality_rejected(self):
        """Non-existent locality ID must be rejected with HTTP 422."""
        payload = {
            "commodity_id": "tomato",
            "locality_id": "loc_non_existent_999",
            "price": 30.0,
            "unit": "kg",
            "source_type": "customer",
        }
        res = self.client.post("/api/community-prices", json=payload)
        self.assertEqual(res.status_code, 422)
        self.assertIn("Locality with ID 'loc_non_existent_999' not found", res.json()["detail"])

    def test_invalid_source_type_rejected(self):
        """Source type must be customer or vendor."""
        payload = {
            "commodity_id": "tomato",
            "locality_id": "loc_katpadi",
            "price": 30.0,
            "unit": "kg",
            "source_type": "administrator",
        }
        res = self.client.post("/api/community-prices", json=payload)
        self.assertEqual(res.status_code, 422)
        self.assertIn("Invalid source_type", res.json()["detail"])

    # -----------------------------------------------------------------------
    # 4. Timestamp Validation
    # -----------------------------------------------------------------------
    def test_future_timestamp_rejected(self):
        """Timestamps in the future beyond 2 hours must be rejected."""
        far_future = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        payload = {
            "commodity_id": "tomato",
            "locality_id": "loc_katpadi",
            "price": 28.0,
            "unit": "kg",
            "source_type": "customer",
            "observed_at": far_future,
        }
        res = self.client.post("/api/community-prices", json=payload)
        self.assertEqual(res.status_code, 422)
        self.assertIn("cannot be in the future", res.json()["detail"])

    # -----------------------------------------------------------------------
    # 5. Duplicate Detection & Submission Preservation
    # -----------------------------------------------------------------------
    def test_conservative_duplicate_detection_preserves_submission(self):
        """
        Duplicate submissions are flagged with is_duplicate=True and duplicate_of_id,
        but the record is preserved in the database (never dropped or deleted).
        """
        t = (self.test_clock - timedelta(hours=3))
        # Initial submission
        payload_1 = {
            "commodity_id": "tomato",
            "locality_id": "loc_katpadi",
            "price": 28.0,
            "unit": "kg",
            "source_type": "customer",
            "contributor_id": "contributor_dup_test",
            "observed_at": t.isoformat(),
        }
        res_1 = self.client.post("/api/community-prices", json=payload_1)
        self.assertEqual(res_1.status_code, 201)
        id_1 = res_1.json()["observation"]["id"]
        self.assertFalse(res_1.json()["is_duplicate"])

        # Second submission: same commodity, locality, price, unit, contributor within 12h
        payload_2 = {
            "commodity_id": "tomato",
            "locality_id": "loc_katpadi",
            "price": 28.0,
            "unit": "kg",
            "source_type": "customer",
            "contributor_id": "contributor_dup_test",
            "observed_at": (t + timedelta(minutes=15)).isoformat(),
        }
        res_2 = self.client.post("/api/community-prices", json=payload_2)
        self.assertEqual(res_2.status_code, 201)
        data_2 = res_2.json()

        # Flagged as duplicate
        self.assertTrue(data_2["is_duplicate"])
        self.assertEqual(data_2["duplicate_of_id"], id_1)
        self.assertIn("Matches existing observation", data_2["duplicate_reason"])

        # Verification: Original submission is preserved in the database
        obs_1 = self.session.get(CommunityPriceObservation, id_1)
        obs_2 = self.session.get(CommunityPriceObservation, data_2["observation"]["id"])
        self.assertIsNotNone(obs_1)
        self.assertIsNotNone(obs_2)
        self.assertFalse(obs_1.is_duplicate)
        self.assertTrue(obs_2.is_duplicate)

    # -----------------------------------------------------------------------
    # 6. Unusual But Valid Prices (Outliers Preserved)
    # -----------------------------------------------------------------------
    def test_unusual_valid_price_is_stored_and_flagged(self):
        """Unusual prices (e.g. ₹220/kg tomato) remain stored and tagged without rejection."""
        payload = {
            "commodity_id": "tomato",
            "locality_id": "loc_katpadi",
            "price": 220.0,
            "unit": "kg",
            "source_type": "customer",
            "contributor_id": "cust_luxury_store",
            "observed_at": (self.test_clock - timedelta(hours=1)).isoformat(),
        }
        res = self.client.post("/api/community-prices", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["status"], "recorded")
        self.assertEqual(data["observation"]["price"], 220.0)
        self.assertTrue(any("unusual" in w for w in data["warnings"]))

        # Check retrieval: outlier is preserved and tagged with is_outlier=True
        list_res = self.client.get("/api/community-prices?commodity_id=tomato&locality_id=loc_katpadi&exclude_duplicates=false")
        self.assertEqual(list_res.status_code, 200)
        items = list_res.json()["items"]
        outlier_item = next((i for i in items if i["id"] == data["observation"]["id"]), None)
        self.assertIsNotNone(outlier_item)
        self.assertTrue(outlier_item["is_outlier"])

    # -----------------------------------------------------------------------
    # 7. Query Filters, 2-Day Window, and Pagination
    # -----------------------------------------------------------------------
    def test_query_filters_and_pagination(self):
        """Verify filtering by commodity, locality, demo window, and pagination limits."""
        res = self.client.get("/api/community-prices?commodity_id=tomato&locality_id=loc_katpadi&window_days=2")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertGreaterEqual(data["total_count"], 1)
        self.assertEqual(data["window_days"], 2)
        self.assertIn("summary", data)
        self.assertIn("median_price", data["summary"])
        self.assertIn("average_price", data["summary"])

        # Pagination check
        paginated_res = self.client.get("/api/community-prices?commodity_id=tomato&limit=1&offset=0")
        self.assertEqual(paginated_res.status_code, 200)
        self.assertEqual(len(paginated_res.json()["items"]), 1)

    # -----------------------------------------------------------------------
    # 8. Route Compatibility
    # -----------------------------------------------------------------------
    def test_vite_proxy_and_direct_api_route_parity(self):
        """Endpoints are accessible with or without /api prefix for Vite proxy compatibility."""
        res_with_api = self.client.get("/api/community-prices?commodity_id=tomato")
        res_without_api = self.client.get("/community-prices?commodity_id=tomato")
        self.assertEqual(res_with_api.status_code, 200)
        self.assertEqual(res_without_api.status_code, 200)
        self.assertEqual(res_with_api.json()["total_count"], res_without_api.json()["total_count"])


if __name__ == "__main__":
    unittest.main()
