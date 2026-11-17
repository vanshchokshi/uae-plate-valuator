import pytest
from valuation import valuate, extract_patterns, calculate_code_multiplier, calculate_base_value

def test_single_digit_base():
    result = valuate("dubai", "A", "7")
    assert result["digit_count"] == 1
    assert result["fair_market_value_aed"] > 10_000_000
    assert result["liquidation_value_aed"] < result["fair_market_value_aed"]
    assert result["dealer_ask_aed"] > result["fair_market_value_aed"]

def test_palindrome_radar_detection():
    patterns, mult = extract_patterns("12321")
    assert "Radar / Palindrome" in patterns
    assert mult > 2.0

def test_cultural_786():
    patterns, mult = extract_patterns("786")
    assert "Cultural Premium (786)" in patterns
    assert mult >= 3.5

def test_national_1971():
    patterns, mult = extract_patterns("1971")
    assert "National Year (1971)" in patterns
    assert mult >= 4.0

def test_super_solid_repeating():
    patterns, mult = extract_patterns("77777")
    assert any("Super Solid" in p for p in patterns)
    assert mult >= 20.0

def test_automotive_badge_911():
    patterns, mult = extract_patterns("911")
    assert any("Automotive Model Match" in p for p in patterns)

def test_repeating_pair():
    patterns, mult = extract_patterns("1212")
    assert "Repeating Pair (ABAB)" in patterns

def test_code_multipliers():
    # Single letter
    mult_a, code_a = calculate_code_multiplier("dubai", "A")
    assert mult_a == 1.30

    # Double identical letter
    mult_aa, code_aa = calculate_code_multiplier("dubai", "AA")
    assert mult_aa == 1.45

    # Abu Dhabi Category 1
    mult_cat1, code_cat1 = calculate_code_multiplier("abu dhabi", "1")
    assert mult_cat1 == 1.85
    assert code_cat1 == "CAT 1"

def test_exact_comp_precedence():
    result = valuate("dubai", "P", "7", exact_comp_price=55_000_000)
    assert result["fair_market_value_aed"] == 55_000_000
    assert "Exact Auction Comp Verified" in result["patterns"]
    assert result["confidence_score"] == 0.99
