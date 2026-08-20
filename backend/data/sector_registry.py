import os
from dataclasses import asdict, dataclass
from pathlib import Path
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


def _unverified(sector_id: str, sector: str, component: str, resource_env_var: str) -> SectorDataConfig:
    return SectorDataConfig(
        sector_id=sector_id,
        sector=sector,
        component=component,
        resource_env_var=resource_env_var,
        status="NO_SUITABLE_DATA_SOURCE",
        dataset_found=None,
        resource_id=None,
        endpoint=None,
        api_available=False,
        fields=(),
        filters={},
        verification_note=(
            "No matching official data.gov.in resource and Resource API have been verified for this component. "
            "Leave the resource variable empty until the resource page, schema, and API are confirmed."
        ),
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
    *(_unverified("food-agriculture", "Food & Agriculture", component, variable) for component, variable in (
        ("Consumer food waste", "FOOD_WASTE_RESOURCE_ID"),
        ("Post-harvest supply chain losses", "POST_HARVEST_LOSS_RESOURCE_ID"),
        ("Agricultural fertilizers and pesticides", "FERTILIZER_RESOURCE_ID"),
        ("Food packaging and single-use containers", "FOOD_PACKAGING_WASTE_RESOURCE_ID"),
    )),
    *(_unverified("energy-fuels", "Energy & Fuels", component, variable) for component, variable in (
        ("Fossil fuels like petrol, diesel, and coal", "FOSSIL_FUELS_RESOURCE_ID"),
        ("Inefficient fossil fuel subsidies", "FOSSIL_FUEL_SUBSIDIES_RESOURCE_ID"),
        ("Renewable energy systems like solar and wind", "RENEWABLE_ENERGY_RESOURCE_ID"),
        ("Industrial and residential electricity grid use", "ELECTRICITY_GRID_RESOURCE_ID"),
    )),
    *(_unverified("water-resources", "Water Resources", component, variable) for component, variable in (
        ("Industrial wastewater and factory effluents", "INDUSTRIAL_WASTEWATER_RESOURCE_ID"),
        ("Agricultural irrigation water", "AGRICULTURAL_IRRIGATION_RESOURCE_ID"),
        ("Municipal and domestic drinking water supply", "MUNICIPAL_DRINKING_WATER_RESOURCE_ID"),
    )),
    *(_unverified("consumer-goods-electronics", "Consumer Goods & Electronics", component, variable) for component, variable in (
        ("E-waste like smartphones, laptops, and batteries", "E_WASTE_RESOURCE_ID"),
        ("Fast fashion textiles and chemical clothing dyes", "FAST_FASHION_TEXTILES_RESOURCE_ID"),
        ("Single-use plastics like grocery bags and straws", "SINGLE_USE_PLASTIC_RESOURCE_ID"),
        ("Durable goods like appliances and furniture", "DURABLE_GOODS_RESOURCE_ID"),
    )),
    *(_unverified("chemicals-hazardous-materials", "Chemicals & Hazardous Materials", component, variable) for component, variable in (
        ("Industrial solvents, paints, and manufacturing toxins", "INDUSTRIAL_CHEMICALS_RESOURCE_ID"),
        ("Household chemical cleaners and non-biodegradable detergents", "HOUSEHOLD_CHEMICALS_RESOURCE_ID"),
        ("Heavy metals like mercury, lead, and cadmium", "HEAVY_METALS_RESOURCE_ID"),
    )),
    *(_unverified("raw-materials-infrastructure", "Raw Materials & Infrastructure", component, variable) for component, variable in (
        ("Construction materials like concrete, cement, and steel", "CONSTRUCTION_MATERIALS_RESOURCE_ID"),
        ("Mined tech minerals like lithium, cobalt, and copper", "MINED_TECH_MINERALS_RESOURCE_ID"),
        ("Aggregates like sand, gravel, and crushed stone", "AGGREGATES_RESOURCE_ID"),
    )),
    *(_unverified("services-corporate-operations", "Services & Corporate Operations", component, variable) for component, variable in (
        ("Public procurement items and green government contracts", "PUBLIC_PROCUREMENT_RESOURCE_ID"),
        ("Corporate sustainability and ESG reporting data", "ESG_REPORTING_RESOURCE_ID"),
        ("Tourism services, hospitality waste, and eco-travel footprints", "TOURISM_RESOURCE_ID"),
    )),
)


_CONFIG_BY_KEY = {
    (config.sector.lower(), config.component.lower()): config
    for config in SECTOR_DATA_CONFIGS
}


def get_sector_config(sector: str, component: str) -> SectorDataConfig | None:
    return _CONFIG_BY_KEY.get((sector.strip().lower(), component.strip().lower()))


def get_all_sector_configs() -> list[dict[str, Any]]:
    return [config.as_dict() for config in SECTOR_DATA_CONFIGS]
