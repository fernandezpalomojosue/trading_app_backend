from app.application.repositories.favorite_repository import FavoriteRepository
from app.domain.use_cases.indicators_use_cases import IndicatorsUseCases
from app.infrastructure.cache.redis_cache import RedisCache
from app.infrastructure.external.market_client import PolygonMarketClient
from app.infrastructure.database.signal_repository import SQLSignalRepository
from app.infrastructure.database.favorite_repository import SQLFavoriteStockRepository
from app.domain.use_cases.signal_orchestrator import SignalOrchestrator
from app.domain.use_cases.signal_engine_use_cases import SignalEngineUseCases
from app.utils.date_utils import get_last_trading_day
from app.db.base import get_session
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

async def run_signal_job():

    logger.info("Signal generation job started")
    
    try:
    market_client = PolygonMarketClient()
    cache_repository = RedisCache()
    indicator_service = IndicatorsUseCases(cache_repository)
    signal_engine = SignalEngineUseCases()
    signal_repository = SQLSignalRepository(get_session())
    favorite_repository = SQLFavoriteStockRepository(get_session())

    current_user = get_current_user_dependency()
    favorite_stocks = favorite_repository.get_user_favorites(current_user.id)

    orchestration_service = SignalOrchestrator(
        market_client,
        indicator_service,
        signal_engine,
        cache_repository,
        signal_repository
    )
    
    for stock in favorite_stocks:
        try:
            await orchestration_service.generate_signal(stock, "day", "2026-01-01", get_last_trading_day())
        except Exception as e:
            print(f"Error generating signal for {stock}: {e}")