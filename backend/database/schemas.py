from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Locality
# ---------------------------------------------------------------------------
class LocalityBase(BaseModel):
    id: str
    name: str
    pincode: Optional[str] = None
    district: str
    state: str


class LocalityRead(LocalityBase):
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Mandi
# ---------------------------------------------------------------------------
class MandiBase(BaseModel):
    id: str
    market_name: str
    district: str
    state: str
    distance_km_reference: Optional[float] = None
    provenance_note: Optional[str] = None
    is_mock: bool = False


class MandiRead(MandiBase):
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Wholesale Price Observation
# ---------------------------------------------------------------------------
class WholesalePriceObservationBase(BaseModel):
    id: str
    commodity_id: str
    mandi_id: str
    price_per_kg: float
    unit: str = "kg"
    source: str = "data.gov.in/agmarknet"
    source_type: str = "mock_seed"
    availability_status: str = "AVAILABLE"
    observed_at: datetime


class WholesalePriceObservationRead(WholesalePriceObservationBase):
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Transport Configuration
# ---------------------------------------------------------------------------
class TransportConfigurationBase(BaseModel):
    id: str
    vehicle_type: str
    base_rate_per_km: float
    flat_fee: float = 0.0
    fuel_consumption_km_per_l: Optional[float] = None
    fuel_price_per_l: Optional[float] = None
    capacity_kg: float
    effective_load_kg: Optional[float] = None
    loading_unloading_fee: float = 0.0
    driver_allowance: float = 0.0
    trip_direction: str = "mandi_to_retail"
    version: str = "1.0"
    provenance: str = "mock_seed_logistics"
    is_active: bool = True


class TransportConfigurationRead(TransportConfigurationBase):
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------
class CustomerBase(BaseModel):
    id: str
    alias: str
    locality_id: Optional[str] = None
    is_mock: bool = True


class CustomerRead(CustomerBase):
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Vendor
# ---------------------------------------------------------------------------
class VendorBase(BaseModel):
    id: str
    display_name: str
    vendor_type: str = "street_vendor"
    locality_id: Optional[str] = None
    is_mock: bool = True


class VendorRead(VendorBase):
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Community Price Observation
# ---------------------------------------------------------------------------
class CommunityPriceObservationBase(BaseModel):
    id: str
    commodity_id: str
    price: float
    unit: str = "kg"
    locality_id: str
    source_type: str  # customer | vendor
    contributor_id: Optional[str] = None
    observed_at: datetime
    provenance: str = "mock_seed_survey"
    is_duplicate: bool = False
    duplicate_of_id: Optional[str] = None
    duplicate_reason: Optional[str] = None
    normalized_price_per_kg: Optional[float] = None


class CommunityPriceObservationRead(CommunityPriceObservationBase):
    created_at: datetime
    is_outlier: Optional[bool] = False
    model_config = ConfigDict(from_attributes=True)


class CommunityPriceSubmission(BaseModel):
    """Payload submitted by user or vendor."""
    commodity_id: str
    locality_id: Optional[str] = None
    locality_name: Optional[str] = None
    district: Optional[str] = "Vellore"
    state: Optional[str] = "Tamil Nadu"
    pincode: Optional[str] = None
    price: float
    unit: str = "kg"
    source_type: str = "customer"  # customer | vendor
    contributor_id: Optional[str] = None
    observed_at: Optional[datetime] = None
    provenance: Optional[str] = None


class CommunityPriceSubmissionResponse(BaseModel):
    status: str = "recorded"
    observation: CommunityPriceObservationRead
    is_duplicate: bool = False
    duplicate_of_id: Optional[str] = None
    duplicate_reason: Optional[str] = None
    normalized_price_per_kg: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)


class CommunityPriceListResponse(BaseModel):
    total_count: int
    window_days: Optional[int] = None
    items: List[CommunityPriceObservationRead]
    summary: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Calculation Record
# ---------------------------------------------------------------------------
class CalculationRecordBase(BaseModel):
    id: str
    sequence_number: int
    commodity_id: str
    locality_id: Optional[str] = None
    status: str = "COMPLETED"
    algorithm_version: str = "v2.0-locality-reconciled"
    schema_version: str = "1.0.0"
    serialized_details: str
    previous_record_hash: str
    current_record_hash: str
    is_mock: bool = True


class CalculationRecordRead(CalculationRecordBase):
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Seed Summary
# ---------------------------------------------------------------------------
class SeedSummary(BaseModel):
    localities_count: int
    mandis_count: int
    wholesale_prices_count: int
    transport_configs_count: int
    customers_count: int
    vendors_count: int
    community_observations_count: int
    seeded_at: datetime
