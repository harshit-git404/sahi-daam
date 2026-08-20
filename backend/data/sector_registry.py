import os
from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import UUID
from typing import Any, Literal

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv(Path(__file__).resolve().parents[3] / ".env")


APIStatus = Literal["API_AVAILABLE", "API_UNAVAILABLE", "NO_SUITABLE_DATA_SOURCE"]


@dataclass(frozen=True)
class SectorDataConfig:
    sector_id: str
    sector: str
    component: str
    resource_env_var: str
    status: APIStatus
    dataset_found: bool | None
    resource_id: str | None
    endpoint: str | None
    api_available: bool
    fields: tuple[str, ...]
    filters: dict[str, str]
    verification_note: str

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["fields"] = list(self.fields)
        return value


AGMARKNET_RESOURCE_ID = os.getenv(
    "AGMARKNET_RESOURCE_ID",
    "35985678-0d79-46b4-9ed6-6f13308a1d24",
).strip()
_AGMARKNET_FIELDS = (
    "Commodity", "State", "District", "Market", "Arrival_Date",
    "Min_Price", "Max_Price", "Modal_Price",
)
_AGMARKNET_FILTERS = {
    "filters[Commodity]": "commodity",
    "filters[State]": "state",
    "filters[District]": "district",
    "filters[Market]": "market",
    "filters[Arrival_Date]": "arrival_date",
}


def _configured_pending(sector_id: str, sector: str, component: str, resource_env_var: str) -> SectorDataConfig:
    resource_id = os.getenv(resource_env_var, "").strip() or None
    if resource_id is None:
        status: APIStatus = "NO_SUITABLE_DATA_SOURCE"
        verification_note = "No data.gov.in Resource ID is configured for this component."
    else:
        try:
            UUID(resource_id)
        except ValueError:
            status = "API_UNAVAILABLE"
            verification_note = "The configured value is not a valid UUID-style data.gov.in Resource ID."
        else:
            status = "API_UNAVAILABLE"
            verification_note = "A Resource ID is configured, but its Resource API schema and filters have not been verified yet."

    return SectorDataConfig(
        sector_id=sector_id,
        sector=sector,
        component=component,
        resource_env_var=resource_env_var,
        status=status,
        dataset_found=None,
        resource_id=resource_id,
        endpoint=None,
        api_available=False,
        fields=(),
        filters={},
        verification_note=verification_note,
    )


SECTOR_DATA_CONFIGS: tuple[SectorDataConfig, ...] = (
    SectorDataConfig(
        sector_id="food-agriculture",
        sector="Food & Agriculture",
        component="Fresh fruits & vegetables",
        resource_env_var="AGMARKNET_RESOURCE_ID",
        status="API_AVAILABLE",
        dataset_found=True,
        resource_id=AGMARKNET_RESOURCE_ID,
        endpoint="https://api.data.gov.in/resource/{resource_id}",
        api_available=True,
        fields=_AGMARKNET_FIELDS,
        filters=_AGMARKNET_FILTERS,
        verification_note="Verified existing Agmarknet Resource API. The photo/classifier/freshness workflow remains on /scan-produce.",
    ),
    _configured_pending("food-agriculture", "Food & Agriculture", "Agricultural fertilizers and pesticides", "FERTILIZER_RESOURCE_ID"),
    _configured_pending("energy-fuels", "Energy & Fuels", "Fossil fuels like petrol, diesel, and coal", "FOSSIL_FUELS_RESOURCE_ID"),
    _configured_pending("energy-fuels", "Energy & Fuels", "Renewable energy systems like solar and wind", "RENEWABLE_ENERGY_RESOURCE_ID"),
    _configured_pending("water-resources", "Water Resources", "Agricultural irrigation water", "AGRICULTURAL_IRRIGATION_RESOURCE_ID"),
    _configured_pending("water-resources", "Water Resources", "Municipal and domestic drinking water supply", "MUNICIPAL_DRINKING_WATER_RESOURCE_ID"),
    _configured_pending("raw-materials-infrastructure", "Raw Materials & Infrastructure", "Mined tech minerals like lithium, cobalt, and copper", "MINED_TECH_MINERALS_RESOURCE_ID"),
    _configured_pending("services-corporate-operations", "Services & Corporate Operations", "Tourism services, hospitality waste, and eco-travel footprints", "TOURISM_RESOURCE_ID"),
)


_CONFIG_BY_KEY = {
    (config.sector.lower(), config.component.lower()): config
    for config in SECTOR_DATA_CONFIGS
}


def get_sector_config(sector: str, component: str) -> SectorDataConfig | None:
    return _CONFIG_BY_KEY.get((sector.strip().lower(), component.strip().lower()))


def get_all_sector_configs() -> list[dict[str, Any]]:
    return [config.as_dict() for config in SECTOR_DATA_CONFIGS]
