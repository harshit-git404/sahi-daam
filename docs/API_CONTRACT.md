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
  "quickcommerce_price": { "source": "Blinkit", "price": 38.0, "unit": "kg" },
  "market_context": {
    "current_price": 22.5,
    "recent_average": 20.8,
    "change_pct": 8.2,
    "trend": "UP",
    "history_days": 7,
    "observation_count": 6,
    "confidence": "Medium"
  }
}
```

> **Note**: When only a single market observation is available (e.g. today's cached mock data), `market_context.trend` will be `"INSUFFICIENT_DATA"`. This is the honest representation and the UI must display "Not enough recent market history" in this case. Do NOT interpolate, duplicate, or fabricate observations to avoid this state.

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
- `market_context` (dict): Local wholesale market price trend analysis.

### `market_context` Fields
- `current_price` (float): Today's local wholesale reference price in ₹/kg.
- `recent_average` (float): Mean of all available historical observations in ₹/kg.
- `change_pct` (float): `(current_price - recent_average) / recent_average * 100`. Positive = elevated today.
- `trend` (Enum): One of `"UP"`, `"DOWN"`, `"STABLE"`, `"INSUFFICIENT_DATA"`.
  - `UP`: `change_pct > 5%` (consumer-visible significance threshold, not a statistical derivation)
  - `DOWN`: `change_pct < -5%`
  - `STABLE`: `-5% ≤ change_pct ≤ 5%`
  - `INSUFFICIENT_DATA`: fewer than 2 historical observations available
- `history_days` (int): Date span from oldest to newest observation in days.
- `observation_count` (int): Number of price records used for the trend calculation.
- `confidence` (Enum): `"High"` (≥10 obs), `"Medium"` (3–9 obs), `"Low"` (2 obs).

### Architectural Notes
- `market_context` is **read-only context**. It does NOT modify the `fair_price_range` calculation.
- The fair-price engine uses today's wholesale price directly. Trend is additive reasoning context.
- The negotiation engine may use trend to enrich its explanation text but does NOT change its threshold logic.


## POST `/haggle-check`

Negotiation intelligence engine. Analyzes vendor asking price, fair market range, produce quality,
and optional quick-commerce reference to return a structured buying decision and negotiation strategy.

**Request:**
```json
{
  "produce_type": "tomato",
  "asking_price": 50,
  "fair_price_min": 29,
  "fair_price_max": 33,
  "freshness_label": "Fresh",
  "quickcommerce_price": { "source": "Blinkit", "price": 40, "unit": "kg" },
  "language": "hi"
}
```

`language` is optional and defaults to `"hi"`. Supported values are `"hi"` (Hindi), `"ta"` (Tamil), and `"en"` (English). It tells the phrase generator which language the user selected for the current negotiation session.

**Response:**
```json
{
  "verdict": "Overpriced",
  "suggested_price": 29,
  "decision": "OVERPRICED",
  "severity": "SIGNIFICANT",
  "deviation_pct": 51.5,
  "starting_offer": 29,
  "target_price": 31,
  "maximum_reasonable_price": 33,
  "potential_saving": 17,
  "below_fair_amount": 0,
  "reasoning": "Rs50/kg is 51.5% above the fair maximum (Rs33/kg)...",
  "recommendation": {
    "action": "NEGOTIATE",
    "headline": "Rs17 above the estimated fair maximum.",
    "explanation": "Rs50/kg is 51.5% above the fair maximum (Rs33/kg)... vendor more expensive than both fair range and quick-commerce."
  },
  "quality_context": {
    "freshness_label": "Fresh",
    "caution": null
  },
  "alternatives": {
    "quickcommerce": { "source": "Blinkit", "price": 40, "unit": "kg" }
  },
  "phrases": [{ "hindi": "...", "tamil": "...", "english": "...", "phonetic": "..." }],
  "phrases_source": "gemini"
}
```

---

### Decision States

| `decision`        | User label       | Condition                                        |
|-------------------|------------------|--------------------------------------------------|
| `FAIR_PRICE`      | Fair Price       | `fair_min <= asking <= fair_max`                |
| `SLIGHTLY_HIGH`   | Slightly High    | `asking > fair_max` AND deviation <= 10%        |
| `OVERPRICED`      | Overpriced       | `asking > fair_max` AND deviation > 10%         |
| `GOOD_DEAL`       | Good Deal        | `asking < fair_min` AND quality = "Fresh"       |
| `UNUSUALLY_CHEAP` | Unusually Cheap  | `asking < fair_min` AND quality ≠ "Fresh"       |

### Severity

| `severity`    | Condition (deviation from fair boundary)  |
|---------------|-------------------------------------------|
| `NONE`        | 0% (within range)                         |
| `SLIGHT`      | 0% < deviation ≤ 10%                     |
| `MODERATE`    | 10% < deviation ≤ 30%                    |
| `SIGNIFICANT` | deviation > 30%                           |

**Threshold rationale**: 10% on a Rs30 item = Rs3 (tolerable daily fluctuation).
30% on a Rs30 item = Rs9 (clearly worth negotiating). Based on observed mandi price volatility.

### Negotiation Strategy Formulas

| Price position  | `starting_offer`     | `target_price`      | `maximum_reasonable_price` |
|-----------------|----------------------|---------------------|----------------------------|
| WITHIN range    | asking               | asking              | fair_max                   |
| SLIGHTLY above  | fair_mid             | fair_max            | asking (small give)        |
| MODERATE above  | fair_min             | fair_mid            | fair_max                   |
| SIGNIFICANT     | fair_min             | fair_mid            | fair_max                   |
| BELOW range     | asking               | asking              | fair_max                   |

`fair_mid = (fair_min + fair_max) / 2`

### Savings Fields

- `potential_saving`: `max(0, asking - fair_max)` — only non-zero when ABOVE range.
- `below_fair_amount`: `max(0, fair_min - asking)` — only non-zero when BELOW range.
- These fields are mutually exclusive and never both non-zero simultaneously.

### Quality × Price Matrix

| Quality         | Price position | Decision          | Notes                            |
|-----------------|----------------|-------------------|----------------------------------|
| Fresh           | Below range    | GOOD_DEAL         | `quality_context.caution` = note |
| Fresh           | Within         | FAIR_PRICE        | —                                |
| Fresh           | Slightly above | SLIGHTLY_HIGH     | —                                |
| Overripe        | Below range    | UNUSUALLY_CHEAP   | caution: use today               |
| Overripe        | Within         | FAIR_PRICE        | caution: note on quality         |
| Unknown         | Slightly below | FAIR_PRICE        | severity=SLIGHT tolerated        |
| Unknown         | Moderately below| UNUSUALLY_CHEAP  | —                                |

### Quick-Commerce Comparison Logic

- Vendor > QC and vendor > fair_max → "vendor more expensive than both"
- Vendor <= QC and vendor > fair_max → "vendor still cheaper than QC but above fair"
- Vendor <= fair_max and vendor <= fair_min → "vendor clearly cheaper than QC"
- Vendor <= fair_max → "vendor cheaper than QC"

QC comparisons use neutral language; they reflect price reference only, not delivery value.

**Fields:**
- `verdict` (str): Legacy — "Fair Price" | "Overpriced" | "Suspiciously Cheap"
- `suggested_price` (float): Legacy alias for `starting_offer`
- `decision` (str): Machine-readable state (see table above)
- `severity` (str): NONE | SLIGHT | MODERATE | SIGNIFICANT
- `deviation_pct` (float): % from relevant fair range boundary
- `starting_offer` (float): Recommended opening offer
- `target_price` (float): Ideal settlement price
- `maximum_reasonable_price` (float): Do not pay more than this
- `potential_saving` (float): Rs saved per kg if target met (only when ABOVE range)
- `below_fair_amount` (float): Rs below fair min (only when BELOW range)
- `recommendation` (dict): action, headline, explanation
- `quality_context` (dict): freshness_label, caution (null if not applicable)
- `alternatives` (dict): quickcommerce comparison
- `phrases` (list): 2-3 bargaining phrases with `hindi`, `tamil`, `english`, and Hindi `phonetic` fields. The request `language` guides the generated phrase intent and voice UI selection.
- `phrases_source` (str): "gemini" | "fallback"


**Request:**
```json
{
  "produce_type": "tomato",
  "asking_price": 45,
  "fair_price_min": 28,
  "fair_price_max": 34,
  "freshness_label": "Fresh",
  "quickcommerce_price": { "source": "Blinkit", "price": 40.0, "unit": "kg" },
  "language": "ta"
}
```

**Response:**
```json
{
  "verdict": "Overpriced",
  "decision": "OVERPRICED",
  "deviation_pct": 32.4,
  "suggested_price": 28.0,
  "maximum_reasonable_price": 34.0,
  "potential_saving": 11.0,
  "reasoning": "Vendor is asking ₹45/kg, while the estimated fair range for this produce is ₹28–34/kg. The asking price is about 32% above the fair maximum. Blinkit is cheaper at ₹40.0/kg, making the vendor the worst option.",
  "recommendation": {
    "action": "NEGOTIATE",
    "headline": "You're paying above the fair range.",
    "explanation": "Vendor is asking ₹45/kg, while the estimated fair range for this produce is ₹28–34/kg. The asking price is about 32% above the fair maximum. Blinkit is cheaper at ₹40.0/kg, making the vendor the worst option."
  },
  "alternatives": {
    "quickcommerce": {
      "source": "Blinkit",
      "price": 40.0,
      "unit": "kg"
    }
  },
  "phrases": [
    {
      "hindi": "भैया, यह तो बहुत महंगा है। थोड़ा कम कीजिए।",
      "tamil": "அண்ணா, இது ரொம்ப அதிகம். கொஞ்சம் குறையுங்கள்.",
      "english": "Brother, this is too expensive. Please reduce the price a bit.",
      "phonetic": "Bhaiya, yeh toh bahut mehanga hai. Thoda kam kijiye."
    }
  ],
  "phrases_source": "gemini"
}
```

**Fields**:
- `decision` (str): One of `"GOOD_DEAL"`, `"FAIR_PRICE"`, `"OVERPRICED"`, `"UNUSUALLY_CHEAP"`.
- `verdict` (str): Legacy verdict fallback.
- `deviation_pct` (float): The percentage difference from the relevant bound of the fair range.
- `suggested_price` (float): Computed counter-offer or accepted price.
- `maximum_reasonable_price` (float): Maximum price to accept.
- `potential_saving` (float): Savings if target price is achieved.
- `reasoning` (str): Text explaining the math to the user.
- `recommendation` (dict): `action`, `headline`, and `explanation` for the UI decision card.
- `alternatives` (dict): Comparison against other sources (e.g. quickcommerce).
