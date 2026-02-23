# app/infrastructure/external/market_client.py
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import aiohttp
from fastapi import HTTPException

from app.domain.entities.market import Asset, MarketSummary, MarketType
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
            # Mantener solo llamadas de los últimos 60 segundos
            one_minute_ago = now - 60
            self.calls = [t for t in self.calls if t > one_minute_ago]
            
            if len(self.calls) >= self.calls_per_minute:
                # Esperar hasta que pase 1 minuto desde la llamada más antigua
                oldest_call = min(self.calls)
                wait_time = 60 - (now - oldest_call)
                if wait_time > 0:
                    print(f"Rate limit alcanzado. Esperando {wait_time:.1f} segundos...")
                    await asyncio.sleep(wait_time)
                    # Después de esperar, resetear para evitar acumulación
                    self.calls = []
            
            self.calls.append(now)


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
            # Use Massive API Custom Bars endpoint
            data = await self._make_request(
                f"/v2/aggs/ticker/{symbol.upper()}/range/{multiplier}/{timespan}/{from_date}/{to_date}",
                {"adjusted": "true", "sort": "asc", "limit": str(limit)}
            )
            
            return data if data.get("status") == "OK" else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching candlestick data: {str(e)}")
    
    async def get_last_trading_date(self) -> str:
        """Get the last trading date from market status - INFRASTRUCTURE ONLY"""
        try:
            from datetime import datetime, timedelta
            
            # Start with yesterday (never today)
            last_trading_day = datetime.now() - timedelta(days=1)
            
            # If it's weekend, go back to Friday
            if last_trading_day.weekday() == 6:  # Sunday
                last_trading_day -= timedelta(days=2)  # Go to Friday
            elif last_trading_day.weekday() == 5:  # Saturday
                last_trading_day -= timedelta(days=1)  # Go to Friday
            
            # Double-check: if somehow we got today's date, go back one more day
            today = datetime.now()
            if last_trading_day.date() >= today.date():
                last_trading_day = today - timedelta(days=1)
                # Apply weekend logic again if needed
                if last_trading_day.weekday() == 6:  # Sunday
                    last_trading_day -= timedelta(days=2)
                elif last_trading_day.weekday() == 5:  # Saturday
                    last_trading_day -= timedelta(days=1)
            
            return last_trading_day.strftime("%Y-%m-%d")
        except Exception as e:
            # Fallback to yesterday if there's an error
            from datetime import datetime, timedelta
            return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    async def fetch_ticker_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch complete ticker details from reference endpoint - INFRASTRUCTURE ONLY"""
        try:
            # Use Polygon API reference endpoint for ticker details
            data = await self._make_request(f"/v3/reference/tickers/{symbol.upper()}")
            
            return data if data.get("status") == "OK" else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching ticker details: {str(e)}")
    
    def _map_polygon_market(self, polygon_market: str) -> MarketType:
        """Map Polygon market to our MarketType enum"""
        market_mapping = {
            "stocks": MarketType.STOCKS,
            "crypto": MarketType.CRYPTO,
            "fx": MarketType.FX,
            "indices": MarketType.INDICES
        }
        return market_mapping.get(polygon_market.lower(), MarketType.STOCKS)
