# app/domain/use_cases/market_use_cases.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.utils.market_utils import MarketDataProcessor
from app.domain.entities.market import Asset, MarketOverview, MarketType, MarketSummary, CandleStick


class MarketRepository(ABC):
    """Abstract repository for market operations"""
    
    @abstractmethod
    async def get_asset_raw_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get raw asset data from external API"""
        pass

    @abstractmethod
    async def search_assets_raw(self, query: str, market_type: Optional[MarketType] = None) -> List[Dict[str, Any]]:
        """Search for assets - returns raw data"""
        pass

    @abstractmethod
    async def fetch_raw_market_data(self, date: str) -> Dict[str, Any]:
        """Fetch raw market data from external API"""
        pass
    
    @abstractmethod
    async def fetch_symbol_data(self, symbol: str, date: str) -> Optional[Dict[str, Any]]:
        """Fetch OHLC data for a specific symbol"""
        pass
    
    @abstractmethod
    async def fetch_candlestick_data(self, symbol: str, multiplier: int, timespan: str, from_date: str, to_date: str, limit: int = 100) -> Optional[Dict[str, Any]]:
        """Fetch candlestick data using Massive API Custom Bars endpoint"""
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
    
    async def get_market_summary(self, market_type: MarketType) -> MarketOverview:
        """Get market summary with optimized single API call and business logic in domain"""
        from app.utils.date_utils import get_last_trading_day
        
        cache_key = f"market_summary_{market_type.value}"
    
        # Try cache first
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            return cached_data
    
        # 1. Get raw data from infrastructure
        last_trading_day = get_last_trading_day()
        raw_data = await self.market_repository.fetch_raw_market_data(last_trading_day)
    
        # 2. Convert to domain entities
        entities = []
        for item in raw_data.get("results", []):
            entity = self._convert_raw_to_entity(item)
            if entity:
                entities.append(entity)
    
        # 3. Process with business logic (PURE DOMAIN LOGIC)
        gainers = MarketDataProcessor.get_top_gainers(entities)
        losers = MarketDataProcessor.get_top_losers(entities)
        active = MarketDataProcessor.get_most_active(entities)
        total_assets = MarketDataProcessor.calculate_total_assets(entities)
    
        # 4. Build overview
        overview = MarketOverview(
        market=market_type,
        total_assets=total_assets,
        status="active",
        last_updated=datetime.now(),
        top_gainers=gainers,
        top_losers=losers,
        most_active=active
        )
    
        # 5. Cache result
        await self.cache_service.set(cache_key, overview, ttl=300)
    
        return overview

    def _convert_raw_to_entity(self, raw_item: Dict[str, Any]) -> Optional[MarketSummary]:
        """Convert raw API data to MarketSummary entity"""
        try:
            if not all(k in raw_item for k in ["T", "c", "o", "v"]):
                return None
            
            open_price = raw_item["o"]
            close_price = raw_item["c"]
        
            change = close_price - open_price
            change_percent = (change / open_price * 100) if open_price > 0 else 0
        
            return MarketSummary(
            symbol=raw_item["T"],
            open=open_price,
            close=close_price,
            high=raw_item.get("h", close_price),
            low=raw_item.get("l", close_price),
            volume=raw_item["v"],
            vwap=raw_item["vw"],
            change=round(change, 4),
            change_percent=round(change_percent, 2),
            timestamp=datetime.now()
            )
        except (TypeError, KeyError, ZeroDivisionError):
            return None
    
    async def get_asset_details(self, symbol: str) -> Optional[Asset]:
        """Get detailed asset information - DOMAIN ORCHESTRATION"""
        cache_key = f"asset_details_{symbol}"
    
        # Try cache first
        cached_asset = await self.cache_service.get(cache_key)
        if cached_asset:
            return cached_asset
    
        # 1. Get raw data from infrastructure
        raw_data = await self.market_repository.get_asset_raw_data(symbol)
    
        # 2. Convert to entity (domain logic)
        asset = self._convert_raw_to_asset(raw_data) if raw_data else None
    
        # 3. Cache if found
        if asset:
            await self.cache_service.set(cache_key, asset, ttl=60)
    
        return asset

    async def search_assets(self, query: str, market_type: Optional[MarketType] = None) -> List[Asset]:
        """Search for assets by query - DOMAIN ORCHESTRATION"""
        if not query or len(query) < 2:
            return []
    
        # 1. Get raw data from infrastructure
        raw_results = await self.market_repository.search_assets_raw(query, market_type)
    
        # 2. Convert to entities (domain logic)
        assets = []
        for raw_data in raw_results:
            asset = self._convert_raw_to_asset(raw_data)
            if asset:
                assets.append(asset)
    
        return assets

    def _convert_raw_to_asset(self, raw_data: Dict[str, Any]) -> Optional[Asset]:
        """Convert raw API data to Asset entity - DOMAIN LOGIC"""
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

    async def get_assets_list(self, market_type: MarketType, limit: int = 50, offset: int = 0) -> List[Asset]:
        """Get assets list from raw market data - DOMAIN LOGIC"""
        cache_key = f"assets_list_{market_type.value}_{limit}_{offset}"
        
        # Try cache first
        cached_assets = await self.cache_service.get(cache_key)
        if cached_assets:
            return cached_assets
        
        # 1. Get raw data from infrastructure
        from app.utils.date_utils import get_last_trading_day
        last_trading_day = get_last_trading_day()
        raw_data = await self.market_repository.fetch_raw_market_data(last_trading_day)
        
        # 2. Process raw data using efficient list comprehension
        seen_symbols = set()
        
        def create_asset(item):
            symbol = item.get("T", "")
            if not symbol or symbol in seen_symbols:
                return None
            seen_symbols.add(symbol)
            return self._convert_raw_to_asset_basic(item, market_type)
        
        # List comprehension with filtering - much faster than explicit loop
        all_assets = [
            asset for asset in (create_asset(item) for item in raw_data.get("results", []))
            if asset is not None
        ]
        
        # 3. Apply pagination using efficient slicing
        paginated_assets = all_assets[offset:offset + limit]
        
        # 4. Cache the paginated result
        await self.cache_service.set(cache_key, paginated_assets, ttl=300)
        
        return paginated_assets

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
    
    async def get_candlestick_data(self, symbol: str, timeframe: str = "1d", limit: int = 100, start_date: str = None) -> List[CandleStick]:
        """Get candlestick data for charting - DOMAIN LOGIC"""
        cache_key = f"candles_{symbol}_{timeframe}_{limit}_{start_date or 'auto'}"
        
        # Try cache first
        cached_candles = await self.cache_service.get(cache_key)
        if cached_candles:
            return cached_candles
        
        # Parse timeframe to multiplier and timespan
        multiplier, timespan = self._parse_timeframe(timeframe)
        
        # Calculate date range
        from datetime import datetime, timedelta
        end_date = datetime.now()
        
        if start_date:
            # Use provided start date
            start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            # Calculate automatic start date based on timeframe and limit
            if timespan == "minute":
                start_date_dt = end_date - timedelta(minutes=multiplier * limit)
            elif timespan == "hour":
                start_date_dt = end_date - timedelta(hours=multiplier * limit)
            elif timespan == "day":
                start_date_dt = end_date - timedelta(days=multiplier * limit)
            else:  # default to day
                start_date_dt = end_date - timedelta(days=limit)
        
        # Get candlestick data from repository
        from_str = start_date_dt.strftime("%Y-%m-%d")
        to_str = end_date.strftime("%Y-%m-%d")
        
        raw_data = await self.market_repository.fetch_candlestick_data(
            symbol, multiplier, timespan, from_str, to_str, limit
        )
        
        if not raw_data or "results" not in raw_data:
            return []
        
        # Convert to CandleStick entities
        candlesticks = []
        for result in raw_data["results"]:
            candle = self._convert_massive_to_candlestick(result)
            if candle:
                candlesticks.append(candle)
        
        # Sort by timestamp
        candlesticks.sort(key=lambda x: x.timestamp)
        
        # Cache the result
        await self.cache_service.set(cache_key, candlesticks, ttl=300)
        
        return candlesticks
    
    def _parse_timeframe(self, timeframe: str) -> tuple[int, str]:
        """Parse timeframe string to multiplier and timespan for Massive API"""
        timeframe_mapping = {
            "1m": (1, "minute"),
            "5m": (5, "minute"),
            "15m": (15, "minute"),
            "30m": (30, "minute"),
            "1h": (1, "hour"),
            "4h": (4, "hour"),
            "1d": (1, "day"),
            "1w": (7, "day"),  # 1 week = 7 days
            "1M": (30, "day")  # 1 month = 30 days
        }
        
        # Handle dynamic multipliers (e.g., "10m", "2h", "3d")
        if timeframe.endswith('m'):
            minutes = int(timeframe[:-1])
            return (minutes, "minute")
        elif timeframe.endswith('h'):
            hours = int(timeframe[:-1])
            return (hours, "hour")
        elif timeframe.endswith('d'):
            days = int(timeframe[:-1])
            return (days, "day")
        elif timeframe.endswith('w'):
            weeks = int(timeframe[:-1])
            return (weeks * 7, "day")
        elif timeframe.endswith('M'):
            months = int(timeframe[:-1])
            return (months * 30, "day")
        
        # Default fallback
        return timeframe_mapping.get(timeframe, (1, "day"))
    
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