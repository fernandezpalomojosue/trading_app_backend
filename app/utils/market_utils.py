"""
Utility functions for market-related operations - Pure business logic
"""
from typing import List, Dict, Any, Optional

from app.domain.entities.market import MarketSummary


class MarketDataProcessor:
    """Pure utility class for market data processing - no infrastructure dependencies"""
    
    @staticmethod
    def get_top_gainers(data: List[MarketSummary], limit: int = 10) -> List[MarketSummary]:
        """Get top gainers from market data"""
        return sorted(
            [item for item in data if item.change_percent > 0],
            key=lambda x: x.change_percent,
            reverse=True
        )[:limit]
    
    @staticmethod
    def get_top_losers(data: List[MarketSummary], limit: int = 10) -> List[MarketSummary]:
        """Get top losers from market data"""
        return sorted(
            [item for item in data if item.change_percent < 0],
            key=lambda x: x.change_percent
        )[:limit]
    
    @staticmethod
    def get_most_active(data: List[MarketSummary], limit: int = 10) -> List[MarketSummary]:
        """Get most active stocks by volume"""
        return sorted(
            data,
            key=lambda x: x.volume,
            reverse=True
        )[:limit]
    
    @staticmethod
    def calculate_total_assets(data: List[MarketSummary]) -> int:
        """Calculate total number of unique assets"""
        return len(set(item.symbol for item in data))

