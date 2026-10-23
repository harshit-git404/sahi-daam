import sys
from pathlib import Path
import unittest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.data.agmarknet.parser import parse_price, normalize_record
from backend.data.history import normalize_date, analyze_distinct_history
from backend.data.commodity_rules import normalize_quantity, classify_variants
from backend.data.retail_service import get_retail_prices, _normalize_commodity_id



class TestAgmarknetParser(unittest.TestCase):
    """Tests for Agmarknet price parsing and record normalization."""

    def test_parse_price_valid_numbers(self):
        self.assertEqual(parse_price(100), 100.0)
        self.assertEqual(parse_price("2500"), 2500.0)
        self.assertEqual(parse_price(" 32.5 "), 32.5)

    def test_parse_price_invalid_and_na(self):
        self.assertEqual(parse_price(None), 0.0)
        self.assertEqual(parse_price(""), 0.0)
        self.assertEqual(parse_price("   "), 0.0)
        self.assertEqual(parse_price("NA"), 0.0)
        self.assertEqual(parse_price("na"), 0.0)
        self.assertEqual(parse_price("invalid_number"), 0.0)

    def test_normalize_record_quintal_to_kg_conversion(self):
        """Agmarknet rates are ₹/Quintal (100 kg); parser must convert to ₹/kg (/ 100)."""
        raw_record = {
            "Commodity": "Tomato",
            "Variety": "Hybrid",
            "State": "Tamil Nadu",
            "District": "Vellore",
            "Market": " Vellore Mandi  ",
            "Arrival_Date": "20/08/2026",
            "Min_Price": "2000",
            "Max_Price": "2600",
            "Modal_Price": "2400",
        }
        normalized = normalize_record(raw_record)
        self.assertEqual(normalized["commodity"], "tomato")
        self.assertEqual(normalized["variety"], "Hybrid")
        self.assertEqual(normalized["state"], "Tamil Nadu")
        self.assertEqual(normalized["district"], "Vellore")
        self.assertEqual(normalized["market"], "Vellore Mandi")  # Stripped whitespace
        self.assertEqual(normalized["arrival_date"], "20/08/2026")
        self.assertEqual(normalized["min_price_per_kg"], 20.0)
        self.assertEqual(normalized["max_price_per_kg"], 26.0)
        self.assertEqual(normalized["modal_price_per_kg"], 24.0)
        self.assertEqual(normalized["source"], "data.gov.in/agmarknet")

    def test_normalize_record_lowercase_keys_fallback(self):
        """Verify fallback to lowercase keys for legacy or variant API schemas."""
        raw_record = {
            "commodity": "Onion",
            "variety": "Red",
            "state": "Maharashtra",
            "district": "Nashik",
            "market": "Lasalgaon",
            "arrival_date": "18/08/2026",
            "min_price": 1500,
            "max_price": 2100,
            "modal_price": 1800,
        }
        normalized = normalize_record(raw_record)
        self.assertEqual(normalized["commodity"], "onion")
        self.assertEqual(normalized["min_price_per_kg"], 15.0)
        self.assertEqual(normalized["max_price_per_kg"], 21.0)
        self.assertEqual(normalized["modal_price_per_kg"], 18.0)


class TestHistoricalAggregation(unittest.TestCase):
    """Tests for historical-price aggregation and trend calculation."""

    def test_normalize_date_formats(self):
        self.assertEqual(normalize_date("20/08/2026"), "2026-08-20")
        self.assertEqual(normalize_date("2026-08-20"), "2026-08-20")
        self.assertEqual(normalize_date("20-08-2026"), "2026-08-20")
        self.assertEqual(normalize_date("08/20/2026"), "2026-08-20")
        self.assertIsNone(normalize_date(""))
        self.assertIsNone(normalize_date(None))
        self.assertIsNone(normalize_date("not-a-date"))

    def test_analyze_distinct_history_empty(self):
        res = analyze_distinct_history([], "date", "price")
        self.assertEqual(res["trend"], "UNAVAILABLE")
        self.assertIsNone(res["current_value"])
        self.assertEqual(res["periods_available"], 0)
        self.assertEqual(res["history"], [])

    def test_analyze_distinct_history_trend_up(self):
        # Current price (most recent) is 30, earlier was 20. Average = 25, Change = +20% -> UP
        records = [
            {"date": "2026-08-20", "modal_price": 30.0},
            {"date": "2026-08-19", "modal_price": 20.0},
        ]
        res = analyze_distinct_history(records, "date", "modal_price", stable_threshold_pct=1.0)
        self.assertEqual(res["trend"], "UP")
        self.assertEqual(res["current_value"], 30.0)
        self.assertEqual(res["average_10_days"], 25.0)
        self.assertEqual(res["high_10_days"], 30.0)
        self.assertEqual(res["low_10_days"], 20.0)
        self.assertEqual(res["periods_available"], 2)

    def test_analyze_distinct_history_trend_down(self):
        # Current price is 15, earlier was 25. Average = 20, Change = -25% -> DOWN
        records = [
            {"date": "2026-08-20", "price": 15.0},
            {"date": "2026-08-19", "price": 25.0},
        ]
        res = analyze_distinct_history(records, "date", "price")
        self.assertEqual(res["trend"], "DOWN")
        self.assertEqual(res["current_value"], 15.0)

    def test_analyze_distinct_history_trend_stable(self):
        # Change within 1% threshold -> STABLE
        records = [
            {"date": "2026-08-20", "price": 100.5},
            {"date": "2026-08-19", "price": 100.0},
        ]
        res = analyze_distinct_history(records, "date", "price", stable_threshold_pct=1.0)
        self.assertEqual(res["trend"], "STABLE")

    def test_analyze_distinct_history_period_limit(self):
        # Create 15 distinct dates; must be limited to 10
        records = [{"date": f"2026-08-{i:02d}", "price": float(i)} for i in range(1, 16)]
        res = analyze_distinct_history(records, "date", "price", limit=10)
        self.assertEqual(res["periods_available"], 10)
        self.assertEqual(len(res["history"]), 10)
        # Most recent date should be 2026-08-15
        self.assertEqual(res["history"][0]["date"], "2026-08-15")


class TestCommodityRulesAndRetail(unittest.TestCase):
    """Tests for retail quantity parsing and retail reference pricing."""

    def test_normalize_quantity_kilograms(self):
        self.assertEqual(normalize_quantity("1 kg"), 1.0)
        self.assertEqual(normalize_quantity("2.5 kgs"), 2.5)
        self.assertEqual(normalize_quantity("1kg"), 1.0)

    def test_normalize_quantity_grams(self):
        self.assertEqual(normalize_quantity("500 g"), 0.5)
        self.assertEqual(normalize_quantity("250 gm"), 0.25)
        self.assertEqual(normalize_quantity("100 grams"), 0.1)

    def test_normalize_quantity_invalid(self):
        self.assertIsNone(normalize_quantity(""))
        self.assertIsNone(normalize_quantity(None))
        self.assertIsNone(normalize_quantity("bunch"))

    def test_classify_variants(self):
        variant_keywords = ["cherry", "organic", "hybrid", "desi"]
        self.assertEqual(classify_variants("Fresh Organic Cherry Tomatoes", variant_keywords), ["cherry", "organic"])
        self.assertEqual(classify_variants("Regular Tomato", variant_keywords), ["regular"])

    def test_retail_service_unsupported_commodity(self):
        result = get_retail_prices("dragonfruit", "Vellore")
        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertEqual(result["products"], [])
        self.assertIn("not available for 'dragonfruit'", result["message"])

    def test_retail_service_supported_commodity(self):
        result = get_retail_prices("tomato", "Vellore")
        # Tomato is supported; if snapshot has records, status is AVAILABLE
        self.assertIn(result["status"], ("AVAILABLE", "UNAVAILABLE"))
        if result["status"] == "AVAILABLE":
            self.assertGreater(len(result["products"]), 0)
            # Products must be sorted by price_per_kg ascending
            prices = [p["price_per_kg"] for p in result["products"]]
            self.assertEqual(prices, sorted(prices))
            self.assertIn("best_price_per_kg", result)
            self.assertIn("best_platform", result)


if __name__ == "__main__":
    unittest.main()
