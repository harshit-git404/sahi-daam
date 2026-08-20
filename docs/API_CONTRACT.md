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

Analyzes a vendor's asking price against the fair market price and dynamically generates haggling strategy and Hindi phrasebook.

**Request:**
```json
{
  "produce_type": "tomato",
  "asking_price": 45,
  "fair_price_min": 28,
  "fair_price_max": 34,
  "freshness_label": "Fresh",
  "quickcommerce_price": { "source": "Blinkit", "price": 40.0, "unit": "kg" }
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
