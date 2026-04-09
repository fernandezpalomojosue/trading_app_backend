from app.application.repositories.favorite_repository import FavoriteRepository
from app.domain.use_cases.indicators_use_cases import IndicatorsUseCases
from app.infrastructure.cache.redis_cache import RedisCache
from app.infrastructure.external.market_client import PolygonMarketClient
from app.infrastructure.database.signal_repository import SQLSignalRepository
from app.infrastructure.database.favorite_repository import SQLFavoriteStockRepository
from app.domain.use_cases.signal_orchestrator import SignalOrchestrator
from app.domain.use_cases.signal_engine_use_cases import SignalEngineUseCases
from app.utils.date_utils import get_last_trading_day
from app.core.config import get_settings
from app.db.base import SessionLocal, engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

import logging

logger = logging.getLogger(__name__)
SessionLocal = sessionmaker(class_=Session, autocommit=False, autoflush=False, bind=engine)

async def run_signal_job():
    """Run signal generation job for all default stocks"""
    print("Signal worker started")
    logger.info("Signal generation job started")
    
    try:
        market_client = PolygonMarketClient()
        settings = get_settings()
        cache_repository = RedisCache(redis_url=settings.REDIS_URL)
        indicator_service = IndicatorsUseCases(cache_repository)
        signal_engine = SignalEngineUseCases()
        
        # Use session context manager for proper cleanup
        with SessionLocal() as session:
            signal_repository = SQLSignalRepository(session)
            favorite_repository = SQLFavoriteStockRepository(session)
            
            # Get default stocks from environment or use fallback
            default_stocks = getattr(settings, 'DEFAULT_SIGNAL_STOCKS', 'AAPL,GOOGL,MSFT,TSLA,NVDA')
            
            # Try to get favorites from database, fallback to default stocks
            stocks = favorite_repository.get_all_favorites()
            
            # If no favorites found, use default stocks
            if not stocks:
                stocks = default_stocks.split(',') if isinstance(default_stocks, str) else default_stocks
                logger.info(f"No favorites found, using default stocks: {stocks}")
            else:
                logger.info(f"Using favorites from database: {stocks}")
            
            orchestration_service = SignalOrchestrator(
                market_client,
                indicator_service,
                signal_engine,
                cache_repository,
                signal_repository
            )
            
            for stock in stocks:
                try:
                    logger.info(f"Generating signal for {stock}")
                    
                    # Log before calling orchestration_service.generate_signal
                    logger.info(f"DEBUG: About to call orchestration_service.generate_signal for {stock}")
                    
                    signal = await orchestration_service.generate_signal(
                        stock, "day", "2026-01-01", get_last_trading_day()
                    )
                    
                    # Log after successful call
                    logger.info(f"DEBUG: Successfully completed orchestration_service.generate_signal for {stock}")
                    logger.info(f"Successfully generated signal for {stock}: {signal}")
                except Exception as e:
                    logger.error(f"Error generating signal for {stock}: {e}")
                    import traceback
                    logger.error(f"TRACEBACK: {traceback.format_exc()}")
                    
    except Exception as e:
        logger.error(f"Critical error in signal job: {e}")
        raise
    finally:
        logger.info("Signal generation job completed")
