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

from app.core.logging_config import get_logger, log_operation

logger = get_logger(__name__)
SessionLocal = sessionmaker(class_=Session, autocommit=False, autoflush=False, bind=engine)

async def run_signal_job():
    """Run signal generation job for all default stocks"""
    logger.info("Signal generation job started", component="signal_worker")
    
    try:
        market_client = PolygonMarketClient()
        settings = get_settings()
        cache_repository = RedisCache(redis_url=settings.REDIS_URL)
        indicator_service = IndicatorsUseCases(cache_repository)
        signal_engine = SignalEngineUseCases()

        lock_key = "signal_job_lock"
        lock_value = await cache_repository.acquire_lock(lock_key, ttl=180)

        if not lock_value:
            logger.warning("Signal job already running, skipping...", lock_key=lock_key)
            return

        logger.info("Signal job lock acquired", lock_key=lock_key, lock_value=lock_value)

        
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
                logger.info("No evaluation targets found, skipping execution", component="signal_worker")
                return
            
            logger.info(
                "Evaluation targets generated",
                component="signal_worker",
                target_count=len(targets),
                total_stocks=sum(t.stock_count for t in targets)
            )
            
            for i, target in enumerate(targets):
                logger.info(
                    "Target details",
                    component="signal_worker",
                    target_index=i+1,
                    stock_count=target.stock_count,
                    sample_stocks=target.stocks[:5]
                )
            
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
                logger.info(
                    "Target execution started",
                    component="signal_worker",
                    target_index=target_idx+1,
                    total_targets=len(targets),
                    stock_count=target.stock_count
                )
                
                for stock in target.stocks:
                    try:
                        logger.debug(
                            "Signal generation started",
                            component="signal_worker",
                            target_index=target_idx+1,
                            symbol=stock
                        )
                        
                        # Still using legacy method which uses default strategy (system default DSL-based)
                        # In future, this can be changed to use generate_signals_for_user with specific user_id
                        signal = await orchestration_service.generate_signal(
                            stock, "day", "2026-01-01", get_last_trading_day()
                        )
                        
                        logger.info(
                            "Signal generated successfully",
                            component="signal_worker",
                            target_index=target_idx+1,
                            symbol=stock,
                            signal_generated=True
                        )
                    except Exception as e:
                        logger.error(
                            "Signal generation failed",
                            component="signal_worker",
                            target_index=target_idx+1,
                            symbol=stock,
                            error_type=type(e).__name__,
                            error_message=str(e)
                        )
                        
                logger.info(
                    "Target execution completed",
                    component="signal_worker",
                    target_index=target_idx+1
                )
                    
    except Exception as e:
        logger.error(
            "Critical error in signal job",
            component="signal_worker",
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise
    finally:
        logger.info("Signal generation job completed", component="signal_worker")
        await cache_repository.release_lock(lock_key, lock_value)
        logger.info("Signal job lock released", component="signal_worker", lock_key=lock_key)
