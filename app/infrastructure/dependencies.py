# app/infrastructure/dependencies.py
from functools import lru_cache
from sqlmodel import Session

from app.db.base import get_session
from app.application.services.user_service import UserService
from app.application.services.market_service import MarketService
from app.domain.use_cases.user_use_cases import UserUseCases, SQLUserRepository, PasslibPasswordService, JWTTokenService
from app.domain.use_cases.market_use_cases import MarketUseCases, PolygonMarketClient, MemoryMarketCache


@lru_cache()
def get_user_service_instance() -> UserService:
    """Get cached user service instance"""
    # This would be properly implemented with dependency injection
    # For now, return a placeholder
    pass


@lru_cache()
def get_market_service_instance() -> MarketService:
    """Get cached market service instance"""
    cache_service = MemoryMarketCache()
    market_repository = PolygonMarketClient()
    market_use_cases = MarketUseCases(market_repository, cache_service)
    return MarketService(market_use_cases)
