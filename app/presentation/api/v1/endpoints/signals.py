from fastapi import APIRouter, Depends
from app.infrastructure.database.signal_repository import SignalRepository
from app.infrastructure.cache.redis_cache import RedisCache
from app.application.repositories.cache_repository import CacheRepository

router = APIRouter()

def get_cache_repository() -> CacheRepository:
    """Get cache repository instance"""
    return RedisCache(redis_url="redis://localhost:6379/0")

@router.get("/signal/{symbol}")
async def get_signals(symbol: str,
cache: CacheRepository = Depends(get_cache_repository)
):
    result = await cache.get(f"signal:{symbol}")
    if result:
        return result
    result = await SignalRepository().get_by_symbol(symbol)
    if result:
        await cache.set(f"signal:{symbol}", result)
        return result
    return None
    
    
