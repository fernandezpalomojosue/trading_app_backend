# app/domain/repositories/market_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class MarketRepository(ABC):
    """Abstract interface for market data repository"""
    @absstractmethod
    async def fetch_raw_market_data(self) -> Dict[str, Any]:
        """Fetch raw market data"""
        pass
    
    @abstractmethod
    async def get_asset_raw_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get raw market data for a specific asset"""
        pass
    
    @abstractmethod
    async def search_assets(self, query: str, market_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for assets by query"""
        pass
    
    @abstractmethod
    async def get_candlestick_data(
        self, 
        symbol: str, 
        timespan: str, 
        multiplier: int, 
        limit: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get candlestick data for charting"""
        pass


class MarketDataCache(ABC):
    """Abstract interface for market data caching"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached data by key"""
        pass
    
    @abstractmethod
    async def set(self, key: str, data: Dict[str, Any], ttl: int = 300) -> None:
        """Set cache data with TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete cached data by key"""
        pass
    
    @abstractmethod
    async def clear_pattern(self, pattern: str) -> None:
        """Clear cache entries matching pattern"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        pass
