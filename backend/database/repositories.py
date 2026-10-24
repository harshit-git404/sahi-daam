from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from .models import (
    Locality,
    Mandi,
    WholesalePriceObservation,
    TransportConfiguration,
    Customer,
    Vendor,
    CommunityPriceObservation,
    CalculationRecord,
)


class LocalityRepository:
    @staticmethod
    def get_by_id(session: Session, locality_id: str) -> Optional[Locality]:
        return session.get(Locality, locality_id)

    @staticmethod
    def list_all(session: Session) -> List[Locality]:
        stmt = select(Locality).order_by(Locality.name)
        return list(session.scalars(stmt).all())

    @staticmethod
    def list_by_pincode(session: Session, pincode: str) -> List[Locality]:
        stmt = select(Locality).where(Locality.pincode == pincode).order_by(Locality.name)
        return list(session.scalars(stmt).all())

    @staticmethod
    def upsert(session: Session, data: Dict[str, Any]) -> Locality:
        item = session.get(Locality, data["id"])
        if item:
            for key, val in data.items():
                setattr(item, key, val)
        else:
            item = Locality(**data)
            session.add(item)
        return item


class MandiRepository:
    @staticmethod
    def get_by_id(session: Session, mandi_id: str) -> Optional[Mandi]:
        return session.get(Mandi, mandi_id)

    @staticmethod
    def list_all(session: Session) -> List[Mandi]:
        stmt = select(Mandi).order_by(Mandi.market_name)
        return list(session.scalars(stmt).all())

    @staticmethod
    def list_by_district(session: Session, district: str) -> List[Mandi]:
        stmt = select(Mandi).where(Mandi.district == district).order_by(Mandi.market_name)
        return list(session.scalars(stmt).all())

    @staticmethod
    def upsert(session: Session, data: Dict[str, Any]) -> Mandi:
        item = session.get(Mandi, data["id"])
        if item:
            for key, val in data.items():
                setattr(item, key, val)
        else:
            item = Mandi(**data)
            session.add(item)
        return item


class WholesalePriceRepository:
    @staticmethod
    def get_latest(
        session: Session, commodity_id: str, mandi_id: Optional[str] = None
    ) -> Optional[WholesalePriceObservation]:
        conditions = [WholesalePriceObservation.commodity_id == commodity_id]
        if mandi_id:
            conditions.append(WholesalePriceObservation.mandi_id == mandi_id)
        stmt = (
            select(WholesalePriceObservation)
            .where(and_(*conditions))
            .order_by(WholesalePriceObservation.observed_at.desc())
            .limit(1)
        )
        return session.scalars(stmt).first()

    @staticmethod
    def list_history(
        session: Session, commodity_id: str, mandi_id: Optional[str] = None, limit: int = 10
    ) -> List[WholesalePriceObservation]:
        conditions = [WholesalePriceObservation.commodity_id == commodity_id]
        if mandi_id:
            conditions.append(WholesalePriceObservation.mandi_id == mandi_id)
        stmt = (
            select(WholesalePriceObservation)
            .where(and_(*conditions))
            .order_by(WholesalePriceObservation.observed_at.desc())
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    @staticmethod
    def upsert(session: Session, data: Dict[str, Any]) -> WholesalePriceObservation:
        item = session.get(WholesalePriceObservation, data["id"])
        if item:
            for key, val in data.items():
                setattr(item, key, val)
        else:
            item = WholesalePriceObservation(**data)
            session.add(item)
        return item


class TransportConfigRepository:
    @staticmethod
    def get_by_vehicle_type(session: Session, vehicle_type: str) -> Optional[TransportConfiguration]:
        stmt = (
            select(TransportConfiguration)
            .where(and_(
                TransportConfiguration.vehicle_type == vehicle_type,
                TransportConfiguration.is_active.is_(True)
            ))
            .order_by(TransportConfiguration.created_at.desc())
            .limit(1)
        )
        return session.scalars(stmt).first()

    @staticmethod
    def list_active(session: Session) -> List[TransportConfiguration]:
        stmt = (
            select(TransportConfiguration)
            .where(TransportConfiguration.is_active.is_(True))
            .order_by(TransportConfiguration.vehicle_type)
        )
        return list(session.scalars(stmt).all())

    @staticmethod
    def upsert(session: Session, data: Dict[str, Any]) -> TransportConfiguration:
        item = session.get(TransportConfiguration, data["id"])
        if item:
            for key, val in data.items():
                setattr(item, key, val)
        else:
            item = TransportConfiguration(**data)
            session.add(item)
        return item


class CustomerRepository:
    @staticmethod
    def get_by_id(session: Session, customer_id: str) -> Optional[Customer]:
        return session.get(Customer, customer_id)

    @staticmethod
    def list_all(session: Session) -> List[Customer]:
        stmt = select(Customer).order_by(Customer.alias)
        return list(session.scalars(stmt).all())

    @staticmethod
    def upsert(session: Session, data: Dict[str, Any]) -> Customer:
        item = session.get(Customer, data["id"])
        if item:
            for key, val in data.items():
                setattr(item, key, val)
        else:
            item = Customer(**data)
            session.add(item)
        return item


class VendorRepository:
    @staticmethod
    def get_by_id(session: Session, vendor_id: str) -> Optional[Vendor]:
        return session.get(Vendor, vendor_id)

    @staticmethod
    def list_by_locality(session: Session, locality_id: str) -> List[Vendor]:
        stmt = select(Vendor).where(Vendor.locality_id == locality_id).order_by(Vendor.display_name)
        return list(session.scalars(stmt).all())

    @staticmethod
    def upsert(session: Session, data: Dict[str, Any]) -> Vendor:
        item = session.get(Vendor, data["id"])
        if item:
            for key, val in data.items():
                setattr(item, key, val)
        else:
            item = Vendor(**data)
            session.add(item)
        return item


class CommunityPriceRepository:
    @staticmethod
    def get_by_id(session: Session, observation_id: str) -> Optional[CommunityPriceObservation]:
        return session.get(CommunityPriceObservation, observation_id)

    @staticmethod
    def create(session: Session, data: Dict[str, Any]) -> CommunityPriceObservation:
        item = CommunityPriceObservation(**data)
        session.add(item)
        session.commit()
        session.refresh(item)
        return item

    @staticmethod
    def find_potential_duplicate(
        session: Session,
        commodity_id: str,
        locality_id: str,
        price: float,
        unit: str,
        observed_at: datetime,
        contributor_id: Optional[str] = None,
        source_type: Optional[str] = None,
        time_window_hours: int = 12,
    ) -> Optional[CommunityPriceObservation]:
        """
        Conservative duplicate check: looks for reports with the same commodity,
        locality, price, unit, and contributor (or source type) within a time window.
        """
        from datetime import timedelta
        window_start = observed_at - timedelta(hours=time_window_hours)
        window_end = observed_at + timedelta(hours=time_window_hours)

        conditions = [
            CommunityPriceObservation.commodity_id == commodity_id,
            CommunityPriceObservation.locality_id == locality_id,
            CommunityPriceObservation.price == price,
            CommunityPriceObservation.unit == unit,
            CommunityPriceObservation.observed_at >= window_start,
            CommunityPriceObservation.observed_at <= window_end,
        ]

        if contributor_id:
            conditions.append(CommunityPriceObservation.contributor_id == contributor_id)
        elif source_type:
            conditions.append(CommunityPriceObservation.source_type == source_type)

        stmt = select(CommunityPriceObservation).where(and_(*conditions)).order_by(CommunityPriceObservation.observed_at.desc()).limit(1)
        return session.scalars(stmt).first()

    @staticmethod
    def query_observations(
        session: Session,
        commodity_id: Optional[str] = None,
        locality_id: Optional[str] = None,
        source_type: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        exclude_duplicates: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[CommunityPriceObservation], int]:
        conditions = []
        if commodity_id:
            conditions.append(CommunityPriceObservation.commodity_id == commodity_id)
        if locality_id:
            conditions.append(CommunityPriceObservation.locality_id == locality_id)
        if source_type:
            conditions.append(CommunityPriceObservation.source_type == source_type)
        if since:
            conditions.append(CommunityPriceObservation.observed_at >= since)
        if until:
            conditions.append(CommunityPriceObservation.observed_at <= until)
        if exclude_duplicates:
            conditions.append(CommunityPriceObservation.is_duplicate.is_(False))

        where_clause = and_(*conditions) if conditions else True

        # Total count query
        count_stmt = select(func.count(CommunityPriceObservation.id)).where(where_clause)
        total_count = session.scalar(count_stmt) or 0

        # Items query
        stmt = (
            select(CommunityPriceObservation)
            .where(where_clause)
            .order_by(CommunityPriceObservation.observed_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list(session.scalars(stmt).all())
        return items, total_count

    @staticmethod
    def list_recent(
        session: Session,
        commodity_id: str,
        locality_id: Optional[str] = None,
        since: Optional[datetime] = None,
        exclude_duplicates: bool = True,
        limit: int = 50,
    ) -> List[CommunityPriceObservation]:
        conditions = [CommunityPriceObservation.commodity_id == commodity_id]
        if locality_id:
            conditions.append(CommunityPriceObservation.locality_id == locality_id)
        if since:
            conditions.append(CommunityPriceObservation.observed_at >= since)
        if exclude_duplicates:
            conditions.append(CommunityPriceObservation.is_duplicate.is_(False))

        stmt = (
            select(CommunityPriceObservation)
            .where(and_(*conditions))
            .order_by(CommunityPriceObservation.observed_at.desc())
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    @staticmethod
    def get_price_metrics(
        session: Session,
        commodity_id: str,
        locality_id: Optional[str] = None,
        since: Optional[datetime] = None,
        exclude_duplicates: bool = True,
    ) -> Dict[str, Any]:
        conditions = [CommunityPriceObservation.commodity_id == commodity_id]
        if locality_id:
            conditions.append(CommunityPriceObservation.locality_id == locality_id)
        if since:
            conditions.append(CommunityPriceObservation.observed_at >= since)
        if exclude_duplicates:
            conditions.append(CommunityPriceObservation.is_duplicate.is_(False))

        stmt = select(
            func.count(CommunityPriceObservation.id).label("count"),
            func.avg(CommunityPriceObservation.price).label("avg"),
            func.min(CommunityPriceObservation.price).label("min"),
            func.max(CommunityPriceObservation.price).label("max"),
        ).where(and_(*conditions))

        row = session.execute(stmt).one()
        return {
            "sample_count": row.count or 0,
            "average_price": round(float(row.avg), 2) if row.avg is not None else None,
            "min_price": round(float(row.min), 2) if row.min is not None else None,
            "max_price": round(float(row.max), 2) if row.max is not None else None,
        }

    @staticmethod
    def upsert(session: Session, data: Dict[str, Any]) -> CommunityPriceObservation:
        item = session.get(CommunityPriceObservation, data["id"])
        if item:
            for key, val in data.items():
                setattr(item, key, val)
        else:
            item = CommunityPriceObservation(**data)
            session.add(item)
        return item


class CalculationRepository:
    @staticmethod
    def create(session: Session, data: Dict[str, Any]) -> CalculationRecord:
        record_data = dict(data)
        if "integrity_hash" in record_data:
            legacy_hash = record_data.pop("integrity_hash")
            if "current_record_hash" not in record_data:
                record_data["current_record_hash"] = legacy_hash or ("0" * 64)
        if "sequence_number" not in record_data:
            max_seq = session.query(func.max(CalculationRecord.sequence_number)).scalar() or 0
            record_data["sequence_number"] = max_seq + 1
        if "previous_record_hash" not in record_data:
            record_data["previous_record_hash"] = "0" * 64
        if "current_record_hash" not in record_data:
            record_data["current_record_hash"] = "0" * 64
        record = CalculationRecord(**record_data)
        session.add(record)
        session.commit()
        session.refresh(record)
        return record

    @staticmethod
    def get_by_id(session: Session, calculation_id: str) -> Optional[CalculationRecord]:
        return session.get(CalculationRecord, calculation_id)

    @staticmethod
    def list_by_commodity(
        session: Session, commodity_id: str, limit: int = 20
    ) -> List[CalculationRecord]:
        stmt = (
            select(CalculationRecord)
            .where(CalculationRecord.commodity_id == commodity_id)
            .order_by(CalculationRecord.created_at.desc())
            .limit(limit)
        )
        return list(session.scalars(stmt).all())
