# app/infrastructure/external/market_client.py
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import aiohttp
from fastapi import HTTPException

from app.domain.entities.market import Asset, MarketSummary, MarketOverview, MarketType
from app.domain.use_cases.market_use_cases import MarketRepository
from app.utils.date_utils import get_last_trading_day
from app.core.config import settings


class RateLimiter:
    """Rate limiter for API calls"""
    def __init__(self, calls_per_minute: int = 5):
        self.calls_per_minute = calls_per_minute
        self.calls = []
        self.lock = asyncio.Lock()
    
    async def wait_if_needed(self):
        async with self.lock:
            now = time.time()
            self.calls = [t for t in self.calls if now - t < 60]
            
            if len(self.calls) >= self.calls_per_minute:
                oldest_call = self.calls[0]
                wait_time = 60 - (now - oldest_call)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
            
            self.calls.append(time.time())


class PolygonMarketClient(MarketRepository):
    """Polygon.io client implementation of MarketRepository"""
    
    BASE_URL = "https://api.massive.com"
    
    def __init__(self, api_key: str = None, rate_limit: int = 5):
        self.api_key = api_key or settings.MASSIVE_API_KEY
        if not self.api_key:
            raise ValueError("Se requiere una API key para Massive API. Configura MASSIVE_API_KEY")
        self.rate_limiter = RateLimiter(calls_per_minute=rate_limit)
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a rate-limited API request"""
        await self.rate_limiter.wait_if_needed()
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        params["apikey"] = self.api_key
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Polygon API error: {await response.text()}"
                    )
        except aiohttp.ClientError as e:
            raise HTTPException(status_code=500, detail=f"External API error: {str(e)}")
    
    async def fetch_raw_market_data(self, date: str) -> Dict[str, Any]:
        """Fetch raw market data - INFRASTRUCTURE ONLY"""
        try:
            data = await self._make_request(
                f"/v2/aggs/grouped/locale/us/market/stocks/{date}",
                {"sort": "volume", "order": "desc", "limit": "100"}
            )
            return data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching market data: {str(e)}")
    
    async def get_asset_raw_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get raw asset data from API - INFRASTRUCTURE ONLY"""
        try:
            ticker_data = await self._make_request(f"/v3/reference/tickers/{symbol.upper()}")
            return ticker_data.get("results")
        except Exception:
            return None
    
    async def search_assets_raw(self, query: str, market_type: Optional[MarketType] = None) -> List[Dict[str, Any]]:
        """Search for assets - returns raw data"""
        try:
            params = {"search": query, "limit": "20"}
            if market_type:
                params["market"] = market_type.value
            
            search_data = await self._make_request("/v3/reference/tickers", params)
            return search_data.get("results", [])
        except Exception:
            return []
    
    async def fetch_symbol_data(self, symbol: str, date: str) -> Optional[Dict[str, Any]]:
        """Fetch OHLC data for a specific symbol using Massive API - INFRASTRUCTURE ONLY"""
        try:
            # Convert date to timestamp if needed
            if date.count('-') == 2:  # YYYY-MM-DD format
                from datetime import datetime
                dt = datetime.strptime(date, "%Y-%m-%d")
                from_timestamp = int(dt.timestamp() * 1000)
                to_timestamp = from_timestamp + (24 * 60 * 60 * 1000)  # Add 1 day
            else:
                from_timestamp = int(date)
                to_timestamp = from_timestamp + (24 * 60 * 60 * 1000)
            
            # Use Massive API Custom Bars endpoint
            data = await self._make_request(
                f"/v2/aggs/ticker/{symbol.upper()}/range/1/day/{from_timestamp}/{to_timestamp}",
                {"adjusted": "true", "sort": "asc", "limit": "1"}
            )
            
            return data if data.get("status") == "OK" else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching symbol data: {str(e)}")
    
    async def fetch_candlestick_data(self, symbol: str, multiplier: int, timespan: str, from_date: str, to_date: str, limit: int = 100) -> Optional[Dict[str, Any]]:
        """Fetch candlestick data using Massive API Custom Bars endpoint - INFRASTRUCTURE ONLY"""
        try:
            # Convert dates to timestamps if needed
            if from_date.count('-') == 2:  # YYYY-MM-DD format
                from datetime import datetime
                dt_from = datetime.strptime(from_date, "%Y-%m-%d")
                dt_to = datetime.strptime(to_date, "%Y-%m-%d")
                from_timestamp = int(dt_from.timestamp() * 1000)
                to_timestamp = int(dt_to.timestamp() * 1000)
            else:
                from_timestamp = int(from_date)
                to_timestamp = int(to_date)
            
            # Use Massive API Custom Bars endpoint
            data = await self._make_request(
                f"/v2/aggs/ticker/{symbol.upper()}/range/{multiplier}/{timespan}/{from_timestamp}/{to_timestamp}",
                {"adjusted": "true", "sort": "asc", "limit": str(limit)}
            )
            
            return data if data.get("status") == "OK" else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching candlestick data: {str(e)}")
    
    def _map_polygon_market(self, polygon_market: str) -> MarketType:
        """Map Polygon market to our MarketType enum"""
        market_mapping = {
            "stocks": MarketType.STOCKS,
            "crypto": MarketType.CRYPTO,
            "fx": MarketType.FX,
            "indices": MarketType.INDICES
        }
        return market_mapping.get(polygon_market.lower(), MarketType.STOCKS)
