# app/domain/use_cases/indicators_use_cases.py
from typing import Optional
import pandas as pd
import ta
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

    async def get_indicators(
        self,
        symbol: str,
        window: int,
        fast: int,
        slow: int,
        signal: int,
        timespan: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> dict:
        """Get all technical indicators for a symbol"""
        raw_data = await self.market_client.fetch_candlestick_data(symbol, timespan, start_date, end_date, limit)
        raw_data = raw_data.get("results", [])
        df = pd.DataFrame(raw_data)
        df['rsi'] = self.get_rsi(df, window)
        df['ema'] = self.get_ema(df, window)
        df['macd'] = self.get_macd(df, fast, slow, signal)
        df['sma'] = self.get_sma(df, window)
        return df
    
    async def get_ema(
        self,
        raw_data: pd.DataFrame,
        window: int
    ):
        """Get EMA indicator data with caching"""
        cache_key = f"ema_{raw_data['ticker'].iloc[0]}_{window}"
        
        # Try cache first
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        ema = ta.trend.EMAIndicator(close=raw_data['close'], window=window).ema_indicator()
        
        # Cache result
        await self.cache.set(cache_key, ema, ttl=60)
        
        return ema
    
    async def get_sma(
        self,
        raw_data: pd.DataFrame,
        window: int
    ):
        """Get SMA indicator data with caching"""
        cache_key = f"sma_{raw_data['ticker'].iloc[0]}_{window}"
        
        # Try cache first
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        sma = ta.trend.SMAIndicator(close=raw_data['close'], window=window).sma_indicator()
        
        # Cache result
        await self.cache.set(cache_key, sma, ttl=60)
        
        return sma
    
    async def get_rsi(
        self,
        raw_data: pd.DataFrame,
        window: int
    ):
        """Get RSI indicator data with caching"""
        cache_key = f"rsi_{raw_data['ticker'].iloc[0]}_{window}"
        
        # Try cache first
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        rsi = ta.momentum.RSIIndicator(close=raw_data['close'], window=window).rsi()
        
        # Cache result
        await self.cache.set(cache_key, rsi, ttl=60)
        
        return rsi
    
    async def get_macd(
        self,
        raw_data: pd.DataFrame,
        fast: int,
        slow: int,
        signal: int
    ):
        """Get MACD indicator data with caching"""
        cache_key = f"macd_{raw_data['ticker'].iloc[0]}_{fast}_{slow}_{signal}"
        
        # Try cache first
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        macd = ta.trend.MACD(close=raw_data['close'], fast=fast, slow=slow, signal=signal)
        
        # Cache result
        await self.cache.set(cache_key, macd, ttl=60)
        
        return macd                           
    
   