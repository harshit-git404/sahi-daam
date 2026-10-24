from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
import unittest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.pricing.engine import calculate_fair_price
from backend.pricing.reconciliation_service import (
    PricingReconciliationService,
    ReconciliationPolicy,
    ReconciliationResult,
    EligibleObservationsBreakdown,
)
from backend.database.models import CommunityPriceObservation


class MockObservation:
    """Mock observation matching CommunityPriceObservation schema."""
    def __init__(
        self,
        price: float,
        unit: str = "kg",
        observed_at: datetime = None,
        is_duplicate: bool = False,
        normalized_price_per_kg: float = None,
    ):
        self.price = price
        self.unit = unit
        self.observed_at = observed_at or datetime.now(timezone.utc)
        self.is_duplicate = is_duplicate
        self.normalized_price_per_kg = normalized_price_per_kg if normalized_price_per_kg is not None else price


class TestPricingReconciliationService(unittest.TestCase):
    """Exhaustive unit test suite for Phase 5 Adaptive Community Reconciliation."""

    def setUp(self):
        self.clock = datetime(2026, 10, 24, 12, 0, 0, tzinfo=timezone.utc)
        self.policy = ReconciliationPolicy(
            window_days=2,
            min_sample_size=10,
            base_alpha=0.20,
            alpha_per_additional_sample=0.02,
            max_alpha=0.40,
            markup_min_pct=30.0,
            markup_max_pct=45.0,
        )

    # -----------------------------------------------------------------------
    # 1. No Community Observations
    # -----------------------------------------------------------------------
    def test_no_community_observations(self):
        """When no community data exists, alpha=0, baseline remains active."""
        res = PricingReconciliationService.reconcile(
            commodity_id="tomato",
            wholesale_price=20.0,
            transport_cost=2.0,
            transport_status="available",
            community_observations=[],
            policy=self.policy,
            test_clock=self.clock,
        )
        self.assertEqual(res.calculation_status, "TRANSPORT_AWARE_BASELINE")
        self.assertEqual(res.cost_basis_per_kg, 22.0)
        self.assertEqual(res.reconciliation_weight_alpha, 0.0)
        self.assertEqual(res.community_sample_size, 0)
        self.assertIsNone(res.community_estimate)
        self.assertEqual(res.baseline_range.min, 28.6)  # 22 * 1.30
        self.assertEqual(res.baseline_range.max, 31.9)  # 22 * 1.45
        self.assertEqual(res.reconciled_range.min, res.baseline_range.min)
        self.assertEqual(res.reconciled_range.max, res.baseline_range.max)

    # -----------------------------------------------------------------------
    # 2. Fewer than 10 Eligible Reports (Insufficient Samples)
    # -----------------------------------------------------------------------
    def test_fewer_than_10_eligible_reports_yields_zero_alpha(self):
        """Alpha must strictly be 0.0 when independent eligible reports < 10."""
        obs = [
            MockObservation(price=30.0, observed_at=self.clock - timedelta(hours=i))
            for i in range(9)  # 9 reports
        ]
        res = PricingReconciliationService.reconcile(
            commodity_id="tomato",
            wholesale_price=20.0,
            transport_cost=2.0,
            transport_status="available",
            community_observations=obs,
            policy=self.policy,
            test_clock=self.clock,
        )
        self.assertEqual(res.reconciliation_weight_alpha, 0.0)
        self.assertFalse(res.is_sample_sufficient)
        self.assertEqual(res.community_sample_size, 9)
        self.assertEqual(res.community_estimate, 30.0)
        # Reconciled range must strictly equal baseline range
        self.assertEqual(res.reconciled_range.mid, res.baseline_range.mid)

    # -----------------------------------------------------------------------
    # 3. Exactly 10 Eligible Reports (Threshold Activated)
    # -----------------------------------------------------------------------
    def test_exactly_10_eligible_reports_activates_base_alpha(self):
        """At exactly 10 reports, alpha=0.20 and community median influences price."""
        # 10 observations with median 35.0
        prices = [32.0, 33.0, 34.0, 34.5, 35.0, 35.0, 36.0, 36.5, 37.0, 38.0]
        obs = [
            MockObservation(price=p, observed_at=self.clock - timedelta(hours=i))
            for i, p in enumerate(prices)
        ]
        res = PricingReconciliationService.reconcile(
            commodity_id="tomato",
            wholesale_price=20.0,
            transport_cost=2.0,
            transport_status="available",
            community_observations=obs,
            policy=self.policy,
            test_clock=self.clock,
        )
        self.assertEqual(res.calculation_status, "TRANSPORT_AWARE_RECONCILED")
        self.assertEqual(res.reconciliation_weight_alpha, 0.20)
        self.assertTrue(res.is_sample_sufficient)
        self.assertEqual(res.community_sample_size, 10)
        self.assertEqual(res.community_estimate, 35.0)

        # Baseline mid = (28.6 + 31.9) / 2 = 30.25
        # Reconciled mid = 0.80 * 30.25 + 0.20 * 35.0 = 24.20 + 7.00 = 31.20
        self.assertEqual(res.reconciled_range.mid, 31.20)
        self.assertGreater(res.reconciled_range.mid, res.baseline_range.mid)

    # -----------------------------------------------------------------------
    # 4. Adaptive Alpha Scaling & Clamping
    # -----------------------------------------------------------------------
    def test_adaptive_alpha_scaling_and_max_cap(self):
        """Alpha scales by +0.02 per sample above 10, clamped at max_alpha (0.40)."""
        # 15 reports -> alpha = 0.20 + 5 * 0.02 = 0.30
        alpha_15, _ = PricingReconciliationService.calculate_adaptive_alpha(15, self.policy)
        self.assertEqual(alpha_15, 0.30)

        # 25 reports -> 0.20 + 15 * 0.02 = 0.50 -> clamped to 0.40
        alpha_25, _ = PricingReconciliationService.calculate_adaptive_alpha(25, self.policy)
        self.assertEqual(alpha_25, 0.40)

    # -----------------------------------------------------------------------
    # 5. Flagged Duplicates Excluded from Sample Count
    # -----------------------------------------------------------------------
    def test_flagged_duplicates_excluded_from_sample_count(self):
        """12 total observations where 4 are flagged duplicates results in 8 independent reports -> alpha=0."""
        obs = []
        for i in range(8):
            obs.append(MockObservation(price=28.0, is_duplicate=False))
        for i in range(4):
            obs.append(MockObservation(price=28.0, is_duplicate=True))

        res = PricingReconciliationService.reconcile(
            commodity_id="tomato",
            wholesale_price=20.0,
            community_observations=obs,
            policy=self.policy,
            test_clock=self.clock,
        )
        self.assertEqual(res.observation_breakdown.total_found, 12)
        self.assertEqual(res.observation_breakdown.excluded_duplicates_count, 4)
        self.assertEqual(res.community_sample_size, 8)
        self.assertEqual(res.reconciliation_weight_alpha, 0.0)

    # -----------------------------------------------------------------------
    # 6. Stale Observations Outside Window Excluded
    # -----------------------------------------------------------------------
    def test_stale_observations_outside_window_excluded(self):
        """Observations older than 2 days are excluded from the demo window sample."""
        obs = []
        # 5 recent observations (1 day old)
        for i in range(5):
            obs.append(MockObservation(price=28.0, observed_at=self.clock - timedelta(days=1)))
        # 8 stale observations (3 days old)
        for i in range(8):
            obs.append(MockObservation(price=28.0, observed_at=self.clock - timedelta(days=3)))

        res = PricingReconciliationService.reconcile(
            commodity_id="tomato",
            wholesale_price=20.0,
            community_observations=obs,
            policy=self.policy,
            test_clock=self.clock,
        )
        self.assertEqual(res.observation_breakdown.excluded_stale_count, 8)
        self.assertEqual(res.community_sample_size, 5)
        self.assertEqual(res.reconciliation_weight_alpha, 0.0)

    # -----------------------------------------------------------------------
    # 7. Non-Weight Units Excluded from Weight-Based Reconciliation
    # -----------------------------------------------------------------------
    def test_non_weight_units_excluded_without_blind_conversion(self):
        """Reports quoted per piece or bunch must NOT be converted blindly to kg."""
        obs = [
            MockObservation(price=5.0, unit="piece"),
            MockObservation(price=10.0, unit="bunch"),
            MockObservation(price=30.0, unit="kg"),
        ]
        res = PricingReconciliationService.reconcile(
            commodity_id="tomato",
            wholesale_price=20.0,
            community_observations=obs,
            policy=self.policy,
            test_clock=self.clock,
        )
        self.assertEqual(res.observation_breakdown.excluded_non_weight_unit_count, 2)
        self.assertEqual(res.community_sample_size, 1)

    # -----------------------------------------------------------------------
    # 8. Unusual Valid Prices (Outliers Preserved in Median)
    # -----------------------------------------------------------------------
    def test_unusual_valid_prices_preserved_in_median(self):
        """Outlier prices (e.g. ₹150/kg) are preserved and included in median evaluation."""
        # 10 observations with one high price
        prices = [26.0, 27.0, 28.0, 28.0, 29.0, 30.0, 30.0, 31.0, 32.0, 150.0]
        obs = [MockObservation(price=p, observed_at=self.clock - timedelta(hours=1)) for p in prices]

        res = PricingReconciliationService.reconcile(
            commodity_id="tomato",
            wholesale_price=20.0,
            community_observations=obs,
            policy=self.policy,
            test_clock=self.clock,
        )
        self.assertEqual(res.community_sample_size, 10)
        # Median of 10 items (sorted): 29.0 and 30.0 -> 29.5
        self.assertEqual(res.community_estimate, 29.5)

    # -----------------------------------------------------------------------
    # 9. Missing Transport -> Provisional Wholesale Baseline
    # -----------------------------------------------------------------------
    def test_missing_transport_labeled_provisional(self):
        """Missing transport must not be treated as zero transport cost."""
        res = PricingReconciliationService.reconcile(
            commodity_id="tomato",
            wholesale_price=20.0,
            transport_cost=None,
            transport_status="unavailable",
            community_observations=[],
            policy=self.policy,
            test_clock=self.clock,
        )
        self.assertEqual(res.calculation_status, "PROVISIONAL_WHOLESALE_BASELINE")
        self.assertTrue(res.is_provisional_wholesale_only)
        self.assertEqual(res.cost_basis_per_kg, 20.0)
        self.assertTrue(any("provisional wholesale-based baseline" in w for w in res.warnings))

    # -----------------------------------------------------------------------
    # 10. Missing Wholesale Price -> UNAVAILABLE (No Fabrication)
    # -----------------------------------------------------------------------
    def test_missing_wholesale_is_unavailable(self):
        """When wholesale data is missing, price is UNAVAILABLE (never fabricated)."""
        res = PricingReconciliationService.reconcile(
            commodity_id="tomato",
            wholesale_price=None,
            transport_cost=2.0,
            transport_status="available",
            community_observations=[],
        )
        self.assertEqual(res.calculation_status, "UNAVAILABLE")
        self.assertIsNone(res.cost_basis_per_kg)
        self.assertIsNone(res.baseline_range)
        self.assertIsNone(res.reconciled_range)

    # -----------------------------------------------------------------------
    # 11. Range Consistency & Non-Negativity
    # -----------------------------------------------------------------------
    def test_range_consistency_with_freshness_deductions(self):
        """Freshness deductions (-5 for spoiled) preserve min <= mid <= max and non-negativity."""
        res = PricingReconciliationService.reconcile(
            commodity_id="tomato",
            wholesale_price=8.0,
            transport_cost=1.0,
            transport_status="available",
            quality_adjustment=-5,
            quality_adjustment_meaning="Spoiled produce deduction",
            community_observations=[],
            policy=self.policy,
            test_clock=self.clock,
        )
        # Cost basis = 9.0
        # raw min = 9 * 1.30 - 5 = 11.7 - 5 = 6.7
        # raw max = 9 * 1.45 - 5 = 13.05 - 5 = 8.05
        self.assertGreaterEqual(res.reconciled_range.min, 0.0)
        self.assertLessEqual(res.reconciled_range.min, res.reconciled_range.max)
        self.assertAlmostEqual(res.reconciled_range.mid, (res.reconciled_range.min + res.reconciled_range.max) / 2.0, places=2)

    # -----------------------------------------------------------------------
    # 12. Backward Compatibility with Existing Pricing
    # -----------------------------------------------------------------------
    def test_backward_compatibility_with_existing_engine(self):
        """When transport is 0/unavailable and alpha=0, baseline matches calculate_fair_price exactly."""
        wholesale = 24.0
        q_adj = -2
        legacy = calculate_fair_price(wholesale, 30.0, 45.0, q_adj)

        reconciled = PricingReconciliationService.reconcile(
            commodity_id="tomato",
            wholesale_price=wholesale,
            transport_cost=None,
            transport_status="unavailable",
            quality_adjustment=q_adj,
            community_observations=[],
            policy=self.policy,
            test_clock=self.clock,
        )

        self.assertEqual(reconciled.baseline_range.min, legacy["min"])
        self.assertEqual(reconciled.baseline_range.max, legacy["max"])

    # -----------------------------------------------------------------------
    # 13. Deterministic Results
    # -----------------------------------------------------------------------
    def test_deterministic_output(self):
        """Running reconciliation repeatedly with identical inputs yields bit-for-bit identical results."""
        obs = [MockObservation(price=30.0 + i, observed_at=self.clock - timedelta(hours=i)) for i in range(12)]
        results = [
            PricingReconciliationService.reconcile(
                commodity_id="tomato",
                wholesale_price=20.0,
                transport_cost=2.5,
                transport_status="available",
                community_observations=obs,
                policy=self.policy,
                test_clock=self.clock,
            )
            for _ in range(50)
        ]
        first = results[0]
        for r in results[1:]:
            self.assertEqual(first.reconciled_range.min, r.reconciled_range.min)
            self.assertEqual(first.reconciled_range.max, r.reconciled_range.max)
            self.assertEqual(first.reconciliation_weight_alpha, r.reconciliation_weight_alpha)


if __name__ == "__main__":
    unittest.main()
