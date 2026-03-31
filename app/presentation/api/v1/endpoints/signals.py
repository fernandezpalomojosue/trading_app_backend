from fastapi import APIRouter, Depends, HTTPException
from app.infrastructure.database.signal_repository import SQLSignalRepository
from app.infrastructure.cache.redis_cache import RedisCache
from app.application.repositories.cache_repository import CacheRepository
from app.application.repositories.favorite_repository import FavoriteRepository
from app.db.base import get_session
from sqlmodel import Session
from app.infrastructure.database.favorite_repository import SQLFavoriteStockRepository
import logging

logger = logging.getLogger(__name__)

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

@router.post("/internal/run-signals")
async def run_signals(
    x_api_key: str = None,
    cache: CacheRepository = Depends(get_cache_repository),
    signal_repo: SQLSignalRepository = Depends(get_signal_repository),
    favorites_repo: FavoriteRepository = Depends(get_favorites_repository)
):
    """Internal endpoint for cron job to generate signals"""
    # Verify API key
    from app.core.config import get_settings
    settings = get_settings()
    
    expected_key = settings.get_signal_worker_api_key()
    
    logger.info("Received API key: %s", x_api_key)
    logger.info("Expected API key: %s", expected_key)
    
    if x_api_key != expected_key:
        logger.error("API key mismatch!")
        logger.error("Received: %s", x_api_key)
        logger.error("Expected: %s", expected_key)
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Import and run signal orchestrator
    from app.domain.use_cases.signal_orchestrator import SignalOrchestrator
    from app.infrastructure.external.market_client import PolygonMarketClient
    from app.infrastructure.cache.memory_cache import MemoryMarketCache
    from app.application.repositories.market_repository import MarketRepository
    from app.db.base import get_session
    
    # Get stocks to process (all favorites from all users)
    stocks = await favorites_repo.get_all_favorites()
    
    # If no favorites found, use default stocks
    if not stocks:
        stocks = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]
    
    results = []
    for stock in stocks:
        try:
            # Create orchestrator
            market_client = PolygonMarketClient()
            cache_repo = MemoryMarketCache()
            orchestrator = SignalOrchestrator(market_client, cache_repo)
            
            # Generate signal
            signal = await orchestrator.generate_signal(stock, "day", "2025-01-01", "2025-12-31")
            
            if signal:
                # Save to database
                await signal_repo.save_signal(stock, signal)
                await cache.set(f"signal:{stock}", signal)
                results.append({"symbol": stock, "signal": signal, "status": "success"})
            else:
                results.append({"symbol": stock, "status": "no_signal"})
                
        except Exception as e:
            results.append({"symbol": stock, "status": "error", "error": str(e)})
    
    return {"message": "Signals processed", "results": results}

@router.get("/signal/{symbol}")
async def get_signals(
    symbol: str,
    cache: CacheRepository = Depends(get_cache_repository),
    signal_repo: SQLSignalRepository = Depends(get_signal_repository)
):
    result = await cache.get(f"signal:{symbol}")
    if result:
        return result
    
    result = await signal_repo.get_by_symbol(symbol)
    if result:
        await cache.set(f"signal:{symbol}", result)
        return result
    
    raise HTTPException(status_code=404, detail=f"No signal found for symbol: {symbol}")
    
    
