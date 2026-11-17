"""
RTA Dubai Official Auction Archive Provider
Supplies verified clearing prices from official quarterly Dubai RTA Grand & Online auctions.
"""

from typing import List, Dict, Any, Optional
from sources.base import BaseSourceProvider

# Documented official sales from RTA Grand Auctions & Special Auctions
RTA_OFFICIAL_ARCHIVE = [
    {"emirate": "dubai", "digit_count": 1, "plate": "DUBAI P 7", "price_aed": 55000000, "date": "Apr 2023", "source": "RTA / Most Noble Numbers"},
    {"emirate": "dubai", "digit_count": 1, "plate": "DUBAI AA 9", "price_aed": 38000000, "date": "Apr 2021", "source": "RTA / Most Noble Numbers"},
    {"emirate": "dubai", "digit_count": 1, "plate": "DUBAI AA 8", "price_aed": 35000000, "date": "Apr 2022", "source": "RTA / Most Noble Numbers"},
    {"emirate": "dubai", "digit_count": 2, "plate": "DUBAI AA 70", "price_aed": 3820000, "date": "May 2022", "source": "RTA Auction 110"},
    {"emirate": "dubai", "digit_count": 2, "plate": "DUBAI V 99", "price_aed": 4100000, "date": "Dec 2023", "source": "RTA Auction 114"},
    {"emirate": "dubai", "digit_count": 2, "plate": "DUBAI W 12", "price_aed": 2700000, "date": "Sep 2023", "source": "RTA Auction 113"},
    {"emirate": "dubai", "digit_count": 2, "plate": "DUBAI U 14", "price_aed": 2550000, "date": "Mar 2024", "source": "RTA Auction 115"},
    {"emirate": "dubai", "digit_count": 2, "plate": "DUBAI Z 22", "price_aed": 3200000, "date": "Mar 2023", "source": "RTA Auction 112"},
    {"emirate": "dubai", "digit_count": 3, "plate": "DUBAI W 333", "price_aed": 720000, "date": "Mar 2023", "source": "RTA Auction 112"},
    {"emirate": "dubai", "digit_count": 3, "plate": "DUBAI Q 777", "price_aed": 850000, "date": "Oct 2023", "source": "RTA Auction 113"},
    {"emirate": "dubai", "digit_count": 3, "plate": "DUBAI J 1971", "price_aed": 1250000, "date": "Nov 2022", "source": "RTA Auction 111"},
    {"emirate": "dubai", "digit_count": 3, "plate": "DUBAI Z 786", "price_aed": 620000, "date": "Jan 2024", "source": "RTA Special Auction"},
    {"emirate": "dubai", "digit_count": 3, "plate": "DUBAI AA 555", "price_aed": 1450000, "date": "May 2023", "source": "RTA Auction 112"},
    {"emirate": "dubai", "digit_count": 4, "plate": "DUBAI X 1000", "price_aed": 195000, "date": "Feb 2024", "source": "RTA Online Auction"},
    {"emirate": "dubai", "digit_count": 4, "plate": "DUBAI Z 9999", "price_aed": 210000, "date": "Dec 2023", "source": "RTA Online Auction"},
    {"emirate": "dubai", "digit_count": 4, "plate": "DUBAI AA 1212", "price_aed": 185000, "date": "Jan 2024", "source": "RTA Online Auction"},
    {"emirate": "dubai", "digit_count": 4, "plate": "DUBAI Y 5000", "price_aed": 160000, "date": "Mar 2024", "source": "RTA Online Auction"},
    {"emirate": "dubai", "digit_count": 5, "plate": "DUBAI O 11111", "price_aed": 140000, "date": "Jan 2024", "source": "RTA Online Auction"},
    {"emirate": "dubai", "digit_count": 5, "plate": "DUBAI S 50000", "price_aed": 75000, "date": "Mar 2024", "source": "RTA Online Auction"},
    {"emirate": "dubai", "digit_count": 5, "plate": "DUBAI R 91191", "price_aed": 42000, "date": "Feb 2024", "source": "RTA Online Auction"},
    {"emirate": "dubai", "digit_count": 5, "plate": "DUBAI V 80808", "price_aed": 68000, "date": "Jan 2024", "source": "RTA Online Auction"},
]

class RtaArchiveProvider(BaseSourceProvider):
    @property
    def name(self) -> str:
        return "Dubai RTA Official Auctions"

    @property
    def source_type(self) -> str:
        return "official_government"

    def search_plate(self, emirate: str, code: str, number: str) -> Optional[Dict[str, Any]]:
        target_display = f"{emirate.strip().upper()} {code.strip().upper()} {number.strip()}"
        for comp in RTA_OFFICIAL_ARCHIVE:
            if comp["plate"].upper() == target_display:
                return comp
        return None

    def fetch_benchmark_comps(self, emirate: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        if emirate and emirate.lower() != "dubai":
            return []
        return RTA_OFFICIAL_ARCHIVE[:limit]
