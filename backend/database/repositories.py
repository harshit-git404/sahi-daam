from datetime import datetime
from typing import Optional, List, Dict, Any
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
        record = CalculationRecord(**data)
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
