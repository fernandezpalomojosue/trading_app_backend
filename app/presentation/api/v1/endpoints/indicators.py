# app/presentation/api/v1/endpoints/indicators.py
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

from app.application.dto.indicators_dto import (
    EMAResponse,
    SMAResponse,
    RSIResponse,
    MACDResponse
)
from app.application.services.indicators_service import IndicatorsService
from app.domain.use_cases.indicators_use_cases import IndicatorsUseCases
from app.infrastructure.external.market_client import PolygonMarketClient
from app.infrastructure.cache.memory_cache import MemoryMarketCache
from app.infrastructure.cache.redis_cache import RedisMarketCache
from app.core.config import get_settings
from app.infrastructure.security.auth_dependencies import get_current_user_dependency

router = APIRouter(prefix="/indicators", tags=["indicators"])


def get_indicators_service() -> IndicatorsService:
    """Get indicators service instance"""
    settings = get_settings()
    
    # Choose cache implementation based on configuration
    if settings.CACHE_TYPE == "redis":
        cache = RedisMarketCache(settings.REDIS_URL)
    else:
        cache = MemoryMarketCache()
    
    # Create client and use cases
    client = PolygonMarketClient()
    return IndicatorsUseCases(client, cache)


@router.get("/{symbol}/ema", response_model=EMAResponse)
async def get_ema(
    symbol: str,
    window: int = Query(14, ge=1, le=200, description="EMA window period"),
    timespan: str = Query("day", description="Timespan: minute, hour, day, week, month"),
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    limit: int = Query(100, ge=1, le=5000, description="Number of data points to return"),
    indicators_service: IndicatorsService = Depends(get_indicators_service),
    current_user = Depends(get_current_user_dependency)
):
    """Get EMA (Exponential Moving Average) indicator data"""
    return await indicators_service.get_ema(
        symbol=symbol,
        window=window,
        timespan=timespan,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )


@router.get("/{symbol}/sma", response_model=SMAResponse)
async def get_sma(
    symbol: str,
    window: int = Query(14, ge=1, le=200, description="SMA window period"),
    timespan: str = Query("day", description="Timespan: minute, hour, day, week, month"),
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    limit: int = Query(100, ge=1, le=5000, description="Number of data points to return"),
    indicators_service: IndicatorsService = Depends(get_indicators_service),
    current_user = Depends(get_current_user_dependency)
):
    """Get SMA (Simple Moving Average) indicator data"""
    return await indicators_service.get_sma(
        symbol=symbol,
        window=window,
        timespan=timespan,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )


@router.get("/{symbol}/rsi", response_model=RSIResponse)
async def get_rsi(
    symbol: str,
    window: int = Query(14, ge=1, le=200, description="RSI window period"),
    timespan: str = Query("day", description="Timespan: minute, hour, day, week, month"),
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    limit: int = Query(100, ge=1, le=5000, description="Number of data points to return"),
    indicators_service: IndicatorsService = Depends(get_indicators_service),
    current_user = Depends(get_current_user_dependency)
):
    """Get RSI (Relative Strength Index) indicator data"""
    return await indicators_service.get_rsi(
        symbol=symbol,
        window=window,
        timespan=timespan,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )


@router.get("/{symbol}/macd", response_model=MACDResponse)
async def get_macd(
    symbol: str,
    fast: int = Query(12, ge=1, le=100, description="Fast EMA period"),
    slow: int = Query(26, ge=1, le=200, description="Slow EMA period"),
    signal: int = Query(9, ge=1, le=50, description="Signal EMA period"),
    timespan: str = Query("day", description="Timespan: minute, hour, day, week, month"),
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    limit: int = Query(100, ge=1, le=5000, description="Number of data points to return"),
    indicators_service: IndicatorsService = Depends(get_indicators_service),
    current_user = Depends(get_current_user_dependency)
):
    """Get MACD (Moving Average Convergence Divergence) indicator data"""
    return await indicators_service.get_macd(
        symbol=symbol,
        fast=fast,
        slow=slow,
        signal=signal,
        timespan=timespan,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
