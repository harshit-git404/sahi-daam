from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from .repositories import (
    LocalityRepository,
    MandiRepository,
    WholesalePriceRepository,
    TransportConfigRepository,
    CustomerRepository,
    VendorRepository,
    CommunityPriceRepository,
)


def seed_database(session: Session, base_time: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Seed predictable, idempotent mock reference data for local testing.

    Args:
        session: SQLAlchemy database session.
        base_time: Controllable clock reference (defaults to UTC now).
                   Community observations for the 2-day demo window are
                   calculated relative to this time so data is never stale.

    Returns:
        Summary dict containing counts of seeded entities.
    """
    ref_time = base_time or datetime.now(timezone.utc)

    # -----------------------------------------------------------------------
    # 1. Localities (Vellore regional reference)
    # Note: loc_bagayam and loc_thorapadi share pincode 632002 demonstrating
    # non-1:1 pincode-to-neighborhood mapping.
    # -----------------------------------------------------------------------
    localities_data = [
        {
            "id": "loc_katpadi",
            "name": "Katpadi",
            "pincode": "632014",
            "district": "Vellore",
            "state": "Tamil Nadu",
        },
        {
            "id": "loc_gandhi_nagar",
            "name": "Gandhi Nagar",
            "pincode": "632006",
            "district": "Vellore",
            "state": "Tamil Nadu",
        },
        {
            "id": "loc_sathuvachari",
            "name": "Sathuvachari",
            "pincode": "632009",
            "district": "Vellore",
            "state": "Tamil Nadu",
        },
        {
            "id": "loc_bagayam",
            "name": "Bagayam",
            "pincode": "632002",
            "district": "Vellore",
            "state": "Tamil Nadu",
        },
        {
            "id": "loc_thorapadi",
            "name": "Thorapadi",
            "pincode": "632002",
            "district": "Vellore",
            "state": "Tamil Nadu",
        },
    ]
    for item in localities_data:
        LocalityRepository.upsert(session, item)

    # -----------------------------------------------------------------------
    # 2. Mandis
    # -----------------------------------------------------------------------
    mandis_data = [
        {
            "id": "mandi_vellore",
            "market_name": "Vellore Mandi",
            "district": "Vellore",
            "state": "Tamil Nadu",
            "distance_km_reference": 5.5,
            "provenance_note": "Official Agmarknet wholesale reporting market",
            "is_mock": False,
        },
        {
            "id": "mandi_katpadi",
            "market_name": "Katpadi Uzhavar Sandhai",
            "district": "Vellore",
            "state": "Tamil Nadu",
            "distance_km_reference": 2.2,
            "provenance_note": "Direct farmer retail market",
            "is_mock": True,
        },
        {
            "id": "mandi_gudiyatham",
            "market_name": "Gudiyatham Wholesale Market",
            "district": "Vellore",
            "state": "Tamil Nadu",
            "distance_km_reference": 32.0,
            "provenance_note": "Sub-district wholesale transit hub",
            "is_mock": True,
        },
    ]
    for item in mandis_data:
        MandiRepository.upsert(session, item)

    # -----------------------------------------------------------------------
    # 3. Wholesale Price Observations
    # -----------------------------------------------------------------------
    wholesale_prices_data = [
        # Tomato wholesale history
        {
            "id": "ws_tomato_vellore_d0",
            "commodity_id": "tomato",
            "mandi_id": "mandi_vellore",
            "price_per_kg": 20.0,
            "unit": "kg",
            "source": "data.gov.in/agmarknet",
            "source_type": "mock_seed",
            "availability_status": "AVAILABLE",
            "observed_at": ref_time - timedelta(hours=4),
        },
        {
            "id": "ws_tomato_vellore_d1",
            "commodity_id": "tomato",
            "mandi_id": "mandi_vellore",
            "price_per_kg": 22.0,
            "unit": "kg",
            "source": "data.gov.in/agmarknet",
            "source_type": "mock_seed",
            "availability_status": "AVAILABLE",
            "observed_at": ref_time - timedelta(days=1),
        },
        {
            "id": "ws_tomato_katpadi_d0",
            "commodity_id": "tomato",
            "mandi_id": "mandi_katpadi",
            "price_per_kg": 21.5,
            "unit": "kg",
            "source": "mock_agmarknet_snapshot",
            "source_type": "mock_seed",
            "availability_status": "AVAILABLE",
            "observed_at": ref_time - timedelta(hours=6),
        },
        # Potato wholesale history
        {
            "id": "ws_potato_vellore_d0",
            "commodity_id": "potato",
            "mandi_id": "mandi_vellore",
            "price_per_kg": 22.0,
            "unit": "kg",
            "source": "data.gov.in/agmarknet",
            "source_type": "mock_seed",
            "availability_status": "AVAILABLE",
            "observed_at": ref_time - timedelta(hours=5),
        },
        # Onion wholesale history
        {
            "id": "ws_onion_vellore_d0",
            "commodity_id": "onion",
            "mandi_id": "mandi_vellore",
            "price_per_kg": 28.0,
            "unit": "kg",
            "source": "data.gov.in/agmarknet",
            "source_type": "mock_seed",
            "availability_status": "AVAILABLE",
            "observed_at": ref_time - timedelta(hours=5),
        },
    ]
    for item in wholesale_prices_data:
        WholesalePriceRepository.upsert(session, item)

    # -----------------------------------------------------------------------
    # 4. Transport Configurations
    # -----------------------------------------------------------------------
    transport_configs_data = [
        {
            "id": "trans_mini_truck_v1",
            "vehicle_type": "mini_truck",
            "base_rate_per_km": 14.0,
            "flat_fee": 150.0,
            "fuel_consumption_km_per_l": 14.0,
            "fuel_price_per_l": 102.5,
            "capacity_kg": 1000.0,
            "effective_load_kg": 750.0,
            "loading_unloading_fee": 80.0,
            "driver_allowance": 100.0,
            "trip_direction": "mandi_to_retail",
            "version": "1.0",
            "provenance": "regional_freight_guideline_2026",
            "is_active": True,
        },
        {
            "id": "trans_cargo_auto_v1",
            "vehicle_type": "cargo_auto",
            "base_rate_per_km": 10.0,
            "flat_fee": 80.0,
            "fuel_consumption_km_per_l": 22.0,
            "fuel_price_per_l": 102.5,
            "capacity_kg": 450.0,
            "effective_load_kg": 350.0,
            "loading_unloading_fee": 40.0,
            "driver_allowance": 50.0,
            "trip_direction": "mandi_to_retail",
            "version": "1.0",
            "provenance": "regional_freight_guideline_2026",
            "is_active": True,
        },
        {
            "id": "trans_tempo_v1",
            "vehicle_type": "tempo",
            "base_rate_per_km": 18.0,
            "flat_fee": 250.0,
            "fuel_consumption_km_per_l": 9.0,
            "fuel_price_per_l": 92.5,
            "capacity_kg": 2500.0,
            "effective_load_kg": 1800.0,
            "loading_unloading_fee": 150.0,
            "driver_allowance": 150.0,
            "trip_direction": "mandi_to_retail",
            "version": "1.0",
            "provenance": "regional_freight_guideline_2026",
            "is_active": True,
        },
    ]
    for item in transport_configs_data:
        TransportConfigRepository.upsert(session, item)

    # -----------------------------------------------------------------------
    # 5. Customer dataset (Separated from vendors, minimal mock metadata)
    # -----------------------------------------------------------------------
    customers_data = [
        {"id": "cust_mock_001", "alias": "Mock Buyer Priya", "locality_id": "loc_katpadi", "is_mock": True},
        {"id": "cust_mock_002", "alias": "Mock Buyer Karthik", "locality_id": "loc_gandhi_nagar", "is_mock": True},
        {"id": "cust_mock_003", "alias": "Mock Buyer Ananya", "locality_id": "loc_sathuvachari", "is_mock": True},
    ]
    for item in customers_data:
        CustomerRepository.upsert(session, item)

    # -----------------------------------------------------------------------
    # 6. Vendor dataset (Separated from customers, marked as mock)
    # -----------------------------------------------------------------------
    vendors_data = [
        {
            "id": "vend_mock_001",
            "display_name": "Mock Cart Vendor Murugan",
            "vendor_type": "street_vendor",
            "locality_id": "loc_katpadi",
            "is_mock": True,
        },
        {
            "id": "vend_mock_002",
            "display_name": "Mock Stall Selvam",
            "vendor_type": "market_stall",
            "locality_id": "loc_gandhi_nagar",
            "is_mock": True,
        },
        {
            "id": "vend_mock_003",
            "display_name": "Mock Cart Vendor Ravi",
            "vendor_type": "street_vendor",
            "locality_id": "loc_sathuvachari",
            "is_mock": True,
        },
    ]
    for item in vendors_data:
        VendorRepository.upsert(session, item)

    # -----------------------------------------------------------------------
    # 7. Community Price Observations
    # Includes:
    # - Dynamic 2-day demo window observations
    # - Different timestamps
    # - Explicit duplicate record
    # - Sparse / thin-sample example (dragonfruit with 1 old observation)
    # -----------------------------------------------------------------------
    community_obs_data = [
        # Recent observations within 48h demo window for Tomato in Katpadi
        {
            "id": "obs_tomato_katpadi_01",
            "commodity_id": "tomato",
            "price": 28.0,
            "unit": "kg",
            "locality_id": "loc_katpadi",
            "source_type": "customer",
            "contributor_id": "cust_mock_001",
            "observed_at": ref_time - timedelta(hours=3),
            "provenance": "mock_seed_survey",
            "is_duplicate": False,
            "duplicate_of_id": None,
        },
        {
            "id": "obs_tomato_katpadi_02",
            "commodity_id": "tomato",
            "price": 30.0,
            "unit": "kg",
            "locality_id": "loc_katpadi",
            "source_type": "vendor",
            "contributor_id": "vend_mock_001",
            "observed_at": ref_time - timedelta(hours=14),
            "provenance": "mock_seed_survey",
            "is_duplicate": False,
            "duplicate_of_id": None,
        },
        {
            "id": "obs_tomato_katpadi_03",
            "commodity_id": "tomato",
            "price": 29.0,
            "unit": "kg",
            "locality_id": "loc_katpadi",
            "source_type": "customer",
            "contributor_id": "cust_mock_001",
            "observed_at": ref_time - timedelta(hours=28),
            "provenance": "mock_seed_survey",
            "is_duplicate": False,
            "duplicate_of_id": None,
        },
        # Explicit Duplicate Record (same price and timestamp as 01)
        {
            "id": "obs_tomato_katpadi_dup",
            "commodity_id": "tomato",
            "price": 28.0,
            "unit": "kg",
            "locality_id": "loc_katpadi",
            "source_type": "customer",
            "contributor_id": "cust_mock_001",
            "observed_at": ref_time - timedelta(hours=3),
            "provenance": "mock_seed_survey",
            "is_duplicate": True,
            "duplicate_of_id": "obs_tomato_katpadi_01",
        },
        # Observations for Onion in Gandhi Nagar
        {
            "id": "obs_onion_gandhi_01",
            "commodity_id": "onion",
            "price": 36.0,
            "unit": "kg",
            "locality_id": "loc_gandhi_nagar",
            "source_type": "vendor",
            "contributor_id": "vend_mock_002",
            "observed_at": ref_time - timedelta(hours=8),
            "provenance": "mock_seed_survey",
            "is_duplicate": False,
            "duplicate_of_id": None,
        },
        {
            "id": "obs_onion_gandhi_02",
            "commodity_id": "onion",
            "price": 38.0,
            "unit": "kg",
            "locality_id": "loc_gandhi_nagar",
            "source_type": "customer",
            "contributor_id": "cust_mock_002",
            "observed_at": ref_time - timedelta(hours=34),
            "provenance": "mock_seed_survey",
            "is_duplicate": False,
            "duplicate_of_id": None,
        },
        # Observations for Potato in Sathuvachari
        {
            "id": "obs_potato_sathu_01",
            "commodity_id": "potato",
            "price": 28.0,
            "unit": "kg",
            "locality_id": "loc_sathuvachari",
            "source_type": "vendor",
            "contributor_id": "vend_mock_003",
            "observed_at": ref_time - timedelta(hours=6),
            "provenance": "mock_seed_survey",
            "is_duplicate": False,
            "duplicate_of_id": None,
        },
        # Thin-sample example: Dragonfruit (only 1 observation, 12 days old, outside 2-day window)
        {
            "id": "obs_dragonfruit_sparse",
            "commodity_id": "dragonfruit",
            "price": 180.0,
            "unit": "kg",
            "locality_id": "loc_katpadi",
            "source_type": "customer",
            "contributor_id": "cust_mock_001",
            "observed_at": ref_time - timedelta(days=12),
            "provenance": "mock_seed_survey",
            "is_duplicate": False,
            "duplicate_of_id": None,
        },
    ]
    for item in community_obs_data:
        if "normalized_price_per_kg" not in item and item.get("unit") == "kg":
            item["normalized_price_per_kg"] = item["price"]
        CommunityPriceRepository.upsert(session, item)

    session.commit()

    return {
        "localities_count": len(localities_data),
        "mandis_count": len(mandis_data),
        "wholesale_prices_count": len(wholesale_prices_data),
        "transport_configs_count": len(transport_configs_data),
        "customers_count": len(customers_data),
        "vendors_count": len(vendors_data),
        "community_observations_count": len(community_obs_data),
        "seeded_at": ref_time,
    }
