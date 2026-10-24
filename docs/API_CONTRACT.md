# API Contract

This document specifies the exact request and response schemas for all active endpoints in the Sahi Daam backend.

---

## 1. POST `/scan-produce`

Analyzes an uploaded produce image, detects produce type and freshness, fetches live Agmarknet mandi wholesale prices and 10-day trends, calculates fair retail price ranges, and retrieves quick-commerce retail benchmarks.

### Request Shape
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "produce_type": "tomato",
  "state": "Tamil Nadu",
  "district": "Vellore",
  "market": "Vellore",
  "purchase_type": "street_vendor"
}
```

* **`image`** *(string, required)*: Base64-encoded image string or Data URL (`data:image/...;base64,...`).
* **`produce_type`** *(string, optional)*: Optional produce type hint. Primary classification is performed by ML.
* **`state`** *(string, optional)*: Mandi search filter for State.
* **`district`** *(string, optional)*: Mandi search filter for District.
* **`market`** *(string, optional)*: Mandi search filter for specific Market name.
* **`purchase_type`** *(string, optional, default: `"street_vendor"`)*: Purchase channel context.

### Response Shape (Full / Success)
```json
{
  "produce_type": "Tomato",
  "detected_produce_id": "tomato",
  "produce_confidence": 95.5,
  "classification_confidence": 95.5,
  "analysis_provider": "gemini",
  "freshness_label": "Fresh",
  "freshness_percent": 88,
  "freshness_note": "Firm texture with vibrant red skin and intact calyx.",
  "quality_adjustment": 0,
  "quality_adjustment_label": "No freshness deduction",
  "market_status": "AVAILABLE",
  "wholesale_price": 24.0,
  "markup_range": {
    "min_pct": 30,
    "max_pct": 45
  },
  "fair_price_range": {
    "min": 31.2,
    "max": 34.8,
    "unit": "kg"
  },
  "data_confidence": "High",
  "location": "Vellore, Vellore",
  "date": "2026-08-20",
  "market": {
    "status": "AVAILABLE",
    "today_price": 24.0,
    "unit": "kg",
    "date": "2026-08-20",
    "market_name": "Vellore",
    "district": "Vellore",
    "current_value": 24.0,
    "average_10_days": 23.5,
    "high_10_days": 26.0,
    "low_10_days": 21.0,
    "percentage_change": 2.13,
    "trend": "UP",
    "history": [
      { "date": "2026-08-20", "value": 24.0 }
    ],
    "periods_available": 10
  },
  "retail": {
    "status": "AVAILABLE",
    "commodity": "tomato",
    "location": "Vellore, Tamil Nadu",
    "products": [
      {
        "platform": "blinkit",
        "commodity": "tomato",
        "product_name": "Tomato Hybrid",
        "variant": "regular",
        "quantity": "1 kg",
        "quantity_kg": 1.0,
        "price": 38.0,
        "mrp": 45.0,
        "price_per_kg": 38.0,
        "location": "Vellore, Tamil Nadu",
        "location_note": null,
        "collected_at": "2026-08-20T08:30:00"
      }
    ],
    "best_price_per_kg": 38.0,
    "best_platform": "blinkit",
    "collected_at": "2026-08-20T08:30:00",
    "cache_age_hours": 2.4,
    "data_source_type": "cached_snapshot",
    "source": "Cached retail snapshot from friend's Blinkit/Zepto collector. Not live — refresh by running the offline collector script."
  },
  "pricing": {
    "fair_price_min": 31.2,
    "fair_price_max": 34.8
  },
  "online_reference_min": 38.0,
  "online_reference_max": 42.0,
  "quickcommerce_price": {
    "source": "Blinkit",
    "price": 38.0,
    "unit": "kg"
  }
}
```

### Unavailability States
* When Agmarknet market data is unavailable:
  * `market_status`: `"UNAVAILABLE"`
  * `wholesale_price`: `null`
  * `fair_price_range`: `null`
  * `pricing`: `null`
  * `data_confidence`: `"Unavailable"`
  * `market`: contains default block with `"status": "UNAVAILABLE"`, `today_price: null`, `trend: "UNAVAILABLE"`, `history: []`.
* When Retail snapshot data is unavailable:
  * `retail.status`: `"UNAVAILABLE"`
  * `retail.products`: `[]`
  * `online_reference_min`: `null`
  * `online_reference_max`: `null`
  * `quickcommerce_price`: `null`
* When image is missing or cannot be decoded: HTTP `400 Bad Request`.
* When both Gemini and local ML fallback fail: HTTP `503 Service Unavailable`.

---

## 2. POST `/haggle-check`

Validates an asking price against the fair price range for street-vendor produce purchases and provides structured haggle guidance.

### Request Shape
```json
{
  "asking_price": 45.0,
  "fair_price_min": 31.2,
  "fair_price_max": 34.8,
  "purchase_type": "street_vendor",
  "market_reference": 24.0,
  "online_reference_min": 38.0,
  "online_reference_max": 42.0
}
```

* **`asking_price`** *(float, required, `gt=0`)*: The vendor's asking price.
* **`fair_price_min`** *(float, required, `ge=0`)*: Lower fair price boundary from `/scan-produce`.
* **`fair_price_max`** *(float, required, `ge=0`)*: Upper fair price boundary (`fair_price_max >= fair_price_min`).
* **`purchase_type`** *(string, default: `"street_vendor"`)*: Must be `"street_vendor"`. Other purchase types return HTTP 400.
* **`market_reference`** *(float, optional)*: Wholesale reference price for echoing in haggle context.
* **`online_reference_min`** *(float, optional)*: Minimum quick-commerce retail reference price.
* **`online_reference_max`** *(float, optional)*: Maximum quick-commerce retail reference price.

### Response Shape
```json
{
  "verdict": "HIGH",
  "deviation_pct": 29.31,
  "suggested_price": 33.0,
  "suggested_price_min": 31.2,
  "suggested_price_max": 34.8,
  "explanation": "The asking price is 29.3% above the upper fair-price boundary.",
  "market_reference": 24.0,
  "online_reference_min": 38.0,
  "online_reference_max": 42.0
}
```

* **`verdict`** *(string)*:
  * `"HIGH"`: Asking price is greater than `fair_price_max`.
  * `"LOW"`: Asking price is lower than `fair_price_min` (good deal).
  * `"FAIR"`: Asking price is within `[fair_price_min, fair_price_max]`.
* **`deviation_pct`** *(float)*: Percentage deviation relative to the relevant boundary.
* **`suggested_price`** *(float)*: Counter-offer recommendation (midpoint if `"HIGH"`, asking price if `"LOW"` or `"FAIR"`).
* **`suggested_price_min`** / **`suggested_price_max`** *(float)*: Re-stated fair boundaries.
* **`explanation`** *(string)*: Plain-text explanation for user bargaining.

---

## 3. GET `/market-price` and GET `/api/market-price`

Fetches and normalizes live mandi wholesale prices directly from Agmarknet (via `data.gov.in`). Both path aliases are supported for direct API consumers and Vite proxy rewrites (`/api` rewrite).

### Query Parameters
* **`commodity`** *(string, required)*: Produce name (e.g., `"Tomato"`, `"Potato"`, `"Onion"`).
* **`state`** *(string, optional)*: Target state (defaults to `DEFAULT_STATE` from `.env` if not provided).
* **`district`** *(string, optional)*: Target district.
* **`market`** *(string, optional)*: Target market name filter.

### Response Shape
```json
{
  "commodity": "tomato",
  "source": "data.gov.in/agmarknet",
  "records": [
    {
      "commodity": "tomato",
      "variety": "Hybrid",
      "state": "Tamil Nadu",
      "district": "Vellore",
      "market": "Vellore",
      "arrival_date": "20/08/2026",
      "min_price_per_kg": 20.0,
      "max_price_per_kg": 26.0,
      "modal_price_per_kg": 24.0,
      "source": "data.gov.in/agmarknet"
    }
  ]
}
```

---

## 4. GET `/retail-prices`

Returns normalized retail benchmark prices from cached snapshots (Blinkit, Zepto).

### Query Parameters
* **`commodity`** *(string, required)*: Produce name or commodity ID (e.g. `"tomato"`, `"potato"`).
* **`location`** *(string, optional)*: Location string for transparency comparison.

### Response Shape (Available)
```json
{
  "status": "AVAILABLE",
  "commodity": "tomato",
  "location": "Vellore, Tamil Nadu",
  "products": [
    {
      "platform": "blinkit",
      "commodity": "tomato",
      "product_name": "Tomato Hybrid",
      "variant": "regular",
      "quantity": "1 kg",
      "quantity_kg": 1.0,
      "price": 38.0,
      "mrp": 45.0,
      "price_per_kg": 38.0,
      "location": "Vellore, Tamil Nadu",
      "location_note": null,
      "collected_at": "2026-08-20T08:30:00"
    }
  ],
  "best_price_per_kg": 38.0,
  "best_platform": "blinkit",
  "collected_at": "2026-08-20T08:30:00",
  "cache_age_hours": 2.4,
  "data_source_type": "cached_snapshot",
  "source": "Cached retail snapshot from friend's Blinkit/Zepto collector..."
}
```

### Response Shape (Unavailable or Unsupported Commodity)
```json
{
  "status": "UNAVAILABLE",
  "commodity": "dragonfruit",
  "location": "Vellore, Tamil Nadu",
  "products": [],
  "message": "Retail comparison is not available for 'dragonfruit'. Supported commodities include tomato, potato, onion, and others."
}
```

---

## 5. Sector Endpoints

* **GET `/sector-status`**: Lists all configured components in the sector registry and their official dataset availability.
* **GET `/sector-analysis?sector={sector}&component={component}`**: Fetches official data.gov.in records for a given non-produce component and computes a distinct-period metric history and trend.

---

## 6. Community Price Endpoints

### POST `/community-prices` (Alias: `/api/community-prices`)

Submit a crowd-sourced produce price observation from an ordinary customer or vendor.

#### Request Shape
```json
{
  "commodity_id": "tomato",
  "locality_id": "loc_katpadi",
  "locality_name": "Katpadi",
  "district": "Vellore",
  "state": "Tamil Nadu",
  "pincode": "632014",
  "price": 28.0,
  "unit": "kg",
  "source_type": "customer",
  "contributor_id": "cust_mock_001",
  "observed_at": "2026-10-23T11:00:00Z"
}
```

* **`commodity_id`** *(string, required)*: Canonical commodity ID or recognizable alias (`"tomato"`, `"onion"`, `"potato"`, etc.).
* **`locality_id`** *(string, optional)*: Pre-existing locality identifier (e.g. `"loc_katpadi"`).
* **`locality_name`** *(string, optional)*: Creates/resolves locality on the fly if `locality_id` is omitted.
* **`price`** *(float, required)*: Positive finite price.
* **`unit`** *(string, required)*: Supported unit (`kg`, `g`, `500g`, `250g`, `100g`, `piece`, `dozen`, `bunch`). Ambiguous units (`box`, `bag`, `crate`) are rejected.
* **`source_type`** *(string, required)*: Contributor category: `"customer"` or `"vendor"`.
* **`contributor_id`** *(string, optional)*: Contributor identifier (mock or anonymous).
* **`observed_at`** *(datetime, optional)*: ISO timestamp of observation (defaults to current time; future timestamps rejected).

#### Response Shape (HTTP 201)
```json
{
  "status": "recorded",
  "observation": {
    "id": "cpo_a1b2c3d4e5f6",
    "commodity_id": "tomato",
    "price": 28.0,
    "unit": "kg",
    "locality_id": "loc_katpadi",
    "source_type": "customer",
    "contributor_id": "cust_mock_001",
    "observed_at": "2026-10-23T11:00:00Z",
    "created_at": "2026-10-23T11:05:00Z",
    "provenance": "community_submission",
    "is_duplicate": false,
    "duplicate_of_id": null,
    "duplicate_reason": null,
    "normalized_price_per_kg": 28.0,
    "is_outlier": false
  },
  "is_duplicate": false,
  "duplicate_of_id": null,
  "duplicate_reason": null,
  "normalized_price_per_kg": 28.0,
  "warnings": []
}
```

---

### GET `/community-prices` (Alias: `/api/community-prices`)

Query crowd-sourced price observations and statistical summary metrics across a configurable rolling temporal window.

#### Query Parameters
* **`commodity_id`** *(string, optional)*: Filter by produce identifier.
* **`locality_id`** *(string, optional)*: Filter by locality identifier.
* **`source_type`** *(string, optional)*: Filter by `"customer"` or `"vendor"`.
* **`window_days`** *(integer, optional, default: `2`)*: Rolling demo window in days.
* **`exclude_duplicates`** *(boolean, optional, default: `true`)*: Exclude conservative duplicates from results.
* **`limit`** *(integer, optional, default: `50`, max: `100`)*: Safe pagination limit.
* **`offset`** *(integer, optional, default: `0`)*: Pagination offset.

#### Response Shape (HTTP 200)
```json
{
  "total_count": 3,
  "window_days": 2,
  "items": [
    {
      "id": "obs_tomato_katpadi_01",
      "commodity_id": "tomato",
      "price": 28.0,
      "unit": "kg",
      "locality_id": "loc_katpadi",
      "source_type": "customer",
      "contributor_id": "cust_mock_001",
      "observed_at": "2026-10-23T09:00:00Z",
      "created_at": "2026-10-23T09:00:00Z",
      "provenance": "mock_seed_survey",
      "is_duplicate": false,
      "duplicate_of_id": null,
      "duplicate_reason": null,
      "normalized_price_per_kg": 28.0,
      "is_outlier": false
    }
  ],
  "summary": {
    "sample_count": 3,
    "average_price": 29.0,
    "median_price": 29.0,
    "min_price": 28.0,
    "max_price": 30.0,
    "duplicate_count": 0
  }
}
```

---

## 4. Locations & Mandi Endpoints

### GET `/localities` (Alias: `/api/localities`)
Retrieve list of registered localities with optional postal code (pincode) filtering.

#### Query Parameters:
* **`pincode`** *(string, optional)*: 6-digit postal code (e.g. `"632014"`).

#### Response (HTTP 200):
```json
[
  {
    "id": "loc_katpadi",
    "name": "Katpadi",
    "pincode": "632014",
    "district": "Vellore",
    "state": "Tamil Nadu"
  }
]
```

---

### GET `/mandis` (Alias: `/api/mandis`)
Retrieve registered wholesale agricultural markets (mandis).

#### Query Parameters:
* **`district`** *(string, optional)*: Filter mandis by district name.

#### Response (HTTP 200):
```json
[
  {
    "id": "mandi_vellore",
    "market_name": "Vellore Mandi",
    "district": "Vellore",
    "state": "Tamil Nadu",
    "distance_km_reference": 5.5,
    "provenance_note": "Official Agmarknet wholesale reporting market",
    "is_mock": false
  }
]
```

---

### GET `/mandis/recommendation` (Alias: `/api/mandis/recommendation`)
Suggest the nearest and most reliable wholesale mandi for a locality, verifying reference distance and commodity data availability.

#### Query Parameters:
* **`locality_id`** *(string, required)*: Locality ID (e.g. `"loc_katpadi"`).
* **`commodity_id`** *(string, optional)*: Commodity ID to verify active wholesale records.

#### Response (HTTP 200):
```json
{
  "suggested_mandi": {
    "id": "mandi_katpadi",
    "market_name": "Katpadi Uzhavar Sandhai",
    "district": "Vellore",
    "state": "Tamil Nadu",
    "distance_km_reference": 2.2,
    "provenance_note": "Direct farmer retail market",
    "is_mock": true
  },
  "locality": {
    "id": "loc_katpadi",
    "name": "Katpadi",
    "pincode": "632014",
    "district": "Vellore",
    "state": "Tamil Nadu"
  },
  "has_recommendation": true,
  "confidence": "high",
  "distance_km": 2.2,
  "reason": "Recommended based on geographic alignment with Vellore. Configured reference distance is 2.2 km. Active wholesale records confirmed for tomato.",
  "available_mandis": [...]
}
```

---

## 5. Calculation Ledger & SHA-256 Hash Chain Endpoints

### GET `/calculations` (Alias: `/api/calculations`)
Retrieve paginated calculation audit history from the persistent SQLite ledger.

#### Query Parameters:
* **`commodity_id`** *(string, optional)*: Filter by commodity ID.
* **`locality_id`** *(string, optional)*: Filter by locality ID.
* **`limit`** *(integer, optional, default: 50, max: 100)*: Items per page.
* **`offset`** *(integer, optional, default: 0)*: Pagination offset.

#### Response (HTTP 200):
```json
{
  "calculations": [
    {
      "id": "calc_a1b2c3d4e5f6",
      "sequence_number": 1,
      "commodity_id": "tomato",
      "locality_id": "loc_katpadi",
      "status": "TRANSPORT_AWARE_RECONCILED",
      "algorithm_version": "v2.0-locality-reconciled",
      "schema_version": "1.0.0",
      "previous_record_hash": "0000000000000000000000000000000000000000000000000000000000000000",
      "current_record_hash": "3f8b72e1c9a...",
      "is_mock": true,
      "created_at": "2026-10-24T05:30:00Z"
    }
  ],
  "total_count": 1,
  "limit": 50,
  "offset": 0
}
```

---

### GET `/calculations/{calculation_id}` (Alias: `/api/calculations/{calculation_id}`)
Retrieve single calculation audit record with full canonical serialized evidence.

---

### GET `/calculations/{calculation_id}/export` (Alias: `/api/calculations/{calculation_id}/export`)
Download canonical calculation evidence file as a downloadable JSON attachment (`sahi_daam_{id}.json`). Preserves cryptographic hash envelope and canonical formatting.

---

### GET `/ledger/verify` (Alias: `/api/ledger/verify`)
Perform full cryptographic verification of the global SHA-256 hash chain:
1. Sequence continuity (`1, 2, ..., N`).
2. Genesis hash check (`seq 1 -> 64 zeros`).
3. Cryptographic link (`rec[i].prev == rec[i-1].curr`).
4. Canonical JSON SHA-256 hash recomputation.
5. Checkpoint height validation (if checkpoint supplied).

#### Response (HTTP 200):
```json
{
  "is_valid": true,
  "total_records": 12,
  "last_sequence_number": 12,
  "last_record_hash": "a4c2e...",
  "tampered_sequences": [],
  "errors": [],
  "checkpoint_verified": false,
  "verified_at": "2026-10-24T05:35:00Z"
}
```

---

### POST `/ledger/checkpoint` (Alias: `/api/ledger/checkpoint`)
Create a verifiable trusted checkpoint snapshot at current ledger height.

#### Response (HTTP 201):
```json
{
  "checkpoint_id": "ckpt_seq_12_a4c2e91b",
  "last_verified_sequence": 12,
  "last_record_hash": "a4c2e...",
  "record_count": 12,
  "created_at": "2026-10-24T05:35:00Z",
  "ledger_schema_version": "1.0.0",
  "algorithm_version": "v2.0-locality-reconciled"
}
```

---

### GET `/ledger/checkpoint` (Alias: `/api/ledger/checkpoint`)
Retrieve the latest trusted checkpoint for the ledger.

