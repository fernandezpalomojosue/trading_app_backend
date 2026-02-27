"""
Utility functions for market-related operations
"""
from typing import List, Dict, Any, Optional

from app.domain.entities.market import MarketSummary


class MarketDataProcessor:
    """Utility class for market data processing"""
    
    @staticmethod
    def get_top_gainers(data: List[MarketSummary], limit: int = 10) -> List[MarketSummary]:
        return sorted(
            [item for item in data if item.change_percent > 0],
            key=lambda x: x.change_percent,
            reverse=True
        )[:limit]
    
    @staticmethod
    def get_top_losers(data: List[MarketSummary], limit: int = 10) -> List[MarketSummary]:
        return sorted(
            [item for item in data if item.change_percent < 0],
            key=lambda x: x.change_percent
        )[:limit]
    
    @staticmethod
    def get_most_active(data: List[MarketSummary], limit: int = 10) -> List[MarketSummary]:
        return sorted(
            data,
            key=lambda x: x.volume,
            reverse=True
        )[:limit]
    
    @staticmethod
    def calculate_total_assets(data: List[MarketSummary]) -> int:
        return len(set(item.symbol for item in data))

