import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Literal

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
    metric_name: str
    unit: str
    date_field: str
    value_field: str
    aggregation: Any
    verification_note: str

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["fields"] = list(self.fields)
        return value


# ---------------------------------------------------------------------------
# Agmarknet (Food & Agriculture → Fresh fruits & vegetables)
# Verified: data.gov.in resource 35985678-0d79-46b4-9ed6-6f13308a1d24
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Helper: create a stub entry for components without verified Resource APIs
# ---------------------------------------------------------------------------
def _stub(
    sector_id: str,
    sector: str,
    component: str,
    resource_env_var: str,
    *,
    dataset_found: bool | None = None,
    verification_note: str = "",
    status: APIStatus = "NO_SUITABLE_DATA_SOURCE",
) -> "SectorDataConfig":
    resource_id = os.getenv(resource_env_var, "").strip() or None
    actual_status: APIStatus = status
    actual_note = verification_note

    if resource_id and not actual_note:
        actual_status = "API_UNAVAILABLE"
        actual_note = (
            "A Resource ID is configured but the Resource API schema and "
            "filters have not been verified for this component."
        )
    elif not resource_id and not actual_note:
        actual_note = (
            "No data.gov.in Resource ID is configured for this component. "
            "Verified data will be added when an official API is confirmed."
        )

    return SectorDataConfig(
        sector_id=sector_id,
        sector=sector,
        component=component,
        resource_env_var=resource_env_var,
        status=actual_status,
        dataset_found=dataset_found,
        resource_id=resource_id,
        endpoint=None,
        api_available=False,
        fields=(),
        filters={},
        metric_name="",
        unit="",
        date_field="",
        value_field="",
        aggregation=lambda values: sum(values) / len(values),
        verification_note=actual_note,
    )


# ---------------------------------------------------------------------------
# Complete sector/component registry — must mirror frontend sectorData.ts
# ---------------------------------------------------------------------------
SECTOR_DATA_CONFIGS: tuple[SectorDataConfig, ...] = (

    # ── Food & Agriculture ────────────────────────────────────────────────
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
        metric_name="Price",
        unit="₹/kg",
        date_field="arrival_date",
        value_field="modal_price_per_kg",
        aggregation=lambda values: sum(values) / len(values),
        verification_note=(
            "Verified Agmarknet Resource API. "
            "Photo/classifier/freshness workflow uses /scan-produce."
        ),
    ),
    _stub(
        "food-agriculture", "Food & Agriculture",
        "Consumer food waste",
        "FOOD_WASTE_RESOURCE_ID",
        verification_note=(
            "No suitable open Resource API found on data.gov.in for "
            "consumer food waste tonnage. Will be updated when verified."
        ),
    ),
    _stub(
        "food-agriculture", "Food & Agriculture",
        "Post-harvest supply chain losses",
        "POST_HARVEST_RESOURCE_ID",
        verification_note=(
            "Post-harvest loss data exists in MoAFW reports but no "
            "queryable Resource API has been confirmed on data.gov.in."
        ),
    ),
    _stub(
        "food-agriculture", "Food & Agriculture",
        "Agricultural fertilizers and pesticides",
        "FERTILIZER_RESOURCE_ID",
        verification_note=(
            "FAO and DAC datasets exist; no verified Resource API "
            "with filterable fields confirmed yet."
        ),
    ),
    _stub(
        "food-agriculture", "Food & Agriculture",
        "Food packaging and single-use containers",
        "FOOD_PACKAGING_RESOURCE_ID",
        verification_note=(
            "No specific Resource API found for food packaging data "
            "on data.gov.in."
        ),
    ),

    # ── Energy & Fuels ────────────────────────────────────────────────────
    _stub(
        "energy-fuels", "Energy & Fuels",
        "Fossil fuels like petrol, diesel, and coal",
        "FOSSIL_FUELS_RESOURCE_ID",
        verification_note=(
            "PPAC (Petroleum Planning & Analysis Cell) publishes fuel "
            "price data. Resource API verification pending."
        ),
    ),
    _stub(
        "energy-fuels", "Energy & Fuels",
        "Inefficient fossil fuel subsidies",
        "FOSSIL_SUBSIDIES_RESOURCE_ID",
        verification_note=(
            "No queryable Resource API for subsidy data found on "
            "data.gov.in at this time."
        ),
    ),
    _stub(
        "energy-fuels", "Energy & Fuels",
        "Renewable energy systems like solar and wind",
        "RENEWABLE_ENERGY_RESOURCE_ID",
        verification_note=(
            "MNRE (Ministry of New and Renewable Energy) data exists "
            "but Resource API not yet verified."
        ),
    ),
    _stub(
        "energy-fuels", "Energy & Fuels",
        "Industrial and residential electricity grid use",
        "ELECTRICITY_GRID_RESOURCE_ID",
        verification_note=(
            "CEA (Central Electricity Authority) publishes grid data. "
            "Resource API verification pending."
        ),
    ),

    # ── Water Resources ───────────────────────────────────────────────────
    _stub(
        "water-resources", "Water Resources",
        "Industrial wastewater and factory effluents",
        "INDUSTRIAL_WASTEWATER_RESOURCE_ID",
        verification_note=(
            "CPCB (Central Pollution Control Board) effluent data "
            "exists; Resource API not confirmed."
        ),
    ),
    _stub(
        "water-resources", "Water Resources",
        "Agricultural irrigation water",
        "AGRICULTURAL_IRRIGATION_RESOURCE_ID",
        verification_note=(
            "CWC (Central Water Commission) and WRIS datasets exist. "
            "Resource API verification pending."
        ),
    ),
    _stub(
        "water-resources", "Water Resources",
        "Municipal and domestic drinking water supply",
        "MUNICIPAL_DRINKING_WATER_RESOURCE_ID",
        verification_note=(
            "MoJS (Ministry of Jal Shakti) Jal Jeevan Mission data "
            "exists. Resource API verification pending."
        ),
    ),

    # ── Consumer Goods & Electronics ─────────────────────────────────────
    _stub(
        "consumer-goods-electronics", "Consumer Goods & Electronics",
        "E-waste like smartphones, laptops, and batteries",
        "EWASTE_RESOURCE_ID",
        verification_note=(
            "MoEFCC (Ministry of Environment) E-waste data is "
            "published but no open queryable Resource API confirmed."
        ),
    ),
    _stub(
        "consumer-goods-electronics", "Consumer Goods & Electronics",
        "Fast fashion textiles and chemical clothing dyes",
        "TEXTILE_RESOURCE_ID",
        verification_note=(
            "No suitable Resource API found for textile/dye data "
            "on data.gov.in."
        ),
    ),
    _stub(
        "consumer-goods-electronics", "Consumer Goods & Electronics",
        "Single-use plastics like grocery bags and straws",
        "SINGLE_USE_PLASTIC_RESOURCE_ID",
        verification_note=(
            "CPCB plastics data exists in reports; no queryable "
            "Resource API confirmed."
        ),
    ),
    _stub(
        "consumer-goods-electronics", "Consumer Goods & Electronics",
        "Durable goods like appliances and furniture",
        "DURABLE_GOODS_RESOURCE_ID",
        verification_note=(
            "No suitable Resource API found for durable goods data."
        ),
    ),

    # ── Chemicals & Hazardous Materials ───────────────────────────────────
    _stub(
        "chemicals-hazardous-materials", "Chemicals & Hazardous Materials",
        "Industrial solvents, paints, and manufacturing toxins",
        "INDUSTRIAL_CHEMICALS_RESOURCE_ID",
        verification_note=(
            "CPCB Hazardous Waste Management data exists. "
            "Resource API not confirmed."
        ),
    ),
    _stub(
        "chemicals-hazardous-materials", "Chemicals & Hazardous Materials",
        "Household chemical cleaners and non-biodegradable detergents",
        "HOUSEHOLD_CHEMICALS_RESOURCE_ID",
        verification_note=(
            "No suitable Resource API found for household chemicals."
        ),
    ),
    _stub(
        "chemicals-hazardous-materials", "Chemicals & Hazardous Materials",
        "Heavy metals like mercury, lead, and cadmium",
        "HEAVY_METALS_RESOURCE_ID",
        verification_note=(
            "CPCB ambient monitoring data mentions heavy metals but "
            "no open queryable Resource API confirmed."
        ),
    ),

    # ── Raw Materials & Infrastructure ────────────────────────────────────
    _stub(
        "raw-materials-infrastructure", "Raw Materials & Infrastructure",
        "Construction materials like concrete, cement, and steel",
        "CONSTRUCTION_MATERIALS_RESOURCE_ID",
        verification_note=(
            "DPIIT and MOSPI track production; no open Resource API "
            "confirmed on data.gov.in."
        ),
    ),
    _stub(
        "raw-materials-infrastructure", "Raw Materials & Infrastructure",
        "Mined tech minerals like lithium, cobalt, and copper",
        "MINED_TECH_MINERALS_RESOURCE_ID",
        verification_note=(
            "IBM (Indian Bureau of Mines) publishes mineral data. "
            "Resource API verification pending."
        ),
    ),
    _stub(
        "raw-materials-infrastructure", "Raw Materials & Infrastructure",
        "Aggregates like sand, gravel, and crushed stone",
        "AGGREGATES_RESOURCE_ID",
        verification_note=(
            "No suitable Resource API found for aggregates data "
            "on data.gov.in."
        ),
    ),

    # ── Services & Corporate Operations ──────────────────────────────────
    _stub(
        "services-corporate-operations", "Services & Corporate Operations",
        "Public procurement items and green government contracts",
        "PUBLIC_PROCUREMENT_RESOURCE_ID",
        verification_note=(
            "GeM (Government e-Marketplace) portal has procurement "
            "data; no open queryable Resource API confirmed."
        ),
    ),
    _stub(
        "services-corporate-operations", "Services & Corporate Operations",
        "Corporate sustainability and ESG reporting data",
        "CORPORATE_ESG_RESOURCE_ID",
        verification_note=(
            "No suitable Resource API found for ESG/sustainability "
            "reporting data on data.gov.in."
        ),
    ),
    _stub(
        "services-corporate-operations", "Services & Corporate Operations",
        "Tourism services, hospitality waste, and eco-travel footprints",
        "TOURISM_RESOURCE_ID",
        verification_note=(
            "Ministry of Tourism publishes visitor arrival data. "
            "Resource API verification pending."
        ),
    ),
)

# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------
_CONFIG_BY_KEY: dict[tuple[str, str], SectorDataConfig] = {
    (config.sector.lower(), config.component.lower()): config
    for config in SECTOR_DATA_CONFIGS
}


def get_sector_config(sector: str, component: str) -> SectorDataConfig | None:
    return _CONFIG_BY_KEY.get((sector.strip().lower(), component.strip().lower()))


def get_all_sector_configs() -> list[dict[str, Any]]:
    return [config.as_dict() for config in SECTOR_DATA_CONFIGS]
