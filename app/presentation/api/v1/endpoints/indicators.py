# app/presentation/api/v1/endpoints/indicators.py
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List

from app.application.dto.indicators_dto import IndicatorDataPoint
from app.application.services.indicators_service import IndicatorsService
from app.domain.use_cases.indicators_use_cases import IndicatorsUseCases
from app.infrastructure.cache.memory_cache import MemoryMarketCache
from app.infrastructure.cache.redis_cache import RedisCache
from app.core.config import get_settings
from app.infrastructure.security.auth_dependencies import get_current_user_dependency
from app.application.repositories.market_repository import MarketRepository
from app.infrastructure.external.market_client import PolygonMarketClient

router = APIRouter()


def get_indicators_service() -> IndicatorsService:
    """Get indicators service instance"""
    settings = get_settings()
    if settings.CACHE_TYPE == "redis":
        cache = RedisCache(settings.REDIS_URL)
    else:
        cache = MemoryMarketCache()
    
    return IndicatorsUseCases(cache)

def get_market_client()->MarketRepository:
    settings = get_settings()
    return PolygonMarketClient()


@router.get("/{symbol}", response_model=List[IndicatorDataPoint])
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
    market_client: MarketRepository = Depends(get_market_client),
    current_user = Depends(get_current_user_dependency)
):
    # Validación
    if fast >= slow:
        raise HTTPException(status_code=400, detail="fast must be less than slow")

    raw_data = await market_client.fetch_candlestick_data(symbol, timespan, start_date, end_date, limit)

    data = await indicators_service.get_indicators(
        symbol,
        raw_data,
        window,
        fast,
        slow,
        signal,
        timespan,
        start_date,
        end_date,
        limit
    )

    return data[-limit:]

