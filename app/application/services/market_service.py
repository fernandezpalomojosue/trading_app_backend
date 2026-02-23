# app/application/services/market_service.py
from typing import List, Optional, Dict, Any

from app.domain.entities.market import Asset, MarketType, MarketSummary, CandleStick
from app.domain.use_cases.market_use_cases import MarketRepository, MarketDataCache, MarketUseCases
from app.application.dto.market_dto import AssetResponse, MarketOverviewResponse, CandleStickDataResponse


class MarketService:
    """Application service for market operations"""
    
    def __init__(self, market_use_cases: MarketUseCases):
        self.market_use_cases = market_use_cases
    
    async def get_market_overview(self, market_type: MarketType) -> MarketOverviewResponse:
        """Get market overview"""
        return await self.market_use_cases.get_market_summary(market_type)
    
    async def search_assets(self, query: str, market_type: Optional[MarketType] = None) -> List[AssetResponse]:
        """Search for assets"""
        return await self.market_use_cases.search_assets(query, market_type)
    
    async def get_asset_details(self, symbol: str) -> Optional[AssetResponse]:
        """Get asset details"""
        return await self.market_use_cases.get_asset_details(symbol)
    
    async def get_assets_list(self, market_type: MarketType, limit: int = 50, offset: int = 0) -> List[AssetResponse]:
        """Get assets list from raw market data"""
        return await self.market_use_cases.get_assets_list(market_type, limit, offset)
    
    async def get_candlestick_data(self, symbol: str, timespan: str = "day", multiplier: int = 1, limit: int = 100, start_date: str = None, end_date: str = None) -> CandleStickDataResponse:
        """Get candlestick data for charting"""
        return await self.market_use_cases.get_candlestick_data(symbol, timespan, multiplier, limit, start_date, end_date)
