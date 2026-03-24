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

router = APIRouter()


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


@router.get("/{symbol}", response_model=dict)
async def get_indicators(
    symbol: str,
    window: int = Query(14, ge=1, le=200),
    fast: int = Query(12, ge=1, le=200),
    slow: int = Query(26, ge=1, le=200),
    signal: int = Query(9, ge=1, le=200),
    timespan: str = Query("day"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(100, ge=1, le=5000),
    indicators_service: IndicatorsService = Depends(get_indicators_service),
    current_user = Depends(get_current_user_dependency)
):
    # Validación
    if fast >= slow:
        raise HTTPException(status_code=400, detail="fast must be less than slow")

    data = await indicators_service.get_indicators(
        symbol,
        window,
        fast,
        slow,
        signal,
        timespan,
        start_date,
        end_date,
        limit
    )

    # limitar resultados
    if "results" in data:
        data["results"] = data["results"][-limit:]

    return data

