# app/domain/use_cases/market_use_cases.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.utils.market_utils import MarketDataProcessor
from app.domain.entities.market import Asset, MarketType, MarketSummary, CandleStick
from app.application.dto.market_dto import AssetResponse, MarketOverviewResponse, CandleStickDataResponse, CandleData


class MarketRepository(ABC):
    """Abstract interface for market data repository"""
    
    @abstractmethod
    async def get_asset_raw_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def search_assets_raw(self, query: str, market_type: Optional[MarketType] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def fetch_raw_market_data(self, date: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def fetch_symbol_data(self, symbol: str, date: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def fetch_candlestick_data(self, symbol: str, multiplier: int, timespan: str, from_date: str, to_date: str, limit: int = 100) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_last_trading_date(self) -> str:
        pass

    @abstractmethod
    async def fetch_ticker_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        pass

class MarketDataCache(ABC):
    """Abstract cache service for market data"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        pass
    
    @abstractmethod
    async def clear_pattern(self, pattern: str) -> None:
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        pass


class MarketUseCases:
    """Market business logic use cases"""
    
    def __init__(
        self,
        market_repository: MarketRepository,
        cache_service: MarketDataCache
    ):
        self.market_repository = market_repository
        self.cache_service = cache_service
    
    async def get_market_summary(self, market_type: MarketType) -> MarketOverviewResponse:
        cache_key = f"market_summary_{market_type.value}"
    
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            return cached_data
    
        filtered_raw_data = await self._get_and_filter_market_data(500)
    
        entities = []
        for item in filtered_raw_data:
            entity = self._convert_raw_to_entity(item)
            if entity:
                entities.append(entity)
        
        gainers = MarketDataProcessor.get_top_gainers(entities)
        losers = MarketDataProcessor.get_top_losers(entities)
        active = MarketDataProcessor.get_most_active(entities)
        total_assets = MarketDataProcessor.calculate_total_assets(entities)
    
        overview_response = MarketOverviewResponse(
            market=market_type,
            total_assets=total_assets,
            status="active",
            last_updated=datetime.now().isoformat(),
            top_gainers=gainers,
            top_losers=losers,
            most_active=active
        )
    
        await self.cache_service.set(cache_key, overview_response, ttl=300)
    
        return overview_response

    def _convert_raw_to_entity(self, raw_item: Dict[str, Any]) -> Optional[MarketSummary]:
        try:
            if not all(k in raw_item for k in ["T", "c", "o", "v"]):
                return None
            
            open_price = raw_item["o"]
            close_price = raw_item["c"]
        
            change = close_price - open_price
            change_percent = (change / open_price * 100) if open_price != 0 else 0
        
            return MarketSummary(
            symbol=raw_item["T"],
            open=open_price,
            close=close_price,
            high=raw_item.get("h", close_price),
            low=raw_item.get("l", close_price),
            volume=raw_item["v"],
            vwap=raw_item.get("vw"),
            change=round(change, 4),
            change_percent=round(change_percent, 2),
            timestamp=datetime.now()
            )
        except (TypeError, KeyError, ZeroDivisionError):
            return None
    
    async def get_asset_details(self, symbol: str) -> Optional[AssetResponse]:
        cache_key = f"asset_details_{symbol}"
    
        cached_asset = await self.cache_service.get(cache_key)
        if cached_asset:
            return cached_asset
    
        try:
            last_trading_day = await self.market_repository.get_last_trading_date()
            print(f"DEBUG: Last trading day: {last_trading_day}")
            
            ohlcv_data = await self.market_repository.fetch_candlestick_data(
                symbol, 1, "day", last_trading_day, last_trading_day, 1
            )
            print(f"DEBUG: OHLCV data: {ohlcv_data}")
            
            ticker_info = await self.market_repository.fetch_ticker_details(symbol)
            print(f"DEBUG: Ticker info: {ticker_info}")
            
            combined_data = {}
            
            if ohlcv_data and ohlcv_data.get("results"):
                latest_data = ohlcv_data["results"][0]
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
            
            print(f"DEBUG: Combined data: {combined_data}")
            
            if combined_data:
                structured_details = {
                    "market_data": {
                        "price": combined_data.get("price"),
                        "change": combined_data.get("change"),
                        "change_percent": combined_data.get("change_percent"),
                        "volume": combined_data.get("volume"),
                        "open": combined_data.get("open"),
                        "high": combined_data.get("high"),
                        "low": combined_data.get("low"),
                        "vwap": combined_data.get("vwap")
                    },
                    "source": "market_data",
                    "market_cap": combined_data.get("market_cap"),
                    "primary_exchange": combined_data.get("primary_exchange"),
                    "description": combined_data.get("description"),
                    "homepage_url": combined_data.get("homepage_url")
                }
                
                asset_response = AssetResponse(
                    id=symbol,
                    symbol=symbol,
                    name=combined_data.get("name", symbol),
                    market=self._map_market_type(combined_data.get("market", "stocks")),
                    currency=combined_data.get("currency_name", "USD"),
                    active=combined_data.get("active", True),
                    price=combined_data.get("price"),
                    change=combined_data.get("change"),
                    change_percent=combined_data.get("change_percent"),
                    volume=combined_data.get("volume"),
                    details=structured_details
                )
                
                await self.cache_service.set(cache_key, asset_response, ttl=60)
                
                return asset_response
            
            return None
            
        except Exception as e:
            print(f"Error fetching asset details for {symbol}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    async def search_assets(self, query: str, market_type: Optional[MarketType] = None) -> List[AssetResponse]:
        if not query or len(query) < 2:
            return []
    
        raw_results = await self.market_repository.search_assets_raw(query, market_type)
    
        asset_responses = []
        for raw_data in raw_results:
            asset = self._convert_raw_to_asset(raw_data)
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
                asset_responses.append(asset_response)
    
        return asset_responses

    def _convert_raw_to_asset(self, raw_data: Dict[str, Any]) -> Optional[Asset]:
        if not raw_data:
            return None
    
        try:
            return Asset(
                id=raw_data.get("ticker", ""),
                symbol=raw_data.get("ticker", ""),
                name=raw_data.get("name", ""),
                market=self._map_market_type(raw_data.get("market", "")),
                currency=raw_data.get("currency_name", "USD"),
                active=raw_data.get("active", True),
                price=raw_data.get("price"),
                change=raw_data.get("change"),
                change_percent=raw_data.get("change_percent"),
                volume=raw_data.get("volume"),
                details=raw_data
            )
        except Exception:
            return None

    def _map_market_type(self, market_str: str) -> MarketType:
        """Map market string to MarketType enum - DOMAIN LOGIC"""
        market_mapping = {
            "stocks": MarketType.STOCKS,
            "crypto": MarketType.CRYPTO,
            "fx": MarketType.FX,  # Para compatibilidad con Polygon
            "indices": MarketType.INDICES
        }
        return market_mapping.get(market_str.lower(), MarketType.STOCKS)

    async def get_assets_list(self, market_type: MarketType, limit: int = 50, offset: int = 0) -> List[AssetResponse]:
        """Get assets list from raw market data - DOMAIN LOGIC"""
        cache_key = f"assets_list_{market_type.value}_{limit}_{offset}"
        
        # Try cache first
        cached_assets = await self.cache_service.get(cache_key)
        if cached_assets:
            return cached_assets
        
        # 1. Get and filter raw market data
        filtered_raw_data = await self._get_and_filter_market_data()
        
        # 2. Process filtered data using efficient list comprehension
        seen_symbols = set()
        
        def create_asset(item):
            symbol = item.get("T", "")
            if not symbol or symbol in seen_symbols:
                return None
            seen_symbols.add(symbol)
            return self._convert_raw_to_asset_basic(item, market_type)
        
        # List comprehension with filtering - much faster than explicit loop
        all_assets = [
            asset for asset in (create_asset(item) for item in filtered_raw_data)
            if asset is not None
        ]
        
        # 3. Apply pagination using efficient slicing
        paginated_assets = all_assets[offset:offset + limit]
        
        # 4. Convert to AssetResponse DTOs
        asset_responses = [
            AssetResponse(
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
            for asset in paginated_assets
        ]
        
        # 5. Cache the paginated result
        await self.cache_service.set(cache_key, asset_responses, ttl=300)
        
        return asset_responses

    def _convert_raw_to_asset_basic(self, raw_item: Dict[str, Any], market_type: MarketType) -> Optional[Asset]:
        """Convert raw market data to basic Asset entity - DOMAIN LOGIC"""
        try:
            if not all(k in raw_item for k in ["T", "c", "v"]):
                return None
                
            symbol = raw_item["T"]
            close_price = raw_item["c"]
            volume = raw_item["v"]
            
            # Calculate change if we have open price
            change = None
            change_percent = None
            if "o" in raw_item:
                open_price = raw_item["o"]
                change = close_price - open_price
                change_percent = (change / open_price * 100) if open_price > 0 else 0
            
            return Asset(
                id=symbol,
                symbol=symbol,
                name=symbol,  # Basic info from market data
                market=market_type,
                currency="USD",
                active=True,
                price=close_price,
                change=round(change, 4) if change is not None else None,
                change_percent=round(change_percent, 2) if change_percent is not None else None,
                volume=int(volume),
                details={
                    "source": "market_raw_data",
                    "open": raw_item.get("o"),
                    "high": raw_item.get("h"),
                    "low": raw_item.get("l"),
                    "vwap": raw_item.get("vw")
                }
            )
        except (TypeError, KeyError, ZeroDivisionError):
            return None
    
    async def get_candlestick_data(self, symbol: str, timespan: str = "day", multiplier: int = 1, limit: int = 100, start_date: str = None, end_date: str = None) -> CandleStickDataResponse:
        """Get candlestick data for charting - DOMAIN LOGIC"""
        # Use last trading date as default for end_date
        if end_date is None:
            end_date = await self.market_repository.get_last_trading_date()
        
        cache_key = f"candles_{symbol}_{timespan}_{multiplier}_{limit}_{start_date or 'auto'}_{end_date or 'auto'}"
        
        # Try cache first
        cached_candles = await self.cache_service.get(cache_key)
        if cached_candles:
            return cached_candles
        
        # Convert timespan and multiplier to Massive API format
        massive_timespan = self._convert_to_massive_timespan(timespan)
        
        # Calculate date range
        from datetime import datetime, timedelta
        end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        if start_date:
            # Use provided start date
            start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            # Calculate automatic start date based on timespan, multiplier and limit
            if massive_timespan == "minute":
                start_date_dt = end_date_dt - timedelta(minutes=multiplier * limit)
            elif massive_timespan == "hour":
                start_date_dt = end_date_dt - timedelta(hours=multiplier * limit)
            elif massive_timespan == "day":
                start_date_dt = end_date_dt - timedelta(days=multiplier * limit)
            elif massive_timespan == "week":
                start_date_dt = end_date_dt - timedelta(weeks=multiplier * limit)
            elif massive_timespan == "month":
                start_date_dt = end_date_dt - timedelta(days=30 * multiplier * limit)
            else:  # default to day
                start_date_dt = end_date_dt - timedelta(days=limit)
        
        # Get candlestick data from repository
        from_str = start_date_dt.strftime("%Y-%m-%d")
        to_str = end_date_dt.strftime("%Y-%m-%d")
        
        raw_data = await self.market_repository.fetch_candlestick_data(
            symbol, multiplier, massive_timespan, from_str, to_str, limit
        )
        
        if not raw_data or "results" not in raw_data:
            return CandleStickDataResponse(results=[])
        
        # Convert to CandleStick entities first
        candlesticks = []
        for result in raw_data["results"]:
            candle = self._convert_massive_to_candlestick(result)
            if candle:
                candlesticks.append(candle)
        
        # Sort by timestamp
        candlesticks.sort(key=lambda x: x.timestamp)
        
        # Convert to CandleData DTOs
        candle_data_list = [
            CandleData(
                t=int(candle.timestamp.timestamp() * 1000),
                c=candle.close,
                o=candle.open,
                h=candle.high,
                l=candle.low,
                v=candle.volume
            )
            for candle in candlesticks
        ]
        
        # Build response
        response = CandleStickDataResponse(results=candle_data_list)
        
        # Cache the result
        await self.cache_service.set(cache_key, response, ttl=300)
        
        return response
    
    def _convert_to_massive_timespan(self, timespan: str) -> str:
        """Convert frontend timespan to Massive API timespan"""
        timespan_mapping = {
            "minute": "minute",
            "hour": "hour",
            "day": "day",
            "week": "week",  # Keep weeks as weeks
            "month": "month",  # Keep months as months
            "quarter": "quarter",  # Keep quarters as quarters
            "year": "year"  # Keep years as years
        }
        return timespan_mapping.get(timespan.lower(), "day")
    
    def _convert_massive_to_candlestick(self, raw_data: Dict[str, Any]) -> Optional[CandleStick]:
        """Convert Massive API response to CandleStick entity - DOMAIN LOGIC"""
        try:
            if not all(k in raw_data for k in ["o", "h", "l", "c", "v", "t"]):
                return None
            
            # Convert millisecond timestamp to datetime
            from datetime import datetime, timezone
            timestamp = datetime.fromtimestamp(raw_data["t"] / 1000, tz=timezone.utc)
            
            return CandleStick(
                timestamp=timestamp,
                open=float(raw_data["o"]),
                high=float(raw_data["h"]),
                low=float(raw_data["l"]),
                close=float(raw_data["c"]),
                volume=int(raw_data["v"])
            )
        except (TypeError, KeyError, ZeroDivisionError):
            return None
    
    async def _get_and_filter_market_data(self, limit: int = 500) -> List[Dict[str, Any]]:
        """Get raw market data and filter by volume - reusable function"""
        from app.utils.date_utils import get_last_trading_day
        
        # 1. Get raw data from infrastructure
        last_trading_day = get_last_trading_day()
        raw_data = await self.market_repository.fetch_raw_market_data(last_trading_day)
    
        # 2. Filter raw data to top assets by volume
        return self._filter_top_assets_by_volume(raw_data.get("results", []), limit)
    
    def _filter_top_assets_by_volume(self, raw_items: List[Dict[str, Any]], limit: int = 500) -> List[Dict[str, Any]]:
        """Filter raw data to keep only the top N by volume - DOMAIN LOGIC"""
        if not raw_items:
            return raw_items
        
        # Filter out items without volume data and sort by volume in descending order
        valid_items = [item for item in raw_items if "v" in item and item["v"] is not None]
        sorted_items = sorted(valid_items, key=lambda x: x["v"], reverse=True)
        
        # Return top N items
        return sorted_items[:limit]

def _convert_to_massive_timespan(self, timespan: str) -> str:
    """Convert frontend timespan to Massive API timespan"""
    timespan_mapping = {
        "minute": "minute",
        "hour": "hour",
        "day": "day",
        "week": "week",  # Keep weeks as weeks
        "month": "month",  # Keep months as months
        "quarter": "quarter",  # Keep quarters as quarters
        "year": "year"  # Keep years as years
    }
    return timespan_mapping.get(timespan.lower(), "day")

def _convert_massive_to_candlestick(self, raw_data: Dict[str, Any]) -> Optional[CandleStick]:
    """Convert Massive API response to CandleStick entity - DOMAIN LOGIC"""
    try:
        if not all(k in raw_data for k in ["o", "h", "l", "c", "v", "t"]):
            return None
        
        # Convert millisecond timestamp to datetime
        from datetime import datetime, timezone
        timestamp = datetime.fromtimestamp(raw_data["t"] / 1000, tz=timezone.utc)
        
        return CandleStick(
            timestamp=timestamp,
            open=float(raw_data["o"]),
            high=float(raw_data["h"]),
            low=float(raw_data["l"]),
            close=float(raw_data["c"]),
            volume=int(raw_data["v"])
        )
    except (TypeError, KeyError, ValueError):
        return None