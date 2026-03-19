# app/domain/use_cases/market_use_cases.py
from typing import List, Optional
from datetime import datetime
from app.utils.market_utils import MarketDataProcessor
from app.domain.repositories.market_repository import MarketRepository, MarketDataCache
from app.application.services.market_service import MarketService
from app.domain.entities.market import Asset, MarketType, MarketSummary, CandleStick
from app.application.dto.market_dto import AssetResponse, MarketOverviewResponse, CandleStickDataResponse, CandleData
from app.utils.date_utils import get_last_trading_day

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
        last_trading_date = get_last_trading_day()
        raw_data = await self.market_repository.fetch_raw_market_data(last_trading_date)
        if not raw_data:
            raise ValueError(f"No market data available for {market_type.value}")
        
        sorted_data = raw_data.get("results", [])
        sorted_data.sort(key=lambda x: x.get("v", 0), reverse=True)
        filtered_data = sorted_data[:500]
        
        # Convert raw data to MarketSummary objects for data processor
        market_summaries = []
        for asset_data in filtered_data:
            market_summary = MarketSummary(
                symbol=asset_data.get("T", ""),
                open=asset_data.get("o", 0.0),
                high=asset_data.get("h", 0.0),
                low=asset_data.get("l", 0.0),
                close=asset_data.get("c", 0.0),
                volume=asset_data.get("v", 0),
                change=asset_data.get("c", 0.0) - asset_data.get("o", 0.0),  
                change_percent=(asset_data.get("c", 0.0) - asset_data.get("o", 0.0)) / asset_data.get("o", 0.0) * 100,
                timestamp=datetime.now()
            )
            market_summaries.append(market_summary)
        
        # Create response
        response = MarketOverviewResponse(
            market=market_type,
            total_assets=len(filtered_data),
            status="active",
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            top_gainers=self.data_processor.get_top_gainers(market_summaries),
            top_losers=self.data_processor.get_top_losers(market_summaries),
            most_active=self.data_processor.get_most_active(market_summaries)
        )
        
        # Cache the result
        await self.cache_service.set(cache_key, response.model_dump(), ttl=300)
        
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
            asset_response = AssetResponse(
                id=item.get("id", f"asset_{item.get('symbol', '')}"),
                symbol=item.get("symbol", ""),
                name=item.get("name", ""),
                market=MarketType(item.get("market", "stocks")),
                currency=item.get("currency", "USD"),
                active=item.get("active", True),
                price=item.get("current_price"),
                change=item.get("change"),
                change_percent=item.get("change_percent"),
                volume=item.get("volume"),
                details={}
            )
            results.append(asset_response)
        
        # Cache results
        await self.cache_service.set(cache_key, [r.model_dump() for r in results], ttl=600)
        
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
        
        # Create AssetResponse directly
        response = AssetResponse(
            id=raw_data.get("id", f"asset_{symbol}"),
            symbol=raw_data.get("symbol", symbol),
            name=raw_data.get("name", ""),
            market=MarketType(raw_data.get("market", "stocks")),
            currency=raw_data.get("currency", "USD"),
            active=raw_data.get("active", True),
            price=raw_data.get("current_price"),
            change=raw_data.get("change"),
            change_percent=raw_data.get("change_percent"),
            volume=raw_data.get("volume"),
            details={}
        )
        
        # Cache result
        await self.cache_service.set(cache_key, response.model_dump(), ttl=300)
        
        return response
    
    async def get_assets_list(self, market_type: MarketType, limit: int = 50, offset: int = 0) -> List[AssetResponse]:
        """Get paginated list of assets for a market type"""
        cache_key = f"assets_list_{market_type.value}_{limit}_{offset}"
        
        # Try cache first
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            return [AssetResponse(**item) for item in cached_data]
        

        raw_data = await self.market_repository.fetch_raw_market_data(market_type.value)
        
        # Get the results array from the raw data
        results = raw_data.get("results", [])
        
        assets = []
        for item in results:
            asset_response = AssetResponse(
                id=item.get("id", f"asset_{item.get('symbol', '')}"),
                symbol=item.get("symbol", ""),
                name=item.get("name", ""),
                market=MarketType(item.get("market", "stocks")),
                currency=item.get("currency", "USD"),
                active=item.get("active", True),
                price=item.get("current_price"),
                change=item.get("change"),
                change_percent=item.get("change_percent"),
                volume=item.get("volume"),
                details={}
            )
            assets.append(asset_response)
        print(f"Assets: {assets}")
        return assets
        
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
        await self.cache_service.set(cache_key, response.model_dump(), ttl=300)
        
        return response
