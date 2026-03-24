# app/domain/use_cases/market_use_cases.py
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.domain.use_cases.portfolio_use_cases import PortfolioRepository
from app.utils.market_utils import MarketDataProcessor
from app.domain.repositories.market_repository import MarketRepository, MarketDataCache
from app.application.services.market_service import MarketService
from app.domain.entities.portfolio import PortfolioHolding
from app.domain.entities.market import Asset, MarketType, MarketSummary, CandleStick
from app.application.dto.market_dto import AssetResponse, MarketOverviewResponse, CandleStickDataResponse, CandleData
from app.utils.date_utils import get_last_trading_day

class MarketUseCases(MarketService):
    """Market business logic use cases"""
    
    def __init__(
        self,
        market_repository: MarketRepository,
        cache_service: MarketDataCache,
        portfolio_repository: PortfolioRepository
    ):
        self.market_repository = market_repository
        self.cache_service = cache_service
        self.data_processor = MarketDataProcessor()
        self.portfolio_repository = portfolio_repository
    
    def _sort_by_volume(self, raw_data: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """Sort raw market data by volume descending and apply limit
        
        Args:
            raw_data: Dictionary with 'results' key containing list of assets
            limit: Maximum number of results to return
            
        Returns:
            List of asset dictionaries sorted by volume (highest first)
        """
        results = raw_data.get("results", [])
        
        # Sort by volume (v) descending - handle missing/None values
        sorted_results = sorted(
            results, 
            key=lambda x: x.get("v") or 0, 
            reverse=True
        )
        
        return sorted_results[:limit]
    
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
        
        filtered_data = self._sort_by_volume(raw_data, limit=500)
        
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
    
    async def get_asset_details(self, current_user_id: str, symbol: str) -> Optional[Asset]:
        """Get detailed asset information combining market data and ticker details - DOMAIN ORCHESTRATION"""
        cache_key = f"asset_details_{symbol}"
    
        # Try cache first
        cached_asset = await self.cache_service.get(cache_key)
        if cached_asset:
            return cached_asset
    
        try:
            # 1. Get OHLCV data from last trading day using aggregates endpoint
            last_trading_day = get_last_trading_day()
            
            ohlcv_data = await self.market_repository.fetch_candlestick_data(
                symbol, "day", 1, 1, last_trading_day, last_trading_day
            )
            
            # 2. Get company information from reference endpoint
            ticker_info = await self.market_repository.fetch_ticker_details(symbol)
            
            # 3. Combine both data sources
            combined_data = {}
            
            # Add OHLCV data (market_data) - fetch_candlestick_data returns a list directly
            if ohlcv_data and len(ohlcv_data) > 0:
                latest_data = ohlcv_data[0]  # Get the most recent day

                is_holding = await self.portfolio_repository.is_a_holding(current_user_id, symbol)
                
                if is_holding:
                    holding = await self.portfolio_repository.get_holding_by_symbol(current_user_id, symbol)
                    holding.current_price = latest_data.get("c")
                    holding.total_value = holding.quantity * holding.current_price
                    holding.unrealized_pnl = holding.total_value - (holding.quantity * holding.average_price)
                    holding.pnl_percentage = (holding.unrealized_pnl / (holding.quantity * holding.average_price) * 100) if (holding.quantity * holding.average_price) > 0 else 0.0

                    await self.portfolio_repository.update_holding(holding)

                combined_data.update({
                    "price": latest_data.get("c"),
                    "change": latest_data.get("c", 0) - latest_data.get("o", 0),
                    "change_percent": ((latest_data.get("c", 0) - latest_data.get("o", 0)) / latest_data.get("o", 1)) * 100,
                    "volume": latest_data.get("v"),
                    "open": latest_data.get("o"),
                    "high": latest_data.get("h"),
                    "low": latest_data.get("l"),
                    "vwap": latest_data.get("vw")
                })
            
            # Add company information from reference endpoint
            if ticker_info and ticker_info.get("status") == "OK" and ticker_info.get("results"):
                company_data = ticker_info["results"]
                combined_data.update({
                    "name": company_data.get("name"),
                    "description": company_data.get("description"),
                    "market_cap": company_data.get("market_cap"),
                    "primary_exchange": company_data.get("primary_exchange"),
                    "homepage_url": company_data.get("homepage_url"),
                    "currency_name": company_data.get("currency_name"),
                    "active": company_data.get("active", True)
                })
            
            # 4. Convert to entity
            asset = self._convert_raw_to_asset({
                "ticker": symbol,
                **combined_data
            }) if combined_data else None
            
            # 5. Convert to DTO for API response
            if asset:
                asset_response = AssetResponse(
                    id=asset.id,
                    symbol=asset.symbol,
                    name=asset.name,
                    market=asset.market,
                    currency=asset.currency,
                    active=asset.active,
                    price=asset.price,
                    change=asset.change,
                    change_percent=asset.change_percent,
                    volume=asset.volume,
                    details=asset.details
                )
                
                # 6. Cache and return
                await self.cache_service.set(cache_key, asset_response.model_dump(), ttl=60)
                return asset_response
            
            return None
            
        except Exception as e:
            # Log error but don't crash
            print(f"Error fetching asset details for {symbol}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _convert_raw_to_asset(self, raw_data: Dict[str, Any]) -> Asset:
        """Convert raw market data to Asset entity"""
        return Asset(
            id=raw_data.get("ticker", f"asset_{raw_data.get('ticker', '')}"),
            symbol=raw_data.get("ticker", ""),
            name=raw_data.get("name", ""),
            market=MarketType(raw_data.get("market", "stocks")),
            currency=raw_data.get("currency_name", "USD"),
            price=raw_data.get("price"),
            change=raw_data.get("change", 0.0),
            change_percent=raw_data.get("change_percent", 0.0),
            volume=raw_data.get("volume", 0),
            active=raw_data.get("active", True),
            details={
                "description": raw_data.get("description", ""),
                "market_cap": raw_data.get("market_cap"),
                "primary_exchange": raw_data.get("primary_exchange"),
                "homepage_url": raw_data.get("homepage_url"),
                "open": raw_data.get("open"),
                "high": raw_data.get("high"),
                "low": raw_data.get("low"),
                "vwap": raw_data.get("vwap")
            }
        )
    
    async def get_assets_list(self, market_type: MarketType, limit: int = 50, offset: int = 0) -> List[AssetResponse]:
        """Get paginated list of assets for a market type"""
        cache_key = f"assets_list_{market_type.value}_{limit}_{offset}"
        
        # Try cache first
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            return [AssetResponse(**item) for item in cached_data]
        
        last_trading_date = get_last_trading_day()
        
        raw_data = await self.market_repository.fetch_raw_market_data(last_trading_date)
        
        # Sort by volume and apply limit
        raw_data = self._sort_by_volume(raw_data, limit=500)
        
        # Apply pagination
        paginated_results = raw_data[offset:offset + limit]
        
        assets = []
        for item in paginated_results:
            asset_response = AssetResponse(
                id=item.get("id", f"asset_{item.get('symbol', '')}"),
                symbol=item.get("T", ""),
                name=item.get("name", ""),
                market=MarketType(item.get("market", "stocks")),
                currency=item.get("currency", "USD"),
                active=item.get("active", True),
                price=item.get("c"),
                change=item.get("c", 0.0) - item.get("o", 0.0),  
                change_percent=(item.get("c", 0.0) - item.get("o", 0.0)) / item.get("o", 0.0) * 100,
                volume=item.get("v"),
                details={}
            )
            assets.append(asset_response)
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
        
        # Fetch from repository (correct parameter order)
        raw_data = await self.market_repository.fetch_candlestick_data(
            symbol, timespan, multiplier, limit, start_date, end_date
        )
        
        # Convert API response directly to DTO format (t, o, h, l, c, v)
        results = []
        for item in raw_data:
            results.append(CandleData(
                t=item.get("t", 0),
                o=item.get("o", 0.0),
                h=item.get("h", 0.0),
                l=item.get("l", 0.0),
                c=item.get("c", 0.0),
                v=int(item.get("v", 0))  # Convert float volume to int
            ))
        
        # Create response - DTO expects 'results' field
        response = CandleStickDataResponse(results=results)
        
        # Cache result
        await self.cache_service.set(cache_key, response.model_dump(), ttl=300)
        
        return response
