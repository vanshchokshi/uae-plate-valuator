"""
Multi-Source Market Data Providers for UAE Plate Valuator
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseSourceProvider(ABC):
    """Abstract base class for plate market data providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name, e.g. 'Emirates Auction', 'RTA Dubai', 'Dubizzle Marketplace'."""
        pass

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Category: 'official_government', 'concessionaire', or 'dealer_marketplace'."""
        pass

    @abstractmethod
    def search_plate(self, emirate: str, code: str, number: str) -> Optional[Dict[str, Any]]:
        """Search this provider for a specific plate."""
        pass

    @abstractmethod
    def fetch_benchmark_comps(self, emirate: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch benchmark comparable records from this provider."""
        pass
