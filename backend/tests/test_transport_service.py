import math
import sys
from pathlib import Path
import unittest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.services.transport_service import (
    TransportCostService,
    TransportCalculationInput,
    TransportCalculationResult,
    TripDirection,
    CalculationStatus,
    TransportMethod,
)
from backend.database.connection import init_db, create_engine, sessionmaker
from backend.database.seed import seed_database


class TestTransportCostService(unittest.TestCase):
    """Exhaustive test suite for deterministic transport-cost service."""

    def setUp(self):
        # Baseline valid input for a mini-truck
        self.baseline_input = TransportCalculationInput(
            source_mandi_id="mandi_vellore_central",
            destination_locality_id="loc_katpadi",
            distance_km=20.0,
            distance_provenance="verified_route",
            trip_direction=TripDirection.ONE_WAY,
            vehicle_type="mini_truck",
            fuel_consumption_litres_per_km=0.1,  # 10 km/L
            fuel_price_per_litre=100.0,  # ₹100/L
            base_rate_per_km=5.0,  # ₹5/km wear
            driver_allowance=100.0,
            loading_unloading_fee=50.0,
            effective_load_kg=500.0,  # 500 kg
        )

    # -----------------------------------------------------------------------
    # 1. Deterministic Output
    # -----------------------------------------------------------------------
    def test_deterministic_output(self):
        """Repeated calculations with identical inputs must produce bit-for-bit identical results."""
        results = [TransportCostService.calculate(self.baseline_input) for _ in range(50)]
        first = results[0]
        for r in results[1:]:
            self.assertEqual(first.status, r.status)
            self.assertEqual(first.cost_per_kg, r.cost_per_kg)
            self.assertEqual(first.total_trip_cost, r.total_trip_cost)
            self.assertEqual(first.distance_traversed_km, r.distance_traversed_km)
            self.assertEqual(first.cost_breakdown, r.cost_breakdown)

    # -----------------------------------------------------------------------
    # 2. Fuel-Price Sensitivity
    # -----------------------------------------------------------------------
    def test_fuel_price_sensitivity(self):
        """Increasing fuel price must scale fuel cost linearly by exact formula."""
        # Baseline: 20 km * 0.1 L/km * 100 ₹/L = ₹200 fuel cost
        # Fixed + km: (20 * 5) + 100 + 50 = ₹250
        # Total = ₹450 -> cost/kg = 450 / 500 = ₹0.90/kg
        res_100 = TransportCostService.calculate(self.baseline_input)
        self.assertEqual(res_100.cost_breakdown["fuel_cost"], 200.0)
        self.assertEqual(res_100.total_trip_cost, 450.0)
        self.assertEqual(res_100.cost_per_kg, 0.90)

        # Higher price: ₹120/L -> fuel cost = 20 * 0.1 * 120 = ₹240 (increase of ₹40)
        input_120 = self.baseline_input.model_copy(update={"fuel_price_per_litre": 120.0})
        res_120 = TransportCostService.calculate(input_120)
        self.assertEqual(res_120.cost_breakdown["fuel_cost"], 240.0)
        self.assertEqual(res_120.total_trip_cost, 490.0)
        self.assertEqual(res_120.cost_per_kg, 0.98)

        # Difference must equal: distance * fuel_consumption * delta_price
        expected_delta = 20.0 * 0.1 * (120.0 - 100.0)
        actual_delta = res_120.total_trip_cost - res_100.total_trip_cost
        self.assertAlmostEqual(actual_delta, expected_delta, places=4)

    # -----------------------------------------------------------------------
    # 3. Distance Sensitivity
    # -----------------------------------------------------------------------
    def test_distance_sensitivity(self):
        """Doubling distance must double distance-dependent costs (fuel and km rate)."""
        input_40km = self.baseline_input.model_copy(update={"distance_km": 40.0})
        res_40km = TransportCostService.calculate(input_40km)

        # At 40km: fuel = 40 * 0.1 * 100 = 400 (was 200)
        # km_rate = 40 * 5 = 200 (was 100)
        # fixed = 150 (unchanged)
        # Total = 400 + 200 + 150 = 750
        self.assertEqual(res_40km.cost_breakdown["fuel_cost"], 400.0)
        self.assertEqual(res_40km.cost_breakdown["km_operating_cost"], 200.0)
        self.assertEqual(res_40km.cost_breakdown["fixed_operating_costs"], 150.0)
        self.assertEqual(res_40km.total_trip_cost, 750.0)
        self.assertEqual(res_40km.cost_per_kg, 1.50)

    # -----------------------------------------------------------------------
    # 4. Load-Capacity Sensitivity
    # -----------------------------------------------------------------------
    def test_load_capacity_sensitivity(self):
        """Doubling effective load with constant trip cost must cut ₹/kg in half."""
        # Baseline total cost = ₹450 with 500 kg = ₹0.90/kg
        input_1000kg = self.baseline_input.model_copy(update={"effective_load_kg": 1000.0})
        res_1000kg = TransportCostService.calculate(input_1000kg)

        self.assertEqual(res_1000kg.total_trip_cost, 450.0)
        self.assertEqual(res_1000kg.cost_per_kg, 0.45)
        self.assertAlmostEqual(res_1000kg.cost_per_kg * 2, 0.90, places=4)

    # -----------------------------------------------------------------------
    # 5. One-Way vs Round-Trip & No Double-Counting
    # -----------------------------------------------------------------------
    def test_one_way_and_round_trip_handling(self):
        """Round-trip journey doubles traversed distance and operating costs when distance is one-way."""
        input_round_trip = self.baseline_input.model_copy(
            update={"trip_direction": TripDirection.ROUND_TRIP, "distance_is_round_trip": False}
        )
        res_round = TransportCostService.calculate(input_round_trip)

        # Traversed distance should be 40.0 km
        self.assertEqual(res_round.distance_traversed_km, 40.0)
        # Fuel cost: 40 * 0.1 * 100 = 400
        self.assertEqual(res_round.cost_breakdown["fuel_cost"], 400.0)
        # km rate: 40 * 5 = 200
        self.assertEqual(res_round.cost_breakdown["km_operating_cost"], 200.0)
        # Total = 400 + 200 + 150 = 750 -> 750 / 500 = 1.50
        self.assertEqual(res_round.total_trip_cost, 750.0)
        self.assertEqual(res_round.cost_per_kg, 1.50)

    def test_no_double_counting_when_distance_is_already_round_trip(self):
        """When distance is already flagged as round-trip, round_trip mode must NOT double it again."""
        input_already_round = self.baseline_input.model_copy(
            update={
                "distance_km": 40.0,
                "trip_direction": TripDirection.ROUND_TRIP,
                "distance_is_round_trip": True,
            }
        )
        res = TransportCostService.calculate(input_already_round)

        # Distance traversed must stay 40.0 km, NOT become 80.0 km
        self.assertEqual(res.distance_traversed_km, 40.0)
        self.assertEqual(res.total_trip_cost, 750.0)
        self.assertEqual(res.cost_per_kg, 1.50)

    # -----------------------------------------------------------------------
    # 6. Fuel Economy (km/L) Specification
    # -----------------------------------------------------------------------
    def test_fuel_economy_km_per_litre_conversion(self):
        """Specifying fuel_economy_km_per_litre (e.g. 10 km/L) must accurately convert to 0.1 L/km."""
        input_economy = self.baseline_input.model_copy(
            update={
                "fuel_consumption_litres_per_km": None,
                "fuel_economy_km_per_litre": 10.0,
            }
        )
        res = TransportCostService.calculate(input_economy)
        self.assertEqual(res.cost_breakdown["fuel_cost"], 200.0)
        self.assertEqual(res.cost_per_kg, 0.90)

    # -----------------------------------------------------------------------
    # 7. Configured Rate Fallbacks
    # -----------------------------------------------------------------------
    def test_configured_trip_cost_fallback(self):
        """When vehicle parameters are missing, fallback to configured flat per-trip rate."""
        rate_trip_input = TransportCalculationInput(
            distance_km=None,  # No distance
            effective_load_kg=400.0,
            configured_trip_cost=800.0,
            rate_provenance="configured_market_charter",
        )
        res = TransportCostService.calculate(rate_trip_input)

        self.assertEqual(res.status, CalculationStatus.AVAILABLE)
        self.assertEqual(res.transport_method, TransportMethod.CONFIGURED_TRIP_RATE)
        self.assertEqual(res.total_trip_cost, 800.0)
        self.assertEqual(res.cost_per_kg, 2.0)  # 800 / 400
        self.assertEqual(res.provenance, "configured_market_charter")

    def test_configured_per_kg_rate_fallback(self):
        """When vehicle and distance parameters are missing, fallback to configured per-kg rate."""
        rate_kg_input = TransportCalculationInput(
            distance_km=None,
            effective_load_kg=300.0,
            configured_per_kg_rate=1.75,
            rate_provenance="verified_mandi_cartage_union",
        )
        res = TransportCostService.calculate(rate_kg_input)

        self.assertEqual(res.status, CalculationStatus.AVAILABLE)
        self.assertEqual(res.transport_method, TransportMethod.CONFIGURED_PER_KG_RATE)
        self.assertEqual(res.cost_per_kg, 1.75)
        self.assertEqual(res.total_trip_cost, 525.0)  # 1.75 * 300

    def test_configured_per_kg_rate_without_load(self):
        """Per-kg rate is directly available even if load is omitted."""
        rate_kg_input = TransportCalculationInput(
            configured_per_kg_rate=2.25,
            rate_provenance="configured_schedule",
        )
        res = TransportCostService.calculate(rate_kg_input)

        self.assertEqual(res.status, CalculationStatus.AVAILABLE)
        self.assertEqual(res.cost_per_kg, 2.25)
        self.assertIsNone(res.total_trip_cost)

    # -----------------------------------------------------------------------
    # 8. Missing Distance Handling
    # -----------------------------------------------------------------------
    def test_missing_distance_without_rates_is_unavailable(self):
        """Vehicle calculation attempted without distance returns UNAVAILABLE with clear warning."""
        no_dist_input = self.baseline_input.model_copy(update={"distance_km": None})
        res = TransportCostService.calculate(no_dist_input)

        self.assertEqual(res.status, CalculationStatus.UNAVAILABLE)
        self.assertIsNone(res.cost_per_kg)
        self.assertIsNone(res.total_trip_cost)
        self.assertTrue(any("Insufficient transport inputs" in w for w in res.warnings))

    # -----------------------------------------------------------------------
    # 9. Missing Rates Handling
    # -----------------------------------------------------------------------
    def test_missing_all_parameters_is_unavailable(self):
        """Empty input returns UNAVAILABLE without fabricating arbitrary default costs."""
        empty_input = TransportCalculationInput()
        res = TransportCostService.calculate(empty_input)

        self.assertEqual(res.status, CalculationStatus.UNAVAILABLE)
        self.assertIsNone(res.cost_per_kg)
        self.assertTrue(len(res.warnings) > 0)

    # -----------------------------------------------------------------------
    # 10. Zero or Negative Load Protection (Zero-Division Guard)
    # -----------------------------------------------------------------------
    def test_zero_load_protection(self):
        """Zero effective load must return UNAVAILABLE and not crash with ZeroDivisionError."""
        zero_load = self.baseline_input.model_copy(update={"effective_load_kg": 0.0})
        res = TransportCostService.calculate(zero_load)

        self.assertEqual(res.status, CalculationStatus.UNAVAILABLE)
        self.assertIsNone(res.cost_per_kg)
        self.assertTrue(any("positive effective load" in w for w in res.warnings))

    def test_negative_load_protection(self):
        """Negative effective load must return UNAVAILABLE with invalid input warning."""
        neg_load = self.baseline_input.model_copy(update={"effective_load_kg": -100.0})
        res = TransportCostService.calculate(neg_load)

        self.assertEqual(res.status, CalculationStatus.UNAVAILABLE)
        self.assertIsNone(res.cost_per_kg)
        self.assertTrue(any("negative values" in w for w in res.warnings))

    # -----------------------------------------------------------------------
    # 11. Invalid Numeric Values (Negative & NaN/Inf Protection)
    # -----------------------------------------------------------------------
    def test_negative_distance_protection(self):
        """Negative distance must be rejected as invalid numeric value."""
        neg_dist = self.baseline_input.model_copy(update={"distance_km": -15.0})
        res = TransportCostService.calculate(neg_dist)

        self.assertEqual(res.status, CalculationStatus.UNAVAILABLE)
        self.assertTrue(any("negative values" in w for w in res.warnings))

    def test_negative_fuel_price_protection(self):
        """Negative fuel price must be rejected as invalid numeric value."""
        neg_fuel = self.baseline_input.model_copy(update={"fuel_price_per_litre": -95.0})
        res = TransportCostService.calculate(neg_fuel)

        self.assertEqual(res.status, CalculationStatus.UNAVAILABLE)
        self.assertTrue(any("negative values" in w for w in res.warnings))

    def test_nan_numeric_value_protection(self):
        """NaN values must be rejected cleanly."""
        nan_input = self.baseline_input.model_copy(update={"distance_km": float("nan")})
        res = TransportCostService.calculate(nan_input)

        self.assertEqual(res.status, CalculationStatus.UNAVAILABLE)
        self.assertTrue(any("NaN or Infinite" in w for w in res.warnings))

    # -----------------------------------------------------------------------
    # 12. Database Integration Helper
    # -----------------------------------------------------------------------
    def test_calculate_from_database_profile(self):
        """Test resolving vehicle configurations directly from seeded database."""
        engine = create_engine("sqlite:///:memory:")
        init_db(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        seed_database(session)

        # Calculate using seeded mini_truck (14 km/L, 102.5 fuel, 14 km rate, 750kg load)
        # Distance: Vellore Mandi (reference 5.5 km)
        res = TransportCostService.calculate_from_database_profile(
            session=session,
            vehicle_type="mini_truck",
            mandi_id="mandi_vellore",
        )

        self.assertEqual(res.status, CalculationStatus.AVAILABLE)
        self.assertEqual(res.transport_method, TransportMethod.VEHICLE_OPERATING_COST)
        self.assertIsNotNone(res.cost_per_kg)
        self.assertGreater(res.cost_per_kg, 0.0)
        self.assertEqual(res.distance_km, 5.5)
        self.assertEqual(res.effective_load_kg, 750.0)

        session.close()
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
