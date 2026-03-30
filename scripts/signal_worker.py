import asyncio
from app.application.repositories.market_repository import MarketRepository
from app.application.services.indicators_service import IndicatorsService
from app.application.repositories.cache_repository import CacheRepository
from app.application.services.signal_engine_service import SignalEngineService
from app.application.repositories.signal_repository import SignalRepository
from app.application.repositories.favorite_repository import FavoriteRepository
from app.infrastructure.security.auth_dependencies import get_current_user_dependency
from app.domain.use_cases.signal_orchestrator import SignalOrchestrator
from app.utils.date_utils import get_last_trading_day
async def main():
    print("Signal worker started")
    market_client = MarketRepository()
    cache_repository = CacheRepository()
    indicator_service = IndicatorsService(cache_repository)
    signal_engine = SignalEngineService(indicator_service)
    signal_repository = SignalRepository()
    favorite_repository = FavoriteRepository()

    current_user = get_current_user_dependency()
    favorite_stocks = favorite_repository.get_user_favorites(current_user.id)

    orchestration_service = SignalOrchestrator(
        market_client,
        cache_repository,
        indicator_service,
        signal_engine,
        signal_repository
    )
    
    for stock in favorite_stocks:
        try:
            await orchestration_service.generate_signal(stock, "day", "2026-01-01", get_last_trading_day())
        except Exception as e:
            print(f"Error generating signal for {stock}: {e}")
    
if __name__ == "__main__":
    asyncio.run(main())
