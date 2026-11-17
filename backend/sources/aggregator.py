"""
Multi-Source Aggregator for UAE License Plates
Orchestrates lookups across official government auctions, authorized concessionaires,
and verified dealer secondary marketplaces.
"""

from typing import List, Dict, Any, Optional

from sources.rta_archive import RtaArchiveProvider
from sources.emirates_auction import EmiratesAuctionProvider
from sources.dealer_marketplace import DealerMarketplaceProvider

class MultiSourceAggregator:
    def __init__(self):
        self.providers = [
            RtaArchiveProvider(),
            EmiratesAuctionProvider(),
            DealerMarketplaceProvider(),
        ]

    def list_sources(self) -> List[Dict[str, str]]:
        """List all active market data sources and categories."""
        return [
            {"name": p.name, "type": p.source_type}
            for p in self.providers
        ]

    def search_all_sources(self, emirate: str, code: str, number: str) -> Optional[Dict[str, Any]]:
        """
        Cross-reference across all providers for an exact historical or secondary comp.
        Priority:
        1. Official Government Auctions (RTA Dubai / Most Noble Numbers)
        2. Authorized Concessionaires (Emirates Auction / Abu Dhabi Police)
        3. Verified Dealer Marketplaces (Alain Class / Pearl Motors / Dubizzle)
        """
        for provider in self.providers:
            match = provider.search_plate(emirate, code, number)
            if match:
                return {
                    **match,
                    "provider_name": provider.name,
                    "provider_type": provider.source_type
                }
        return None

    def get_all_benchmark_comps(self, emirate: Optional[str] = None, limit: int = 60) -> List[Dict[str, Any]]:
        """Collect and deduplicate benchmark records from all providers."""
        all_comps: List[Dict[str, Any]] = []
        seen = set()

        for provider in self.providers:
            comps = provider.fetch_benchmark_comps(emirate=emirate, limit=limit)
            for c in comps:
                key = c["plate"].upper()
                if key not in seen:
                    seen.add(key)
                    all_comps.append(c)

        return all_comps[:limit]

# Global singleton aggregator
multi_source_aggregator = MultiSourceAggregator()
