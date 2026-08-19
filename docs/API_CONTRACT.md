# API Contract

## POST `/scan-produce`

Analyzes produce and returns pricing and quality details.

### Response Shape
```json
{
  "produce_type": "Tomato",
  "freshness_label": "Fresh",
  "freshness_percent": 85,
  "freshness_note": "Slight softness detected — good for immediate use",
  "wholesale_price": 22.0,
  "markup_range": { "min_pct": 30.0, "max_pct": 45.0 },
  "quality_adjustment": -2.0,
  "quality_adjustment_label": "Slight bruising detected",
  "fair_price_range": { "min": 27.0, "max": 30.0, "unit": "kg" },
  "data_confidence": "Estimated",
  "location": "Katpadi, Vellore",
  "date": "2026-08-19",
  "quickcommerce_price": { "source": "Blinkit", "price": 38.0, "unit": "kg" }
}
```

**Fields**:
- `produce_type` (str): Type of produce detected.
- `freshness_label` (Enum): One of `"Fresh"`, `"Slightly Aged"`, `"Overripe"`.
- `freshness_percent` (int): 0-100 indicating exact freshness score.
- `freshness_note` (str): Explanatory text on quality.
- `wholesale_price` (float): Base wholesale price today.
- `markup_range` (dict): Typical local markup percentages.
- `quality_adjustment` (float): Absolute price adjustment for quality.
- `quality_adjustment_label` (str): Explanation for price adjustment.
- `fair_price_range` (dict): Final computed min/max fair price and unit.
- `data_confidence` (Enum): One of `"High"`, `"Medium"`, `"Estimated"`.
- `location` (str): Target market location.
- `date` (str): Snapshot date (YYYY-MM-DD).
- `quickcommerce_price` (dict): Price comparison from quick commerce.

## POST `/haggle-check`

Validates user's asking price.

### Request Shape
```json
{
  "asking_price": 45.0
}
```

### Response Shape
```json
{
  "verdict": "Overpriced",
  "deviation_pct": 32.0,
  "suggested_price": 30.0,
  "reasoning": "Vendor's asking price is significantly above today's fair range for this quality of tomato."
}
```
