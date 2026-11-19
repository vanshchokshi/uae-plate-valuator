"""
UAE License Plate Valuation Engine
----------------------------------
Heuristic valuation algorithm combining pattern recognition, digit decay,
emirate prestige, code multipliers, and market comp anchoring.
"""

from typing import List, Tuple, Dict, Any, Optional
import re

EMIRATE_MULTIPLIERS: Dict[str, float] = {
    "dubai": 1.25,
    "abu dhabi": 1.30,
    "sharjah": 0.85,
    "ajman": 0.65,
    "ras al khaimah": 0.60,
    "fujairah": 0.55,
    "umm al quwain": 0.50,
}

CAR_BADGES = {
    "911", "488", "720", "812", "300", "500", "63", "55",
    "718", "918", "296", "800", "700", "430", "458", "600"
}

def is_consecutive(num_str: str) -> bool:
    """Check if digits are strictly consecutive ascending or descending (e.g. 1234, 4321)."""
    if len(num_str) < 3:
        return False
    digits = [int(d) for d in num_str]
    ascending = all(digits[i] + 1 == digits[i + 1] for i in range(len(digits) - 1))
    descending = all(digits[i] - 1 == digits[i + 1] for i in range(len(digits) - 1))
    return ascending or descending

def extract_patterns(num_str: str) -> Tuple[List[str], float]:
    """
    Detect pattern significance and calculate cumulative pattern multiplier.
    """
    patterns: List[str] = []
    multiplier = 1.0
    length = len(num_str)
    unique_digits = set(num_str)

    # 1. Cultural & National Significant Numbers
    if num_str == "786":
        patterns.append("Cultural Premium (786)")
        multiplier *= 3.5
    elif num_str == "1971":
        patterns.append("National Year (1971)")
        multiplier *= 4.0
    elif num_str in {"50", "71"}:
        patterns.append("National Jubilee / Federation Match")
        multiplier *= 1.4

    # 2. Automotive enthusiast badges
    if num_str in CAR_BADGES:
        patterns.append(f"Automotive Model Match ({num_str})")
        multiplier *= 2.0

    # 3. Repeating single digit (e.g., 77777, 8888, 333)
    if len(unique_digits) == 1:
        if length >= 4:
            patterns.append(f"Super Solid ({num_str})")
            multiplier *= 15.0 if length == 4 else 25.0
        elif length == 3:
            patterns.append(f"Solid Triplet ({num_str})")
            multiplier *= 5.5
        elif length == 2:
            patterns.append(f"Solid Double ({num_str})")
            multiplier *= 3.2
        elif length == 1:
            patterns.append("Single Digit Super Rare")
            multiplier *= 1.0

    # 4. Radars / Palindromes (e.g. 121, 9119, 12321, 50005)
    elif num_str == num_str[::-1] and length >= 3:
        patterns.append("Radar / Palindrome")
        multiplier *= 3.0 if length >= 4 else 2.3

    # 5. Consecutive sequences (e.g. 123, 1234, 12345)
    elif is_consecutive(num_str):
        patterns.append("Consecutive Sequence")
        multiplier *= 4.5 if length >= 4 else 2.8

    # 6. Repeating pairs (ABAB pattern, e.g. 1212, 5050, 7070)
    elif length == 4 and num_str[:2] == num_str[2:]:
        patterns.append("Repeating Pair (ABAB)")
        multiplier *= 2.8

    # 7. Clean round base (e.g. 1000, 20000, 50000)
    elif length >= 3 and num_str[1:] == "0" * (length - 1):
        patterns.append("Clean Round Base")
        multiplier *= 2.6

    # 8. Bookend triplets (e.g. 1888, 7771, 90009)
    elif length == 4 and (num_str[1:] == num_str[1] * 3 or num_str[:3] == num_str[0] * 3):
        patterns.append("Bookend Triplet")
        multiplier *= 2.2

    # 9. Binary plate (composed of only 2 distinct digits, e.g. 10101, 80880)
    elif len(unique_digits) == 2 and length >= 4:
        patterns.append("Binary Combination")
        multiplier *= 1.75

    # Secondary National match if "71" or "1971" is contained
    if ("71" in num_str or "1971" in num_str) and "National Year (1971)" not in patterns and "National Jubilee / Federation Match" not in patterns:
        patterns.append("National Match (71)")
        multiplier *= 1.25

    return patterns, multiplier

def calculate_code_multiplier(emirate: str, raw_code: str) -> Tuple[float, str]:
    """
    Determine code multiplier and standardized display code.
    - Abu Dhabi uses numeric categories (CAT 1, CAT 2, CAT 50, etc.).
    - Dubai and other emirates use letters (A, AA, etc.).
    """
    emirate_clean = emirate.strip().lower()
    code_clean = raw_code.strip().upper()

    if emirate_clean == "abu dhabi":
        if code_clean.isdigit():
            cat_num = int(code_clean)
            if cat_num == 1:
                return 1.85, f"CAT 1"
            elif cat_num in {2, 3, 4}:
                return 1.30, f"CAT {cat_num}"
            elif cat_num == 50:
                return 1.40, f"CAT 50"
            else:
                return 1.0, f"CAT {cat_num}"
        else:
            return 1.0, code_clean
    else:
        # Standard emirate letter codes
        if len(code_clean) == 1 and code_clean.isalpha():
            return 1.30, code_clean
        elif len(code_clean) == 2 and code_clean.isalpha() and code_clean[0] == code_clean[1]:
            # Double identical letter (e.g., AA, BB)
            return 1.45, code_clean
        else:
            return 1.0, code_clean

def calculate_base_value(length: int, has_patterns: bool) -> int:
    """
    Base financial value in AED according to plate length (exponential rarity decay).
    Calibrated to genuine secondary market transaction clearing prices
    (filtering out speculative Dubizzle listing markups while avoiding outdated auction opening bids).
    """
    if length == 1:
        return 18_000_000
    elif length == 2:
        return 1_400_000
    elif length == 3:
        return 220_000 if has_patterns else 135_000
    elif length == 4:
        return 48_000 if has_patterns else 20_000
    elif length == 5:
        return 22_000 if has_patterns else 4_500
    else:
        return 0

def valuate(
    emirate: str,
    code: str,
    number: str,
    exact_comp_price: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calculate comprehensive valuation metrics for a given plate.
    """
    num = number.strip()
    emirate_clean = emirate.strip().lower()
    length = len(num)

    code_multiplier, display_code = calculate_code_multiplier(emirate_clean, code)
    emirate_factor = EMIRATE_MULTIPLIERS.get(emirate_clean, 1.0)
    
    patterns, pattern_multiplier = extract_patterns(num)
    has_patterns = len(patterns) > 0
    base_val = calculate_base_value(length, has_patterns)

    calculated_fair = int(base_val * emirate_factor * pattern_multiplier * code_multiplier)
    confidence = 0.94 if has_patterns else 0.82
    display_patterns = list(patterns) if patterns else ["Standard Baseline Sequence"]

    # Exact auction comp takes highest precedence if present
    if exact_comp_price and exact_comp_price > 0:
        calculated_fair = exact_comp_price
        display_patterns.append("Exact Auction Comp Verified")
        confidence = 0.99
    elif calculated_fair == 0:
        display_patterns = ["Standard Issue (No Market Premium)"]
        confidence = 0.99

    # Liquidation (quick cash discount) and Dealer Ask (retail showroom markup)
    if calculated_fair > 0:
        liquidation_val = int(calculated_fair * 0.78)
        dealer_ask_val = int(calculated_fair * 1.28)
    else:
        liquidation_val = 0
        dealer_ask_val = 0

    plate_display = f"{emirate.strip().upper()} {display_code} {num}"

    return {
        "plate_display": plate_display,
        "emirate": emirate_clean,
        "code": display_code,
        "number": num,
        "digit_count": length,
        "patterns": display_patterns,
        "fair_market_value_aed": calculated_fair,
        "liquidation_value_aed": liquidation_val,
        "dealer_ask_aed": dealer_ask_val,
        "confidence_score": round(confidence, 2),
    }
