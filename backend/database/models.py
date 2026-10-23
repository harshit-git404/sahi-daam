from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Text,
    TypeDecorator,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .connection import Base


class UTCDateTime(TypeDecorator):
    """
    Ensures datetimes stored in SQLite are returned as timezone-aware UTC datetimes.
    SQLite stores datetimes without timezone info by default, causing comparisons
    with offset-aware datetimes to raise TypeError.
    """
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        return value


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Locality(Base):
    """Geographic locality and neighborhood definitions."""
    __tablename__ = "localities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    pincode: Mapped[Optional[str]] = mapped_column(String(16), index=True, nullable=True)
    district: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utc_now)

    # Relationships
    community_observations: Mapped[List["CommunityPriceObservation"]] = relationship(
        "CommunityPriceObservation", back_populates="locality"
    )
    customers: Mapped[List["Customer"]] = relationship("Customer", back_populates="locality")
    vendors: Mapped[List["Vendor"]] = relationship("Vendor", back_populates="locality")

    __table_args__ = (
        Index("ix_localities_name_district", "name", "district"),
    )


class Mandi(Base):
    """Agricultural mandi and wholesale market registry."""
    __tablename__ = "mandis"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    market_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    district: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(128), nullable=False)
    distance_km_reference: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    provenance_note: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utc_now)

    # Relationships
    wholesale_prices: Mapped[List["WholesalePriceObservation"]] = relationship(
        "WholesalePriceObservation", back_populates="mandi"
    )


class WholesalePriceObservation(Base):
    """Historical and snapshot wholesale mandi price observations."""
    __tablename__ = "wholesale_price_observations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    commodity_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    mandi_id: Mapped[str] = mapped_column(String(64), ForeignKey("mandis.id"), index=True, nullable=False)
    price_per_kg: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(16), default="kg", nullable=False)
    source: Mapped[str] = mapped_column(String(128), default="data.gov.in/agmarknet")
    source_type: Mapped[str] = mapped_column(String(64), default="mock_seed")
    availability_status: Mapped[str] = mapped_column(String(32), default="AVAILABLE")
    observed_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utc_now)

    # Relationships
    mandi: Mapped["Mandi"] = relationship("Mandi", back_populates="wholesale_prices")

    __table_args__ = (
        Index("ix_wholesale_commodity_mandi", "commodity_id", "mandi_id", "observed_at"),
    )


class TransportConfiguration(Base):
    """Vehicular and regional freight rate configurations."""
    __tablename__ = "transport_configurations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    vehicle_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    base_rate_per_km: Mapped[float] = mapped_column(Float, nullable=False)
    flat_fee: Mapped[float] = mapped_column(Float, default=0.0)
    fuel_consumption_km_per_l: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fuel_price_per_l: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    capacity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    effective_load_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    loading_unloading_fee: Mapped[float] = mapped_column(Float, default=0.0)
    driver_allowance: Mapped[float] = mapped_column(Float, default=0.0)
    trip_direction: Mapped[str] = mapped_column(String(64), default="mandi_to_retail")
    version: Mapped[str] = mapped_column(String(32), default="1.0")
    provenance: Mapped[str] = mapped_column(String(128), default="mock_seed_logistics")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utc_now)


class Customer(Base):
    """Customer entity kept strictly separate from vendors with minimal mock metadata."""
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    alias: Mapped[str] = mapped_column(String(128), nullable=False)
    locality_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("localities.id"), nullable=True)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utc_now)

    # Relationships
    locality: Mapped[Optional["Locality"]] = relationship("Locality", back_populates="customers")


class Vendor(Base):
    """Vendor entity kept strictly separate from customers with minimal mock metadata."""
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    vendor_type: Mapped[str] = mapped_column(String(64), default="street_vendor")  # street_vendor | market_stall
    locality_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("localities.id"), nullable=True)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utc_now)

    # Relationships
    locality: Mapped[Optional["Locality"]] = relationship("Locality", back_populates="vendors")


class CommunityPriceObservation(Base):
    """Community-sourced price reports with duplicate tracking and timestamps."""
    __tablename__ = "community_price_observations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    commodity_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(16), default="kg", nullable=False)
    locality_id: Mapped[str] = mapped_column(String(64), ForeignKey("localities.id"), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)  # customer | vendor
    contributor_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utc_now)
    provenance: Mapped[str] = mapped_column(String(128), default="mock_seed_survey")
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    duplicate_of_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Relationships
    locality: Mapped["Locality"] = relationship("Locality", back_populates="community_observations")

    __table_args__ = (
        Index("ix_community_obs_filter", "commodity_id", "locality_id", "observed_at", "is_duplicate"),
    )


class CalculationRecord(Base):
    """Persistent storage for calculation attempts in preparation for Phase 6 ledger."""
    __tablename__ = "calculation_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    commodity_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    locality_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="COMPLETED")  # COMPLETED | FAILED | FALLBACK
    algorithm_version: Mapped[str] = mapped_column(String(32), default="v1.0-baseline")
    serialized_details: Mapped[str] = mapped_column(Text, nullable=False)  # JSON payload of calculation
    integrity_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)  # Reserved for Phase 6 hash chain
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utc_now, index=True)
