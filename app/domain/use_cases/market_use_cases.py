# app/domain/use_cases/market_use_cases.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.utils.market_utils import MarketDataProcessor
from app.domain.repositories.market_repository import MarketRepository, MarketDataCache
from app.application.services.market_service import MarketService
from app.domain.entities.market import Asset, MarketType, MarketSummary, CandleStick
from app.application.dto.market_dto import AssetResponse, MarketOverviewResponse, CandleStickDataResponse, CandleData


class MarketUseCases(MarketService):
    """Market business logic use cases"""
    
    def __init__(
        self,
        market_repository: MarketRepository,
        cache_service: MarketDataCache
    ):
        self.market_repository = market_repository
        self.cache_service = cache_service
        self.data_processor = MarketDataProcessor()
    
    async def get_market_overview(self, market_type: MarketType) -> MarketOverviewResponse:
        """Get market overview for specific market type"""
        cache_key = f"market_overview_{market_type.value}"
        
        # Try to get from cache first
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            return MarketOverviewResponse(**cached_data)
        
        # Fetch from repository
        raw_data = await self.market_repository.get_market_summary(market_type.value)
        if not raw_data:
            raise ValueError(f"No market data available for {market_type.value}")
        
        # Process the data
        market_summary = MarketSummary(
            symbol=raw_data.get("symbol", ""),
            open=raw_data.get("open", 0.0),
            high=raw_data.get("high", 0.0),
            low=raw_data.get("low", 0.0),
            close=raw_data.get("close", 0.0),
            volume=raw_data.get("volume", 0),
            change=raw_data.get("change", 0.0),
            change_percent=raw_data.get("change_percent", 0.0)
        )
        
        # Create response
        response = MarketOverviewResponse(
            market_type=market_type,
            summary=market_summary,
            top_gainers=self.data_processor.get_top_gainers([market_summary]),
            top_losers=self.data_processor.get_top_losers([market_summary]),
            most_active=self.data_processor.get_most_active([market_summary])
        )
        
        # Cache the result
        await self.cache_service.set(cache_key, response.dict(), ttl=300)
        
        return response
    
    async def search_assets(self, query: str, market_type: Optional[MarketType] = None) -> List[AssetResponse]:
        """Search for assets by query and market type"""
        cache_key = f"search_{query}_{market_type.value if market_type else 'all'}"
        
        # Try cache first
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            return [AssetResponse(**item) for item in cached_data]
        
        # Search in repository
        raw_results = await self.market_repository.search_assets_raw(query, market_type)
        
        # Convert to AssetResponse
        results = []
        for item in raw_results:
            asset = Asset(
                symbol=item.get("symbol", ""),
                name=item.get("name", ""),
                market_type=MarketType(item.get("market_type", "stocks")),
                current_price=item.get("current_price", 0.0),
                change=item.get("change", 0.0),
                change_percent=item.get("change_percent", 0.0),
                volume=item.get("volume", 0),
                market_cap=item.get("market_cap", 0.0)
            )
            results.append(AssetResponse.from_entity(asset))
        
        # Cache results
        await self.cache_service.set(cache_key, [r.dict() for r in results], ttl=600)
        
        return results
    
    async def get_asset_details(self, symbol: str) -> Optional[AssetResponse]:
        """Get detailed information for a specific asset"""
        cache_key = f"asset_details_{symbol}"
        
        # Try cache first
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            return AssetResponse(**cached_data)
        
        # Fetch from repository
        raw_data = await self.market_repository.get_asset_raw_data(symbol)
        if not raw_data:
            return None
        
        # Create Asset entity
        asset = Asset(
            symbol=raw_data.get("symbol", symbol),
            name=raw_data.get("name", ""),
            market_type=MarketType(raw_data.get("market_type", "stocks")),
            current_price=raw_data.get("current_price", 0.0),
            change=raw_data.get("change", 0.0),
            change_percent=raw_data.get("change_percent", 0.0),
            volume=raw_data.get("volume", 0),
            market_cap=raw_data.get("market_cap", 0.0)
        )
        
        # Create response
        response = AssetResponse.from_entity(asset)
        
        # Cache result
        await self.cache_service.set(cache_key, response.dict(), ttl=300)
        
        return response
    
    async def get_assets_list(self, market_type: MarketType, limit: int = 50, offset: int = 0) -> List[AssetResponse]:
        """Get paginated list of assets for a market type"""
        cache_key = f"assets_list_{market_type.value}_{limit}_{offset}"
        
        # Try cache first
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            return [AssetResponse(**item) for item in cached_data]
        
        # For now, return empty list - this would need to be implemented in the repository
        # based on the specific market data provider API
        results = []
        
        # Cache result
        await self.cache_service.set(cache_key, [r.dict() for r in results], ttl=600)
        
        return results
    
    async def get_candlestick_data(
        self, 
        symbol: str, 
        timespan: str, 
        multiplier: int, 
        limit: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> CandleStickDataResponse:
        """Get candlestick data for charting"""
        cache_key = f"candles_{symbol}_{timespan}_{multiplier}_{limit}_{start_date}_{end_date}"
        
        # Try cache first
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            return CandleStickDataResponse(**cached_data)
        
        # Fetch from repository
        raw_data = await self.market_repository.get_candlestick_data(
            symbol, timespan, multiplier, limit, start_date, end_date
        )
        
        # Convert to CandleStick entities
        candlesticks = []
        for item in raw_data:
            candle = CandleStick(
                timestamp=datetime.fromisoformat(item.get("timestamp", "")),
                open=item.get("open", 0.0),
                high=item.get("high", 0.0),
                low=item.get("low", 0.0),
                close=item.get("close", 0.0),
                volume=item.get("volume", 0)
            )
            candlesticks.append(candle)
        
        # Create response
        response = CandleStickDataResponse(
            symbol=symbol,
            timespan=timespan,
            multiplier=multiplier,
            candlesticks=[
                CandleData(
                    timestamp=c.timestamp.isoformat(),
                    open=c.open,
                    high=c.high,
                    low=c.low,
                    close=c.close,
                    volume=c.volume
                ) for c in candlesticks
            ]
        )
        
        # Cache result
        await self.cache_service.set(cache_key, response.dict(), ttl=300)
        
        return response
