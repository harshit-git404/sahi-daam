import pytest
from pricing.engine import analyze_purchase_decision

def test_overpriced_decision():
    result = analyze_purchase_decision(29, 33, 50)
    assert result["decision"] == "OVERPRICED"
    assert result["recommendation"]["action"] == "NEGOTIATE"
    assert result["suggested_price"] == 29
    assert result["maximum_reasonable_price"] == 33
    assert result["potential_saving"] == 17
    assert "about 52% above" in result["recommendation"]["explanation"]

def test_fair_price_decision():
    result = analyze_purchase_decision(29, 33, 31)
    assert result["decision"] == "FAIR_PRICE"
    assert result["recommendation"]["action"] == "BUY"
    assert result["suggested_price"] == 31
    assert result["potential_saving"] == 0

def test_good_deal_decision():
    result = analyze_purchase_decision(29, 33, 27, quality_info="Fresh")
    assert result["decision"] == "GOOD_DEAL"
    assert result["recommendation"]["action"] == "BUY"

def test_unusually_cheap_decision():
    result = analyze_purchase_decision(29, 33, 20, quality_info="Overripe")
    assert result["decision"] == "UNUSUALLY_CHEAP"
    assert result["recommendation"]["action"] == "CHECK QUALITY"

def test_quickcommerce_comparison():
    result = analyze_purchase_decision(29, 33, 50, quickcommerce_price={"source": "Blinkit", "price": 40, "unit": "kg"})
    assert result["alternatives"]["quickcommerce"]["price"] == 40
    assert "Blinkit is cheaper at ₹40/kg" in result["recommendation"]["explanation"]
    
def test_quickcommerce_vendor_cheaper():
    result = analyze_purchase_decision(29, 33, 35, quickcommerce_price={"source": "Blinkit", "price": 40, "unit": "kg"})
    assert "Vendor is still cheaper than Blinkit" in result["recommendation"]["explanation"]
