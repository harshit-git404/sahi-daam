import sys
from pathlib import Path
import unittest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.pricing.engine import calculate_fair_price, calculate_haggle_verdict



class TestPricingEngine(unittest.TestCase):
    """Regression tests for fair-price and haggle-verdict calculations."""

    def test_calculate_fair_price_nominal(self):
        """Verify normal wholesale-to-retail range calculation with 0 quality adjustment."""
        # Wholesale ₹20/kg, 30% to 45% markup -> ₹26 to ₹29
        result = calculate_fair_price(20.0, 30.0, 45.0, 0)
        self.assertEqual(result["min"], 26.0)
        self.assertEqual(result["max"], 29.0)

    def test_calculate_fair_price_with_negative_freshness_adjustment(self):
        """Verify that negative quality deductions (e.g. -2 for slightly aged) reduce fair bounds."""
        # Wholesale ₹20/kg, 30% to 45% markup, -2 quality adj -> ₹24 to ₹27
        result = calculate_fair_price(20.0, 30.0, 45.0, -2)
        self.assertEqual(result["min"], 24.0)
        self.assertEqual(result["max"], 27.0)

    def test_calculate_fair_price_with_severe_negative_adjustment(self):
        """Verify -5 quality deduction for spoiled produce."""
        result = calculate_fair_price(20.0, 30.0, 45.0, -5)
        self.assertEqual(result["min"], 21.0)
        self.assertEqual(result["max"], 24.0)

    def test_calculate_fair_price_zero_wholesale(self):
        """Wholesale 0 with 0 adjustment must return 0."""
        result = calculate_fair_price(0.0, 30.0, 45.0, 0)
        self.assertEqual(result["min"], 0.0)
        self.assertEqual(result["max"], 0.0)

    def test_calculate_fair_price_non_negative_clamp(self):
        """Price range should never go below 0 even with large negative adjustments."""
        result = calculate_fair_price(5.0, 10.0, 20.0, -20)
        self.assertGreaterEqual(result["min"], 0.0)
        self.assertGreaterEqual(result["max"], 0.0)

    def test_calculate_fair_price_min_max_ordering(self):
        """Guarantee that max_price is always >= min_price."""
        result = calculate_fair_price(30.0, 50.0, 20.0, 0)  # Inverted markup inputs
        self.assertGreaterEqual(result["max"], result["min"])

    def test_calculate_fair_price_rounding(self):
        """Verify float precision is rounded to 2 decimal places."""
        result = calculate_fair_price(22.33, 33.333, 44.444, 0)
        self.assertEqual(result["min"], round(result["min"], 2))
        self.assertEqual(result["max"], round(result["max"], 2))

    # --- Haggle Verdict Tests ---

    def test_haggle_verdict_high(self):
        """Asking price above fair_max must return verdict HIGH and midpoint counter-offer."""
        fair_range = {"min": 30.0, "max": 40.0}
        result = calculate_haggle_verdict(50.0, fair_range)
        self.assertEqual(result["verdict"], "HIGH")
        self.assertGreater(result["deviation_pct"], 0)
        self.assertEqual(result["suggested_price"], 35.0)  # Midpoint of 30 and 40
        self.assertEqual(result["suggested_price_min"], 30.0)
        self.assertEqual(result["suggested_price_max"], 40.0)
        self.assertIn("above the upper fair-price boundary", result["explanation"])

    def test_haggle_verdict_low(self):
        """Asking price below fair_min must return verdict LOW and accept asking price."""
        fair_range = {"min": 30.0, "max": 40.0}
        result = calculate_haggle_verdict(25.0, fair_range)
        self.assertEqual(result["verdict"], "LOW")
        self.assertLess(result["deviation_pct"], 0)
        self.assertEqual(result["suggested_price"], 25.0)  # Asking price accepted
        self.assertIn("below the calculated fair-price range", result["explanation"])

    def test_haggle_verdict_fair_within_range(self):
        """Asking price inside range must return verdict FAIR and accept asking price."""
        fair_range = {"min": 30.0, "max": 40.0}
        result = calculate_haggle_verdict(35.0, fair_range)
        self.assertEqual(result["verdict"], "FAIR")
        self.assertEqual(result["suggested_price"], 35.0)
        self.assertIn("within the verified fair-price range", result["explanation"])

    def test_haggle_verdict_boundary_exact_min(self):
        """Asking price exactly equal to fair_min should be FAIR."""
        fair_range = {"min": 30.0, "max": 40.0}
        result = calculate_haggle_verdict(30.0, fair_range)
        self.assertEqual(result["verdict"], "FAIR")
        self.assertEqual(result["deviation_pct"], 0.0)
        self.assertEqual(result["suggested_price"], 30.0)

    def test_haggle_verdict_boundary_exact_max(self):
        """Asking price exactly equal to fair_max should be FAIR."""
        fair_range = {"min": 30.0, "max": 40.0}
        result = calculate_haggle_verdict(40.0, fair_range)
        self.assertEqual(result["verdict"], "FAIR")
        self.assertEqual(result["deviation_pct"], 0.0)
        self.assertEqual(result["suggested_price"], 40.0)

    def test_haggle_verdict_zero_baseline_safety(self):
        """Asking price when fair boundaries are 0.0 must not cause ZeroDivisionError."""
        fair_range = {"min": 0.0, "max": 0.0}
        result = calculate_haggle_verdict(10.0, fair_range)
        self.assertEqual(result["verdict"], "HIGH")
        self.assertEqual(result["deviation_pct"], 0.0)


if __name__ == "__main__":
    unittest.main()
