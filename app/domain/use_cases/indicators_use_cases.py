# app/domain/use_cases/indicators_use_cases.py
from typing import Optional

from app.application.services.indicators_service import IndicatorsService
from app.application.dto.indicators_dto import (
    EMADataPoint,
    EMAResponse,
    SMADataPoint,
    SMAResponse,
    RSIDataPoint,
    RSIResponse,
    MACDDataPoint,
    MACDResponse
)
from app.infrastructure.external.market_client import PolygonMarketClient


class IndicatorsUseCases(IndicatorsService):
    """Use cases for technical indicators - implements IndicatorsService interface"""
    
    def __init__(self, market_client: PolygonMarketClient, cache_service):
        self.market_client = market_client
        self.cache = cache_service
    
    async def get_ema(
        self,
        symbol: str,
        window: int,
        timespan: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> EMAResponse:
        """Get EMA indicator data with caching"""
        cache_key = f"ema_{symbol}_{window}_{timespan}_{start_date}_{end_date}_{limit}"
        
        # Try cache first
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return EMAResponse(**cached_data)
        
        # Fetch from API
        raw_data = await self.market_client.fetch_ema(
            symbol, window, timespan, start_date, end_date, limit
        )
        
        # Transform to DTO
        results = [
            EMADataPoint(t=item.get("timestamp", 0), v=item.get("value", 0.0))
            for item in raw_data
        ]
        
        response = EMAResponse(
            symbol=symbol,
            window=window,
            timespan=timespan,
            results=results
        )
        
        # Cache result
        await self.cache.set(cache_key, response.model_dump(), ttl=60)
        
        return response
    
    async def get_sma(
        self,
        symbol: str,
        window: int,
        timespan: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> SMAResponse:
        """Get SMA indicator data with caching"""
        cache_key = f"sma_{symbol}_{window}_{timespan}_{start_date}_{end_date}_{limit}"
        
        # Try cache first
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return SMAResponse(**cached_data)
        
        # Fetch from API
        raw_data = await self.market_client.fetch_sma(
            symbol, window, timespan, start_date, end_date, limit
        )
        
        # Transform to DTO
        results = [
            SMADataPoint(t=item.get("timestamp", 0), v=item.get("value", 0.0))
            for item in raw_data
        ]
        
        response = SMAResponse(
            symbol=symbol,
            window=window,
            timespan=timespan,
            results=results
        )
        
        # Cache result
        await self.cache.set(cache_key, response.model_dump(), ttl=60)
        
        return response
    
    async def get_rsi(
        self,
        symbol: str,
        window: int,
        timespan: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> RSIResponse:
        """Get RSI indicator data with caching"""
        cache_key = f"rsi_{symbol}_{window}_{timespan}_{start_date}_{end_date}_{limit}"
        
        # Try cache first
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return RSIResponse(**cached_data)
        
        # Fetch from API
        raw_data = await self.market_client.fetch_rsi(
            symbol, window, timespan, start_date, end_date, limit
        )
        
        # Transform to DTO
        results = [
            RSIDataPoint(t=item.get("timestamp", 0), v=item.get("value", 0.0))
            for item in raw_data
        ]
        
        response = RSIResponse(
            symbol=symbol,
            window=window,
            timespan=timespan,
            results=results
        )
        
        # Cache result
        await self.cache.set(cache_key, response.model_dump(), ttl=60)
        
        return response
    
    async def get_macd(
        self,
        symbol: str,
        fast: int,
        slow: int,
        signal: int,
        timespan: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> MACDResponse:
        """Get MACD indicator data with caching"""
        cache_key = f"macd_{symbol}_{fast}_{slow}_{signal}_{timespan}_{start_date}_{end_date}_{limit}"
        
        # Try cache first
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return MACDResponse(**cached_data)
        
        # Fetch from API
        raw_data = await self.market_client.fetch_macd(
            symbol, fast, slow, signal, timespan, start_date, end_date, limit
        )
        
        # Transform to DTO
        results = [
            MACDDataPoint(
                t=item.get("timestamp", 0),
                macd=item.get("value", 0.0),
                signal=item.get("signal", 0.0),
                histogram=item.get("histogram", 0.0)
            )
            for item in raw_data
        ]
        
        response = MACDResponse(
            symbol=symbol,
            fast=fast,
            slow=slow,
            signal_period=signal,
            timespan=timespan,
            results=results
        )
        
        # Cache result
        await self.cache.set(cache_key, response.model_dump(), ttl=60)
        
        return response
