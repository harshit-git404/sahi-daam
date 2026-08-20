"""
Tests for the Negotiation Intelligence Engine (backend/pricing/engine.py).

Test matrix verifies:
  - All 5 user-facing decision states
  - 3 severity bands (SLIGHT/MODERATE/SIGNIFICANT)
  - Quality-aware decision matrix
  - Negotiation strategy formulas
  - Savings calculations
  - below_fair_amount for GOOD_DEAL
  - Quick-commerce comparisons
  - Boundary conditions near thresholds
"""
import pytest
from pricing.engine import (
    analyze_purchase_decision,
    SLIGHT_THRESHOLD_PCT,
    SIGNIFICANT_THRESHOLD_PCT,
)

# ─────────────────────────────────────────────────────────────
# BASELINE: fair range Rs29–33 used throughout
# ─────────────────────────────────────────────────────────────

def r(fair_min=29, fair_max=33, asking=None, quality=None, qc=None):
    """Shorthand test helper."""
    return analyze_purchase_decision(fair_min, fair_max, asking, quality, qc)


# ── OVERPRICED / SIGNIFICANTLY above range ──────────────────

def test_significantly_overpriced():
    """Rs50 vs Rs29–33: deviation = 51.5% >> 30% → OVERPRICED / SIGNIFICANT."""
    result = r(asking=50)
    assert result["decision"] == "OVERPRICED"
    assert result["severity"] == "SIGNIFICANT"
    assert result["recommendation"]["action"] == "NEGOTIATE"
    # Negotiation strategy: start=f_min, target=fair_mid, max=f_max
    assert result["starting_offer"] == 29
    assert result["target_price"] == 31   # (29+33)/2 = 31
    assert result["maximum_reasonable_price"] == 33
    assert result["potential_saving"] == 17   # 50 - 33 = 17
    assert result["below_fair_amount"] == 0.0
    # Deviation percentage
    expected_dev = round(((50 - 33) / 33) * 100, 1)
    assert result["deviation_pct"] == expected_dev


def test_moderately_overpriced():
    """Rs40 vs Rs29–33: deviation = 21.2% → OVERPRICED / MODERATE."""
    result = r(asking=40)
    assert result["decision"] == "OVERPRICED"
    assert result["severity"] == "MODERATE"
    assert result["starting_offer"] == 29
    assert result["target_price"] == 31
    assert result["maximum_reasonable_price"] == 33
    assert result["potential_saving"] == 7   # 40 - 33 = 7
    expected_dev = round(((40 - 33) / 33) * 100, 1)
    assert result["deviation_pct"] == expected_dev


def test_slightly_high():
    """Rs34 vs Rs29–33: deviation = 3.0% → SLIGHTLY_HIGH / SLIGHT."""
    result = r(asking=34)
    assert result["decision"] == "SLIGHTLY_HIGH"
    assert result["severity"] == "SLIGHT"
    assert result["recommendation"]["action"] == "NEGOTIATE"
    # Slight strategy: start=fair_mid, target=f_max, max=asking (small give)
    assert result["starting_offer"] == 31   # fair mid
    assert result["target_price"] == 33     # f_max
    assert result["maximum_reasonable_price"] == 34  # asking (small deviation)
    assert result["potential_saving"] == 1   # 34 - 33 = 1
    expected_dev = round(((34 - 33) / 33) * 100, 1)
    assert result["deviation_pct"] == expected_dev


# ── FAIR PRICE ───────────────────────────────────────────────

def test_fair_price_mid():
    """Rs31 (mid-range) → FAIR_PRICE / BUY."""
    result = r(asking=31)
    assert result["decision"] == "FAIR_PRICE"
    assert result["severity"] == "NONE"
    assert result["recommendation"]["action"] == "BUY"
    assert result["deviation_pct"] == 0.0
    assert result["potential_saving"] == 0.0
    assert result["below_fair_amount"] == 0.0
    # No aggressive negotiation
    assert result["starting_offer"] == 31
    assert result["target_price"] == 31
    assert result["maximum_reasonable_price"] == 33


def test_fair_price_at_min():
    """Rs29 (exactly at fair_min) → FAIR_PRICE."""
    result = r(asking=29)
    assert result["decision"] == "FAIR_PRICE"


def test_fair_price_at_max():
    """Rs33 (exactly at fair_max) → FAIR_PRICE."""
    result = r(asking=33)
    assert result["decision"] == "FAIR_PRICE"


# ── GOOD DEAL ────────────────────────────────────────────────

def test_good_deal_fresh_moderately_below():
    """Rs27 (fresh, 6.9% below) → GOOD_DEAL / BUY."""
    result = r(asking=27, quality="Fresh")
    assert result["decision"] == "GOOD_DEAL"
    assert result["recommendation"]["action"] == "BUY"
    assert result["below_fair_amount"] == 2   # 29 - 27 = 2
    assert result["potential_saving"] == 0.0  # not overpriced
    expected_dev = round(((29 - 27) / 29) * 100, 1)
    assert result["deviation_pct"] == expected_dev


def test_good_deal_fresh_significantly_below():
    """Rs20 (fresh, 31% below) → GOOD_DEAL / BUY."""
    result = r(asking=20, quality="Fresh")
    assert result["decision"] == "GOOD_DEAL"
    assert result["recommendation"]["action"] == "BUY"
    assert result["below_fair_amount"] == 9  # 29 - 20 = 9
    quality_ctx = result["quality_context"]
    assert quality_ctx["caution"] == "Fresh quality at a below-fair price — a genuine good deal."


# ── UNUSUALLY CHEAP ──────────────────────────────────────────

def test_unusually_cheap_overripe():
    """Rs20 (overripe, 31% below) → UNUSUALLY_CHEAP."""
    result = r(asking=20, quality="Overripe")
    assert result["decision"] == "UNUSUALLY_CHEAP"
    assert result["recommendation"]["action"] == "CHECK_QUALITY"
    assert result["below_fair_amount"] == 9
    caution = result["quality_context"]["caution"]
    assert caution is not None and "use it today" in caution


def test_unusually_cheap_no_quality_info():
    """Rs20 (no quality info, 31% below) → UNUSUALLY_CHEAP."""
    result = r(asking=20, quality=None)
    assert result["decision"] == "UNUSUALLY_CHEAP"
    assert result["recommendation"]["action"] == "CHECK_QUALITY"


# ── QUALITY MATRIX EDGE CASES ────────────────────────────────

def test_slightly_below_unknown_quality():
    """Rs28 (1 below min, 3.4% → SLIGHT) without quality → FAIR_PRICE-like (slight below = ok)."""
    result = r(asking=28)  # 3.4% below fair_min=29
    assert result["decision"] == "FAIR_PRICE"  # slight below without quality context
    assert result["severity"] == "SLIGHT"


def test_quality_caution_within_range_overripe():
    """Rs31 (within range, overripe) → FAIR_PRICE but with quality caution."""
    result = r(asking=31, quality="Overripe")
    assert result["decision"] == "FAIR_PRICE"
    caution = result["quality_context"]["caution"]
    assert caution is not None and "overripe" in caution.lower()


# ── NEGOTIATION STRATEGY FORMULAS ────────────────────────────

def test_negotiation_significant_start_at_fair_min():
    """Significant deviation: start = f_min, target = fair_mid."""
    result = r(asking=50)
    assert result["starting_offer"] == 29
    assert result["target_price"] == 31  # (29+33)/2


def test_negotiation_slight_start_at_fair_mid():
    """Slight deviation: start = fair_mid."""
    result = r(asking=34)
    assert result["starting_offer"] == 31  # (29+33)/2


def test_negotiation_fair_price_no_aggression():
    """Fair price: start == asking, max = f_max."""
    result = r(asking=31)
    assert result["starting_offer"] == 31
    assert result["maximum_reasonable_price"] == 33


def test_negotiation_good_deal_start_at_asking():
    """Good deal: starting offer = asking (already good)."""
    result = r(asking=27, quality="Fresh")
    assert result["starting_offer"] == 27


# ── SAVINGS CALCULATIONS ─────────────────────────────────────

def test_potential_saving_overpriced():
    assert r(asking=50)["potential_saving"] == 17.0   # 50-33


def test_potential_saving_fair():
    assert r(asking=31)["potential_saving"] == 0.0


def test_below_fair_amount_good_deal():
    assert r(asking=27, quality="Fresh")["below_fair_amount"] == 2.0  # 29-27


def test_below_fair_amount_not_set_for_overpriced():
    assert r(asking=50)["below_fair_amount"] == 0.0


# ── QUICK-COMMERCE COMPARISONS ───────────────────────────────

def test_qc_vendor_worse_than_both():
    """Rs50 vs fair Rs29–33, Blinkit Rs40 → vendor worst option."""
    result = r(asking=50, qc={"source": "Blinkit", "price": 40, "unit": "kg"})
    assert result["alternatives"]["quickcommerce"]["price"] == 40
    assert "more expensive than both" in result["recommendation"]["explanation"]


def test_qc_vendor_above_fair_but_cheaper_than_qc():
    """Rs35 vs fair Rs29–33, Blinkit Rs40 → above fair but cheaper than QC."""
    result = r(asking=35, qc={"source": "Blinkit", "price": 40, "unit": "kg"})
    assert "still cheaper than Blinkit" in result["recommendation"]["explanation"]


def test_qc_vendor_fair_cheaper_than_qc():
    """Rs31 (fair price) vs Blinkit Rs40 → vendor cheaper than QC."""
    result = r(asking=31, qc={"source": "Blinkit", "price": 40, "unit": "kg"})
    # Within range + cheaper than QC
    assert result["decision"] == "FAIR_PRICE"
    assert "cheaper than Blinkit" in result["recommendation"]["explanation"]


def test_qc_structure():
    result = r(asking=50, qc={"source": "Zepto", "price": 45, "unit": "kg"})
    assert "quickcommerce" in result["alternatives"]
    assert result["alternatives"]["quickcommerce"]["source"] == "Zepto"


# ── BOUNDARY CONDITIONS ──────────────────────────────────────

def test_boundary_exactly_slight_threshold():
    """Exactly at 10% above f_max: still SLIGHT (<=)."""
    # f_max=33, 10% above = 33 * 1.10 = 36.3
    result = r(asking=36.3)
    assert result["severity"] == "SLIGHT"
    assert result["decision"] == "SLIGHTLY_HIGH"


def test_boundary_just_above_slight_threshold():
    """Just above 10%: becomes MODERATE → OVERPRICED."""
    # 10.1% above f_max=33 → 33 * 1.101 = 36.33...
    result = r(asking=36.4)
    assert result["severity"] == "MODERATE"
    assert result["decision"] == "OVERPRICED"


def test_boundary_exactly_significant_threshold():
    """Exactly at 30% above f_max: still MODERATE (<=)."""
    # 33 * 1.30 = 42.9
    result = r(asking=42.9)
    assert result["severity"] == "MODERATE"


def test_boundary_just_above_significant_threshold():
    """Just above 30%: becomes SIGNIFICANT."""
    # 33 * 1.301 = 42.93...
    result = r(asking=43.0)
    assert result["severity"] == "SIGNIFICANT"

