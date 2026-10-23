import sys
from pathlib import Path
import unittest
from datetime import datetime, timezone, timedelta

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from backend.database.connection import Base, init_db
from backend.database.models import (
    Locality,
    Mandi,
    WholesalePriceObservation,
    TransportConfiguration,
    Customer,
    Vendor,
    CommunityPriceObservation,
    CalculationRecord,
)
from backend.database.repositories import (
    LocalityRepository,
    MandiRepository,
    WholesalePriceRepository,
    TransportConfigRepository,
    CustomerRepository,
    VendorRepository,
    CommunityPriceRepository,
    CalculationRepository,
)
from backend.database.seed import seed_database


class TestDatabaseLayer(unittest.TestCase):
    """Tests for SQLite persistence layer, models, repositories, and repeatable mock seeding."""

    def setUp(self):
        # Use an isolated, in-memory SQLite database for each test
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        init_db(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.test_clock = datetime(2026, 10, 23, 12, 0, 0, tzinfo=timezone.utc)

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    # -----------------------------------------------------------------------
    # Table creation and non-destructive initialization
    # -----------------------------------------------------------------------
    def test_init_db_is_non_destructive(self):
        """Calling init_db multiple times must not drop or alter existing tables."""
        # Create an initial locality
        LocalityRepository.upsert(
            self.session,
            {"id": "loc_test", "name": "Test Locality", "pincode": "632001", "district": "Vellore", "state": "Tamil Nadu"}
        )
        self.session.commit()

        # Re-run init_db on the same engine
        init_db(self.engine)

        # Existing record must still be present and intact
        recheck = LocalityRepository.get_by_id(self.session, "loc_test")
        self.assertIsNotNone(recheck)
        self.assertEqual(recheck.name, "Test Locality")

    # -----------------------------------------------------------------------
    # Entity constraints and models
    # -----------------------------------------------------------------------
    def test_localities_multiple_neighborhoods_shared_pincode(self):
        """Verify that multiple distinct localities can share the same pincode."""
        summary = seed_database(self.session, base_time=self.test_clock)
        self.assertGreaterEqual(summary["localities_count"], 2)

        bagayam = LocalityRepository.get_by_id(self.session, "loc_bagayam")
        thorapadi = LocalityRepository.get_by_id(self.session, "loc_thorapadi")
        self.assertIsNotNone(bagayam)
        self.assertIsNotNone(thorapadi)
        self.assertNotEqual(bagayam.id, thorapadi.id)
        self.assertEqual(bagayam.pincode, thorapadi.pincode)  # Both 632002

    def test_mandis_and_distance_provenance(self):
        """Verify mandi persistence, distance reference, and provenance notes."""
        seed_database(self.session, base_time=self.test_clock)
        mandi = MandiRepository.get_by_id(self.session, "mandi_vellore")
        self.assertIsNotNone(mandi)
        self.assertEqual(mandi.market_name, "Vellore Mandi")
        self.assertEqual(mandi.distance_km_reference, 5.5)
        self.assertIn("Agmarknet", mandi.provenance_note)
        self.assertFalse(mandi.is_mock)

    def test_customers_and_vendors_are_strictly_separate(self):
        """Customer and vendor records must reside in separate tables with is_mock=True."""
        seed_database(self.session, base_time=self.test_clock)

        customers = CustomerRepository.list_all(self.session)
        vendors = VendorRepository.list_by_locality(self.session, "loc_katpadi")

        self.assertGreater(len(customers), 0)
        self.assertGreater(len(vendors), 0)

        customer_ids = {c.id for c in customers}
        vendor_ids = {v.id for v in vendors}

        # IDs must be disjoint and in separate tables
        self.assertTrue(customer_ids.isdisjoint(vendor_ids))
        self.assertTrue(all(c.is_mock for c in customers))
        self.assertTrue(all(v.is_mock for v in vendors))

    def test_transport_configuration_persistence(self):
        """Verify freight vehicle configuration fields and active status."""
        seed_database(self.session, base_time=self.test_clock)

        mini_truck = TransportConfigRepository.get_by_vehicle_type(self.session, "mini_truck")
        self.assertIsNotNone(mini_truck)
        self.assertEqual(mini_truck.capacity_kg, 1000.0)
        self.assertEqual(mini_truck.effective_load_kg, 750.0)
        self.assertEqual(mini_truck.base_rate_per_km, 14.0)
        self.assertEqual(mini_truck.flat_fee, 150.0)
        self.assertTrue(mini_truck.is_active)

    # -----------------------------------------------------------------------
    # Repeatable seeding (idempotency)
    # -----------------------------------------------------------------------
    def test_seed_database_is_idempotent(self):
        """Seeding twice must result in identical record counts without multiplying rows."""
        summary1 = seed_database(self.session, base_time=self.test_clock)
        counts1 = {
            "localities": self.session.scalar(select(func.count(Locality.id))),
            "mandis": self.session.scalar(select(func.count(Mandi.id))),
            "wholesale": self.session.scalar(select(func.count(WholesalePriceObservation.id))),
            "transport": self.session.scalar(select(func.count(TransportConfiguration.id))),
            "customers": self.session.scalar(select(func.count(Customer.id))),
            "vendors": self.session.scalar(select(func.count(Vendor.id))),
            "community": self.session.scalar(select(func.count(CommunityPriceObservation.id))),
        }

        # Re-run seed on the same session
        summary2 = seed_database(self.session, base_time=self.test_clock)
        counts2 = {
            "localities": self.session.scalar(select(func.count(Locality.id))),
            "mandis": self.session.scalar(select(func.count(Mandi.id))),
            "wholesale": self.session.scalar(select(func.count(WholesalePriceObservation.id))),
            "transport": self.session.scalar(select(func.count(TransportConfiguration.id))),
            "customers": self.session.scalar(select(func.count(Customer.id))),
            "vendors": self.session.scalar(select(func.count(Vendor.id))),
            "community": self.session.scalar(select(func.count(CommunityPriceObservation.id))),
        }

        self.assertEqual(counts1, counts2)
        self.assertEqual(summary1["community_observations_count"], summary2["community_observations_count"])

    # -----------------------------------------------------------------------
    # Controllable clock & 2-day demo window
    # -----------------------------------------------------------------------
    def test_community_observations_controllable_clock_window(self):
        """Observations within the 48-hour demo window are captured dynamically relative to test_clock."""
        seed_database(self.session, base_time=self.test_clock)
        window_start = self.test_clock - timedelta(days=2)

        recent_obs = CommunityPriceRepository.list_recent(
            self.session,
            commodity_id="tomato",
            locality_id="loc_katpadi",
            since=window_start,
            exclude_duplicates=True,
        )

        # 3 distinct tomato observations seeded within the 48h window
        self.assertEqual(len(recent_obs), 3)
        prices = [o.price for o in recent_obs]
        self.assertIn(28.0, prices)
        self.assertIn(30.0, prices)
        self.assertIn(29.0, prices)

        # All observed_at timestamps must be within the 48h demo window
        for o in recent_obs:
            self.assertGreaterEqual(o.observed_at, window_start)
            self.assertLessEqual(o.observed_at, self.test_clock)

    def test_community_observations_duplicate_and_sparse_handling(self):
        """Verify that duplicate records are tagged and sparse commodities are handled properly."""
        seed_database(self.session, base_time=self.test_clock)

        # 1. Duplicate observation exists and is excluded when exclude_duplicates=True
        all_obs = CommunityPriceRepository.list_recent(
            self.session,
            commodity_id="tomato",
            locality_id="loc_katpadi",
            exclude_duplicates=False,
        )
        deduped_obs = CommunityPriceRepository.list_recent(
            self.session,
            commodity_id="tomato",
            locality_id="loc_katpadi",
            exclude_duplicates=True,
        )
        self.assertEqual(len(all_obs), len(deduped_obs) + 1)

        dup_record = next(o for o in all_obs if o.is_duplicate)
        self.assertEqual(dup_record.id, "obs_tomato_katpadi_dup")
        self.assertEqual(dup_record.duplicate_of_id, "obs_tomato_katpadi_01")

        # 2. Sparse / thin-sample commodity (dragonfruit has only 1 observation 12 days ago)
        window_start = self.test_clock - timedelta(days=2)
        recent_dragonfruit = CommunityPriceRepository.list_recent(
            self.session, commodity_id="dragonfruit", since=window_start
        )
        self.assertEqual(len(recent_dragonfruit), 0)  # Excluded from 2-day window

        all_dragonfruit = CommunityPriceRepository.list_recent(
            self.session, commodity_id="dragonfruit"
        )
        self.assertEqual(len(all_dragonfruit), 1)
        self.assertEqual(all_dragonfruit[0].price, 180.0)

    def test_community_price_metrics_calculation(self):
        """Verify aggregation metrics (count, average, min, max) across community observations."""
        seed_database(self.session, base_time=self.test_clock)

        metrics = CommunityPriceRepository.get_price_metrics(
            self.session,
            commodity_id="tomato",
            locality_id="loc_katpadi",
            exclude_duplicates=True,
        )
        self.assertEqual(metrics["sample_count"], 3)
        self.assertEqual(metrics["average_price"], 29.0)  # (28 + 30 + 29) / 3 = 29.0
        self.assertEqual(metrics["min_price"], 28.0)
        self.assertEqual(metrics["max_price"], 30.0)

    # -----------------------------------------------------------------------
    # Calculation Record (Phase 6 foundation)
    # -----------------------------------------------------------------------
    def test_calculation_record_persistence(self):
        """Verify storage of serialized calculation details and status."""
        calc = CalculationRepository.create(
            self.session,
            {
                "id": "calc_test_001",
                "commodity_id": "tomato",
                "locality_id": "loc_katpadi",
                "status": "COMPLETED",
                "algorithm_version": "v1.0-baseline",
                "serialized_details": '{"fair_min": 26.0, "fair_max": 29.0, "wholesale": 20.0}',
                "integrity_hash": None,
            }
        )
        self.assertIsNotNone(calc)

        retrieved = CalculationRepository.get_by_id(self.session, "calc_test_001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.status, "COMPLETED")
        self.assertIn('"fair_min": 26.0', retrieved.serialized_details)


if __name__ == "__main__":
    unittest.main()
