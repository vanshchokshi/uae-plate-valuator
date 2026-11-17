"""
Emirates Auction Provider
Official concessionaire for Abu Dhabi Police, Sharjah Police, and UAE judicial auctions.
"""

from typing import List, Dict, Any, Optional
from sources.base import BaseSourceProvider

# Documented benchmark sales from Emirates Auction
EMIRATES_AUCTION_BENCHMARKS = [
    {"emirate": "abu dhabi", "digit_count": 1, "plate": "ABU DHABI 2", "price_aed": 23300000, "date": "Nov 2021", "source": "Emirates Auction / Abu Dhabi Police"},
    {"emirate": "abu dhabi", "digit_count": 1, "plate": "ABU DHABI 5", "price_aed": 25200000, "date": "Nov 2020", "source": "Emirates Auction / Abu Dhabi Police"},
    {"emirate": "abu dhabi", "digit_count": 2, "plate": "ABU DHABI CAT 1 77", "price_aed": 9150000, "date": "Jun 2023", "source": "Emirates Auction / Abu Dhabi Police"},
    {"emirate": "abu dhabi", "digit_count": 2, "plate": "ABU DHABI CAT 50 11", "price_aed": 4600000, "date": "Dec 2022", "source": "Emirates Auction / Abu Dhabi Police"},
    {"emirate": "abu dhabi", "digit_count": 2, "plate": "ABU DHABI CAT 4 22", "price_aed": 3100000, "date": "Feb 2024", "source": "Emirates Auction / Abu Dhabi Police"},
    {"emirate": "abu dhabi", "digit_count": 3, "plate": "ABU DHABI CAT 1 111", "price_aed": 1100000, "date": "Mar 2023", "source": "Emirates Auction / Abu Dhabi Police"},
    {"emirate": "abu dhabi", "digit_count": 3, "plate": "ABU DHABI CAT 4 500", "price_aed": 340000, "date": "Oct 2023", "source": "Emirates Auction / Abu Dhabi Police"},
    {"emirate": "abu dhabi", "digit_count": 3, "plate": "ABU DHABI CAT 50 999", "price_aed": 780000, "date": "Dec 2023", "source": "Emirates Auction / Abu Dhabi Police"},
    {"emirate": "abu dhabi", "digit_count": 4, "plate": "ABU DHABI CAT 50 7777", "price_aed": 260000, "date": "Nov 2023", "source": "Emirates Auction / Abu Dhabi Police"},
    {"emirate": "abu dhabi", "digit_count": 4, "plate": "ABU DHABI CAT 1 1234", "price_aed": 180000, "date": "Jan 2024", "source": "Emirates Auction / Abu Dhabi Police"},
    {"emirate": "abu dhabi", "digit_count": 4, "plate": "ABU DHABI CAT 4 8080", "price_aed": 95000, "date": "Feb 2024", "source": "Emirates Auction / Abu Dhabi Police"},
    {"emirate": "abu dhabi", "digit_count": 5, "plate": "ABU DHABI CAT 50 55555", "price_aed": 165000, "date": "May 2023", "source": "Emirates Auction / Abu Dhabi Police"},
    {"emirate": "abu dhabi", "digit_count": 5, "plate": "ABU DHABI CAT 1 98989", "price_aed": 92000, "date": "Feb 2024", "source": "Emirates Auction / Abu Dhabi Police"},
    {"emirate": "abu dhabi", "digit_count": 5, "plate": "ABU DHABI CAT 4 10000", "price_aed": 85000, "date": "Dec 2023", "source": "Emirates Auction / Abu Dhabi Police"},
    {"emirate": "sharjah", "digit_count": 2, "plate": "SHARJAH 12", "price_aed": 1850000, "date": "Oct 2023", "source": "Emirates Auction / Sharjah Police"},
    {"emirate": "sharjah", "digit_count": 3, "plate": "SHARJAH 333", "price_aed": 420000, "date": "Dec 2023", "source": "Emirates Auction / Sharjah Police"},
]

class EmiratesAuctionProvider(BaseSourceProvider):
    @property
    def name(self) -> str:
        return "Emirates Auction (Gov Concessionaire)"

    @property
    def source_type(self) -> str:
        return "concessionaire"

    def search_plate(self, emirate: str, code: str, number: str) -> Optional[Dict[str, Any]]:
        target_display = f"{emirate.strip().upper()} {code.strip().upper()} {number.strip()}"
        for comp in EMIRATES_AUCTION_BENCHMARKS:
            if comp["plate"].upper() == target_display:
                return comp
        return None

    def fetch_benchmark_comps(self, emirate: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        if not emirate:
            return EMIRATES_AUCTION_BENCHMARKS[:limit]
        return [c for c in EMIRATES_AUCTION_BENCHMARKS if c["emirate"].lower() == emirate.lower()][:limit]
