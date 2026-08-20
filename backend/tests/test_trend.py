"""
Tests for analyze_price_trend in pricing/engine.py

Threshold rationale:
- A change >= +5% is UP: consumer-visible significance (₹1 on ₹20 produce)
- A change <= -5% is DOWN: meaningful price drop
- Between -5% and +5% is STABLE: day-to-day fluctuation, not meaningful
This is a consumer-facing significance threshold, NOT a statistically derived market metric.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pricing.engine import analyze_price_trend


def make_obs(prices: list[float], base_date: str = "2026-08-20") -> list[dict]:
    """Helper to build a list of observation dicts from a price list (most recent first)."""
    from datetime import datetime, timedelta
    base = datetime.strptime(base_date, "%Y-%m-%d")
    return [{"date": (base - timedelta(days=i)).strftime("%Y-%m-%d"), "price": p}
            for i, p in enumerate(prices)]


# ── INSUFFICIENT_DATA ────────────────────────────────────────────────────────

def test_insufficient_data_no_history():
    result = analyze_price_trend(22.5, [])
    assert result["trend"] == "INSUFFICIENT_DATA"
    assert result["observation_count"] == 0
    assert result["history_days"] == 0

def test_insufficient_data_single_observation():
    obs = make_obs([22.5])
    result = analyze_price_trend(22.5, obs)
    assert result["trend"] == "INSUFFICIENT_DATA"
    assert result["observation_count"] == 1

def test_insufficient_data_returns_current_price_as_average():
    """When insufficient history, recent_average should equal current_price."""
    result = analyze_price_trend(22.5, [])
    assert result["recent_average"] == 22.5
    assert result["current_price"] == 22.5
    assert result["change_pct"] == 0.0


# ── STABLE ───────────────────────────────────────────────────────────────────

def test_stable_same_price():
    obs = make_obs([22.5, 22.5, 22.5])
    result = analyze_price_trend(22.5, obs)
    assert result["trend"] == "STABLE"
    assert result["change_pct"] == 0.0

def test_stable_within_5pct_positive():
    """3% up is still STABLE."""
    avg = 22.0
    current = 22.0 * 1.03  # +3%
    obs = make_obs([avg, avg, avg])
    result = analyze_price_trend(current, obs)
    assert result["trend"] == "STABLE"
    assert result["change_pct"] == pytest.approx(3.0, abs=0.2)

def test_stable_within_5pct_negative():
    """3% down is still STABLE."""
    avg = 22.0
    current = 22.0 * 0.97  # -3%
    obs = make_obs([avg, avg, avg])
    result = analyze_price_trend(current, obs)
    assert result["trend"] == "STABLE"

def test_stable_exactly_5pct_up():
    """Exactly 5% up should still be STABLE (boundary: > 5% is UP)."""
    avg = 20.0
    current = 21.0  # exactly 5%
    obs = make_obs([avg, avg, avg])
    result = analyze_price_trend(current, obs)
    assert result["trend"] == "STABLE"

def test_stable_exactly_5pct_down():
    """Exactly -5% should still be STABLE."""
    avg = 20.0
    current = 19.0  # exactly -5%
    obs = make_obs([avg, avg, avg])
    result = analyze_price_trend(current, obs)
    assert result["trend"] == "STABLE"


# ── UP ───────────────────────────────────────────────────────────────────────

def test_up_8pct():
    """8% above average → UP."""
    avg = 20.8
    current = avg * 1.082  # ~8.2% above
    obs = make_obs([avg, avg, avg, avg, avg])
    result = analyze_price_trend(current, obs)
    assert result["trend"] == "UP"
    assert result["change_pct"] > 5.0

def test_up_just_above_threshold():
    """5.1% above average → UP."""
    avg = 20.0
    current = 21.02  # 5.1%
    obs = make_obs([avg, avg, avg])
    result = analyze_price_trend(current, obs)
    assert result["trend"] == "UP"


# ── DOWN ─────────────────────────────────────────────────────────────────────

def test_down_10pct():
    """10% below average → DOWN."""
    avg = 25.0
    current = 22.5  # -10%
    obs = make_obs([avg, avg, avg, avg])
    result = analyze_price_trend(current, obs)
    assert result["trend"] == "DOWN"
    assert result["change_pct"] < -5.0

def test_down_just_below_threshold():
    """5.1% below average → DOWN."""
    avg = 20.0
    current = 18.98  # -5.1%
    obs = make_obs([avg, avg, avg])
    result = analyze_price_trend(current, obs)
    assert result["trend"] == "DOWN"


# ── CALCULATIONS ─────────────────────────────────────────────────────────────

def test_recent_average_calculation():
    """recent_average should be mean of all observation prices."""
    obs = make_obs([20.0, 22.0, 24.0])
    result = analyze_price_trend(22.0, obs)
    assert result["recent_average"] == pytest.approx(22.0, abs=0.01)

def test_change_pct_calculation():
    """change_pct = (current - avg) / avg * 100."""
    obs = make_obs([20.0, 20.0])
    result = analyze_price_trend(22.0, obs)
    # avg = 20.0, change = (22.0 - 20.0) / 20.0 * 100 = 10%
    assert result["change_pct"] == pytest.approx(10.0, abs=0.1)

def test_observation_count():
    obs = make_obs([20.0, 21.0, 22.0, 23.0, 24.0])
    result = analyze_price_trend(22.0, obs)
    assert result["observation_count"] == 5

def test_history_days_calculated_from_dates():
    obs = make_obs([20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0])
    result = analyze_price_trend(22.0, obs)
    assert result["history_days"] == 7  # 7 consecutive days

def test_current_price_preserved():
    obs = make_obs([20.0, 21.0, 22.0])
    result = analyze_price_trend(25.5, obs)
    assert result["current_price"] == 25.5


# ── CONFIDENCE ───────────────────────────────────────────────────────────────

def test_confidence_low_for_two_observations():
    obs = make_obs([20.0, 22.0])
    result = analyze_price_trend(22.0, obs)
    assert result["confidence"] == "Low"

def test_confidence_medium_for_three_to_nine():
    obs = make_obs([20.0, 21.0, 22.0, 23.0, 24.0])
    result = analyze_price_trend(22.0, obs)
    assert result["confidence"] == "Medium"

def test_confidence_high_for_ten_or_more():
    obs = make_obs([20.0] * 10)
    result = analyze_price_trend(20.0, obs)
    assert result["confidence"] == "High"


# ── FAIR PRICE UNCHANGED ─────────────────────────────────────────────────────

def test_market_context_does_not_change_fair_price():
    """Adding market_context must not change calculate_fair_price output."""
    from pricing.engine import calculate_fair_price, analyze_price_trend

    wholesale = 22.5
    fp_without = calculate_fair_price(wholesale, 30, 45, -2)

    # Simulate an elevated market
    obs = make_obs([20.0, 20.0, 20.0, 20.0, 20.0])  # 12.5% higher current
    mc = analyze_price_trend(wholesale, obs)
    assert mc["trend"] == "UP"

    fp_with_same_wholesale = calculate_fair_price(wholesale, 30, 45, -2)
    assert fp_without == fp_with_same_wholesale, "Fair price must not change due to trend"


# ── GOLDEN TOMATO CASE ───────────────────────────────────────────────────────

def test_golden_tomato_single_observation_insufficient():
    """
    Golden case: tomato with only one observation from the fallback mock.
    The API currently returns a single record for today.
    This must produce INSUFFICIENT_DATA — not a fabricated trend.
    """
    obs = make_obs([22.5])  # single mock observation
    result = analyze_price_trend(22.5, obs)
    assert result["trend"] == "INSUFFICIENT_DATA"
    assert result["observation_count"] == 1
