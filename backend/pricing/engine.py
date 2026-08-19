from typing import Dict

def calculate_fair_price(wholesale_price: float, markup_min_pct: float, markup_max_pct: float, quality_adjustment: int) -> Dict[str, float]:
    """
    Calculates a fair retail price range based on wholesale data, typical markups, and freshness.
    Returns: {"min": float, "max": float}
    """
    # TODO(Person 3): implement
    pass

def calculate_haggle_verdict(asking_price: float, fair_price_range: Dict[str, float]) -> dict:
    """
    Checks asking price against fair price range.
    Returns:
    {
      "verdict": "Overpriced" | "Fair Price",
      "deviation_pct": float,
      "suggested_price": float,
      "reasoning": str
    }
    """
    # TODO(Person 3): implement
    pass
