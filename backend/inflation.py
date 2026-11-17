"""
Market Appreciation & Inflation Indexing Engine for UAE License Plates
Calculates compound capital appreciation on historical auction comps up to the current market year (2026).
"""

import re
from typing import Tuple, Dict, Any, Optional

CURRENT_MARKET_YEAR = 2026

# Annualized appreciation rates based on historical RTA and Emirates Auction repeat sales (2018-2026)
ANNUAL_APPRECIATION_RATES = {
    1: 0.085,  # 1-digit plates: +8.5% CAGR (Ultra-exclusive capital concentration)
    2: 0.080,  # 2-digit plates: +8.0% CAGR
    3: 0.060,  # 3-digit plates: +6.0% CAGR
    4: 0.045,  # 4-digit plates: +4.5% CAGR (pattern-weighted)
    5: 0.030,  # 5-digit plates: +3.0% CAGR (baseline inflation tracking)
}

def parse_year_from_date(date_str: str) -> Optional[int]:
    """Extract 4-digit year from date string (e.g. 'Apr 2021', '2023', 'May 2022')."""
    if not date_str:
        return None
    match = re.search(r'\b(20\d{2})\b', date_str)
    if match:
        return int(match.group(1))
    return None

def adjust_comp_for_appreciation(
    price_aed: int,
    date_str: str,
    digit_count: int
) -> Dict[str, Any]:
    """
    Adjust historical transaction price to current 2026 market values using compound appreciation.
    
    Returns:
        dict containing:
            - original_price_aed
            - adjusted_price_aed
            - appreciation_pct
            - elapsed_years
            - sale_year
    """
    sale_year = parse_year_from_date(date_str)
    
    if not sale_year or sale_year >= CURRENT_MARKET_YEAR:
        return {
            "original_price_aed": price_aed,
            "adjusted_price_aed": price_aed,
            "appreciation_pct": 0.0,
            "elapsed_years": 0,
            "sale_year": CURRENT_MARKET_YEAR
        }
    
    elapsed_years = CURRENT_MARKET_YEAR - sale_year
    rate = ANNUAL_APPRECIATION_RATES.get(digit_count, 0.035)
    
    # Compound annual growth calculation: Price * (1 + r)^t
    multiplier = (1.0 + rate) ** elapsed_years
    adjusted_price = int(round(price_aed * multiplier))
    appreciation_pct = round((multiplier - 1.0) * 100, 1)
    
    return {
        "original_price_aed": price_aed,
        "adjusted_price_aed": adjusted_price,
        "appreciation_pct": appreciation_pct,
        "elapsed_years": elapsed_years,
        "sale_year": sale_year
    }
