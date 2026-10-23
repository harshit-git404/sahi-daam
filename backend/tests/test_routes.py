import base64
import sys
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi.testclient import TestClient

from backend.main import app
from backend.ml.gemini_analysis import GeminiUnavailable



TINY_JPEG_B64 = (
    "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////"
    "////////////////////////////////////////////////////wgALCAABAAEBAREA"
    "/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="
)


class TestRoutes(unittest.TestCase):
    """Integration tests for all FastAPI endpoints using TestClient with mocked external dependencies."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # -----------------------------------------------------------------------
    # Health endpoint
    # -----------------------------------------------------------------------
    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    # -----------------------------------------------------------------------
    # POST /scan-produce validation tests
    # -----------------------------------------------------------------------
    def test_scan_produce_missing_image_returns_400(self):
        """Simulation mode or missing-image requests must be strictly rejected with HTTP 400."""
        response = self.client.post("/scan-produce", json={"produce_type": "tomato"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("An image is required for produce analysis", response.json()["detail"])

    def test_scan_produce_empty_image_returns_400(self):
        response = self.client.post("/scan-produce", json={"image": ""})
        self.assertEqual(response.status_code, 400)
        self.assertIn("An image is required for produce analysis", response.json()["detail"])

    def test_scan_produce_invalid_base64_returns_400(self):
        response = self.client.post("/scan-produce", json={"image": "not-valid-base-64!!!"})
        self.assertEqual(response.status_code, 400)

    # -----------------------------------------------------------------------
    # POST /scan-produce ML execution & response shape
    # -----------------------------------------------------------------------
    @patch("backend.routers.scan.get_retail_prices")
    @patch("backend.routers.scan.get_mandi_prices")
    @patch("backend.routers.scan.analyze_with_gemini")
    def test_scan_produce_success_with_gemini(
        self, mock_gemini, mock_mandi, mock_retail
    ):
        mock_gemini.return_value = {
            "produce_type": "Tomato",
            "produce_confidence": 95.0,
            "freshness_label": "Fresh",
            "freshness_percent": 90,
            "freshness_note": "Firm and ripe",
            "quality_adjustment": 0,
            "quality_adjustment_label": "No deduction",
        }
        mock_mandi.return_value = {
            "records": [
                {
                    "commodity": "tomato",
                    "market": "Vellore",
                    "district": "Vellore",
                    "arrival_date": "20/08/2026",
                    "modal_price_per_kg": 20.0,
                    "min_price_per_kg": 18.0,
                    "max_price_per_kg": 22.0,
                }
            ]
        }
        mock_retail.return_value = {
            "status": "AVAILABLE",
            "commodity": "tomato",
            "products": [
                {
                    "platform": "blinkit",
                    "price_per_kg": 35.0,
                }
            ],
        }

        payload = {
            "image": f"data:image/jpeg;base64,{TINY_JPEG_B64}",
            "state": "Tamil Nadu",
            "district": "Vellore",
        }
        response = self.client.post("/scan-produce", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # ML result fields
        self.assertEqual(data["produce_type"], "Tomato")
        self.assertEqual(data["detected_produce_id"], "tomato")
        self.assertEqual(data["produce_confidence"], 95.0)
        self.assertEqual(data["analysis_provider"], "gemini")
        self.assertEqual(data["freshness_label"], "Fresh")
        self.assertEqual(data["freshness_percent"], 90)

        # Market & pricing fields
        self.assertEqual(data["market_status"], "AVAILABLE")
        self.assertEqual(data["wholesale_price"], 20.0)
        self.assertIsNotNone(data["fair_price_range"])
        self.assertEqual(data["fair_price_range"]["min"], 26.0)  # 20 * 1.30
        self.assertEqual(data["fair_price_range"]["max"], 29.0)  # 20 * 1.45
        self.assertEqual(data["pricing"]["fair_price_min"], 26.0)
        self.assertEqual(data["pricing"]["fair_price_max"], 29.0)

        # Retail references
        self.assertEqual(data["online_reference_min"], 35.0)
        self.assertEqual(data["online_reference_max"], 35.0)
        self.assertEqual(data["quickcommerce_price"]["price"], 35.0)

    @patch("backend.routers.scan.get_retail_prices")
    @patch("backend.routers.scan.get_mandi_prices")
    @patch("backend.routers.scan.predict_freshness")
    @patch("backend.routers.scan.identify_produce")
    @patch("backend.routers.scan.analyze_with_gemini")
    def test_scan_produce_gemini_fallback_to_local_ml(
        self, mock_gemini, mock_identify, mock_freshness, mock_mandi, mock_retail
    ):
        """When Gemini is unavailable, scan must seamlessly fall back to local ML inference."""
        mock_gemini.side_effect = GeminiUnavailable("Quota exceeded")
        mock_identify.return_value = {
            "produce_type": "Tomato",
            "produce_id": "tomato",
            "produce_confidence": 91.0,
        }
        mock_freshness.return_value = {
            "freshness_label": "Slightly Aged",
            "freshness_percent": 75,
            "freshness_note": "Usable soon",
            "quality_adjustment": -2,
            "quality_adjustment_label": "Slight deduction",
        }
        mock_mandi.return_value = {"records": []}
        mock_retail.return_value = {"status": "UNAVAILABLE", "products": []}

        payload = {"image": TINY_JPEG_B64}
        response = self.client.post("/scan-produce", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["analysis_provider"], "local_fallback")
        self.assertEqual(data["produce_type"], "Tomato")
        self.assertEqual(data["freshness_label"], "Slightly Aged")
        self.assertEqual(data["quality_adjustment"], -2)
        # When mandi returns 0 records, market_status is UNAVAILABLE
        self.assertEqual(data["market_status"], "UNAVAILABLE")
        self.assertIsNone(data["wholesale_price"])
        self.assertIsNone(data["fair_price_range"])

    @patch("backend.routers.scan.identify_produce")
    @patch("backend.routers.scan.analyze_with_gemini")
    def test_scan_produce_both_ml_paths_fail_returns_503(
        self, mock_gemini, mock_identify
    ):
        mock_gemini.side_effect = GeminiUnavailable("Network error")
        mock_identify.side_effect = RuntimeError("Local model weights missing")

        payload = {"image": TINY_JPEG_B64}
        response = self.client.post("/scan-produce", json=payload)
        self.assertEqual(response.status_code, 503)
        self.assertIn("Both Gemini and local produce analysis are currently unavailable", response.json()["detail"])

    # -----------------------------------------------------------------------
    # POST /haggle-check validation & response tests
    # -----------------------------------------------------------------------
    def test_haggle_check_valid_request(self):
        payload = {
            "asking_price": 50.0,
            "fair_price_min": 30.0,
            "fair_price_max": 40.0,
            "purchase_type": "street_vendor",
            "market_reference": 24.0,
            "online_reference_min": 45.0,
            "online_reference_max": 48.0,
        }
        response = self.client.post("/haggle-check", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["verdict"], "HIGH")
        self.assertEqual(data["suggested_price"], 35.0)
        self.assertEqual(data["market_reference"], 24.0)
        self.assertEqual(data["online_reference_min"], 45.0)
        self.assertEqual(data["online_reference_max"], 48.0)

    def test_haggle_check_invalid_purchase_type_returns_400(self):
        """Haggle check is only supported for street_vendor purchases."""
        payload = {
            "asking_price": 50.0,
            "fair_price_min": 30.0,
            "fair_price_max": 40.0,
            "purchase_type": "supermarket",
        }
        response = self.client.post("/haggle-check", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("only available for street-vendor purchases", response.json()["detail"])

    def test_haggle_check_inverted_range_returns_400(self):
        payload = {
            "asking_price": 50.0,
            "fair_price_min": 40.0,
            "fair_price_max": 30.0,  # Invalid: max < min
            "purchase_type": "street_vendor",
        }
        response = self.client.post("/haggle-check", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid fair-price range", response.json()["detail"])

    def test_haggle_check_zero_or_negative_asking_price_returns_422(self):
        payload = {
            "asking_price": 0.0,
            "fair_price_min": 30.0,
            "fair_price_max": 40.0,
            "purchase_type": "street_vendor",
        }
        response = self.client.post("/haggle-check", json=payload)
        self.assertEqual(response.status_code, 422)

    # -----------------------------------------------------------------------
    # Route / proxy compatibility tests (/market-price vs /api/market-price)
    # -----------------------------------------------------------------------
    @patch("backend.routers.scan.get_mandi_prices")
    def test_market_price_route_compatibility(self, mock_get_mandi):
        """Verify both direct path (/api/market-price) and Vite proxy rewritten path (/market-price) work."""
        mock_get_mandi.return_value = {
            "commodity": "tomato",
            "source": "data.gov.in/agmarknet",
            "records": [
                {
                    "commodity": "tomato",
                    "modal_price_per_kg": 25.0,
                }
            ],
        }

        # 1. Direct path /api/market-price
        resp_direct = self.client.get("/api/market-price?commodity=Tomato")
        self.assertEqual(resp_direct.status_code, 200)

        # 2. Vite rewritten path /market-price
        resp_rewritten = self.client.get("/market-price?commodity=Tomato")
        self.assertEqual(resp_rewritten.status_code, 200)

        # Both must return identical payloads
        self.assertEqual(resp_direct.json(), resp_rewritten.json())
        self.assertEqual(resp_rewritten.json()["records"][0]["modal_price_per_kg"], 25.0)

    # -----------------------------------------------------------------------
    # GET /retail-prices endpoint
    # -----------------------------------------------------------------------
    def test_retail_prices_route(self):
        response = self.client.get("/retail-prices?commodity=tomato")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("commodity", data)


if __name__ == "__main__":
    unittest.main()
