from fastapi import APIRouter, Depends, HTTPException, Header
from app.domain.use_cases.signal_engine_use_cases import SignalEngineUseCases
from app.infrastructure.database.signal_repository import SQLSignalRepository
from app.infrastructure.cache.redis_cache import RedisCache
from app.application.repositories.cache_repository import CacheRepository
from app.application.repositories.favorite_repository import FavoriteRepository
from app.db.base import get_session
from sqlmodel import Session
from app.infrastructure.database.favorite_repository import SQLFavoriteStockRepository
import logging
from app.infrastructure.external.market_client import PolygonMarketClient
from app.core.logging_config import get_logger
from app.application.repositories.market_repository import MarketRepository
from app.domain.use_cases.indicators_use_cases import IndicatorsUseCases
from app.application.services.indicators_service import IndicatorsService
from app.application.services.signal_engine_service import SignalEngineService
from app.domain.use_cases.signal_orchestrator import SignalOrchestrator
from app.workers.signal_worker import run_signal_job
from app.domain.entities.user import UserEntity
from app.core.security import get_current_user

logger = get_logger(__name__)

router = APIRouter()

def get_cache_repository() -> CacheRepository:
    """Get cache repository instance"""
    from app.core.config import get_settings
    settings = get_settings()
    return RedisCache(settings.REDIS_URL)

def get_signal_repository(db: Session = Depends(get_session)) -> SQLSignalRepository:
    """Get signal repository instance"""
    return SQLSignalRepository(db)

def get_favorites_repository(db: Session = Depends(get_session)) -> FavoriteRepository:
    """Get favorites repository instance"""
    return SQLFavoriteStockRepository(db)

def get_market_client()->MarketRepository:
    """Get market client instance"""
    return PolygonMarketClient()

def get_indicators_service()->IndicatorsService:
    """Get indicators service instance"""
    return IndicatorsUseCases(get_cache_repository())

def get_signal_engine_service()->SignalEngineService:
    """Get signal engine service instance"""
    return SignalEngineUseCases()

@router.post("/internal/run-signals", include_in_schema=False)
async def run_signals(
    x_api_key: str = Header(None, alias="x-api-key"),
):
    """Internal endpoint for cron job to generate signals"""
    # Verify API key
    from app.core.config import get_settings
    settings = get_settings()
    
    expected_key = settings.get_signal_worker_api_key()
    
    if x_api_key != expected_key:
        logger.error("API key mismatch", component="signals", received_key=x_api_key)
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    await run_signal_job()
    return {"status": "triggered"}

@router.get("/{symbol}")
async def get_signal(
    symbol: str,
    cache: CacheRepository = Depends(get_cache_repository),
    signal_repo: SQLSignalRepository = Depends(get_signal_repository),
    current_user: UserEntity = Depends(get_current_user)
):
    result = await cache.get(f"signal:{symbol}")
    if result:
        return result
    
    result = await signal_repo.get_by_symbol(symbol)
    if result:
        cache_success = await cache.set(f"signal:{symbol}", result)
        if not cache_success:
            logger.warning(
                "Failed to cache signal",
                component="signals",
                symbol=symbol
            )
        return result
    else:
        return {"symbol": symbol, "status": "no_signal"}
