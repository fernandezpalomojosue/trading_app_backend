from app.application.repositories.favorite_repository import FavoriteRepository
from app.domain.use_cases.indicators_use_cases import IndicatorsUseCases
from app.domain.use_cases.strategy_use_cases import StrategyUseCases
from app.infrastructure.cache.redis_cache import RedisCache
from app.infrastructure.external.market_client import PolygonMarketClient
from app.infrastructure.database.signal_repository import SQLSignalRepository
from app.infrastructure.database.favorite_repository import SQLFavoriteStockRepository
from app.infrastructure.database.strategy_repository import SQLStrategyRepository
from app.domain.use_cases.signal_orchestrator import SignalOrchestrator
from app.domain.use_cases.signal_engine_use_cases import SignalEngineUseCases
from app.application.services.evaluation_target_service import EvaluationTargetService
from app.utils.date_utils import get_last_trading_day
from app.core.config import get_settings
from app.db.base import SessionLocal, engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session
from app.infrastructure.cache.redis_lock import RedisLock

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

        lock_key = "signal_job_lock"
        lock_value = await cache_repository.acquire_lock(lock_key, ttl=180)

        if not lock_value:
            logger.warning("Signal job already running, skipping...")
            return

        logger.info("Signal job lock acquired ✅")
        print(f"Lock value: {lock_value}")

        
        # Use session context manager for proper cleanup
        with SessionLocal() as session:
            signal_repository = SQLSignalRepository(session)
            favorite_repository = SQLFavoriteStockRepository(session)
            strategy_repository = SQLStrategyRepository(session)
            strategy_use_cases = StrategyUseCases(strategy_repository)
            
            # NEW: Create evaluation target service
            target_service = EvaluationTargetService(
                favorite_repository=favorite_repository,
                settings=settings
            )
            
            # NEW: Get evaluation targets (Phase 1: returns 1 target)
            targets = await target_service.get_targets()
            
            if not targets:
                logger.info("No evaluation targets found, skipping execution")
                return
            
            logger.info(f"Generated {len(targets)} evaluation target(s)")
            for i, target in enumerate(targets):
                logger.info(f"Target {i+1}: {target.stock_count} stocks - {target.stocks[:5]}...")
            
            # Create orchestrator with strategy_use_cases for DSL-based signal generation
            orchestration_service = SignalOrchestrator(
                market_client,
                indicator_service,
                signal_engine,
                cache_repository,
                signal_repository,
                strategy_use_cases=strategy_use_cases
            )
            
            # NEW: Iterate over targets, then stocks
            for target_idx, target in enumerate(targets):
                logger.info(f"[Target {target_idx+1}/{len(targets)}] Starting execution of {target.stock_count} stocks")
                
                for stock in target.stocks:
                    try:
                        logger.info(f"[Target {target_idx+1}] Generating signal for {stock}")
                        
                        # Log before calling orchestration_service.generate_signal
                        logger.info(f"DEBUG: About to call orchestration_service.generate_signal for {stock}")
                        
                        # Still using legacy method which uses default strategy (system default DSL-based)
                        # In future, this can be changed to use generate_signals_for_user with specific user_id
                        signal = await orchestration_service.generate_signal(
                            stock, "day", "2026-01-01", get_last_trading_day()
                        )
                        
                        # Log after successful call
                        logger.info(f"DEBUG: Successfully completed orchestration_service.generate_signal for {stock}")
                        logger.info(f"Successfully generated signal for {stock}: {signal}")
                    except Exception as e:
                        logger.error(f"[Target {target_idx+1}] Error generating signal for {stock}: {e}")
                        import traceback
                        logger.error(f"TRACEBACK: {traceback.format_exc()}")
                        
                logger.info(f"[Target {target_idx+1}] Completed")
                    
    except Exception as e:
        logger.error(f"Critical error in signal job: {e}")
        raise
    finally:
        logger.info("Signal generation job completed")
        await cache_repository.release_lock(lock_key, lock_value)
        logger.info("Signal job lock released 🔄")
