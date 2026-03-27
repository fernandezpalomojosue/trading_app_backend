# app/application/services/market_service.py
from typing import List, Optional
from abc import ABC, abstractmethod
from uuid import UUID
from app.domain.entities.user import UserEntity
from app.domain.entities.market import MarketType
from app.application.dto.market_dto import (
    AssetResponse, MarketOverviewResponse, CandleStickDataResponse,
    FavoriteStockResponse, FavoriteStockListResponse
)


class MarketService(ABC):
    """Application interface for market operations"""
    
    @abstractmethod
    async def get_market_overview(self, market_type: MarketType) -> MarketOverviewResponse:
        """Get market overview for specific market type"""
        pass
    
    @abstractmethod
    async def search_assets(self, query: str, market_type: Optional[MarketType] = None) -> List[AssetResponse]:
        """Search for assets by query and market type"""
        pass
    
    @abstractmethod
    async def get_asset_details(self, current_user: UserEntity, symbol: str) -> Optional[AssetResponse]:
        """Get detailed information for a specific asset"""
        pass
    
    @abstractmethod
    async def get_assets_list(self, market_type: MarketType, limit: int = 50, offset: int = 0) -> List[AssetResponse]:
        """Get paginated list of assets for a market type"""
        pass
    
    @abstractmethod
    async def get_candlestick_data(self, symbol: str, timespan: str = "day", multiplier: int = 1, limit: int = 100, start_date: str = None, end_date: str = None) -> CandleStickDataResponse:
        """Get candlestick data for a specific asset"""
        pass
    
    @abstractmethod
    async def add_favorite_stock(self, user_id: UUID, symbol: str) -> FavoriteStockResponse:
        """Add a stock to user's favorites"""
        pass
    
    @abstractmethod
    async def remove_favorite_stock(self, user_id: UUID, symbol: str) -> FavoriteStockResponse:
        """Remove a stock from user's favorites"""
        pass
    
    @abstractmethod
    async def get_user_favorite_stocks(self, user_id: UUID) -> List[FavoriteStockResponse]:
        """Get user's favorite stocks"""
        pass
