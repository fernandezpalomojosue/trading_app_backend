from app.domain.use_cases.indicators_use_cases import IndicatorsUseCases
from app.domain.use_cases.strategy_use_cases import StrategyUseCases
from app.infrastructure.cache.redis_cache import RedisCache
from app.infrastructure.external.market_client import PolygonMarketClient
from app.infrastructure.database.signal_repository import SQLSignalRepository
from app.infrastructure.database.execution_plan_repository import SQLExecutionPlanRepository
from app.domain.use_cases.signal_orchestrator import SignalOrchestrator
from app.domain.use_cases.signal_engine_use_cases import SignalEngineUseCases
from app.application.services.snapshot_precomputation_service import SnapshotPrecomputationService
from app.core.config import get_settings
from app.db.base import SessionLocal, engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session
from app.infrastructure.database.strategy_repository import SQLStrategyRepository


from app.core.logging_config import get_logger

logger = get_logger(__name__)
SessionLocal = sessionmaker(class_=Session, autocommit=False, autoflush=False, bind=engine)

async def run_signal_job():
    """
    This function implements the optimized pipeline that:
    1. Precomputes market snapshots once per (symbol, timeframe)
    2. Evaluates all execution plans using precomputed snapshots
    3. Eliminates redundant API calls and indicator computations
    """
    logger.info("Signal generation job started", component="signal_worker")
    
    try:
        settings = get_settings()
        cache_repository = RedisCache(redis_url=settings.REDIS_URL)
        
        lock_key = "signal_job_lock"
        lock_value = await cache_repository.acquire_lock(lock_key, ttl=180)

        if not lock_value:
            logger.warning("Signal job already running, skipping...", lock_key=lock_key)
            return

        logger.info("Signal job lock acquired", lock_key=lock_key, lock_value=lock_value)

        # Use session context manager for proper cleanup
        with SessionLocal() as session:
            signal_repository = SQLSignalRepository(session)
            execution_plan_repository = SQLExecutionPlanRepository(session)
            strategy_repository = SQLStrategyRepository(session)
            strategy_use_cases = StrategyUseCases(strategy_repository)
            
            # Create services
            market_client = PolygonMarketClient()
            indicator_service = IndicatorsUseCases(cache_repository)
            signal_engine = SignalEngineUseCases()
            
            # Create services
            snapshot_service = SnapshotPrecomputationService(
                market_service=market_client,
                indicator_service=indicator_service,
                max_concurrency=5
            )
            
            orchestrator = SignalOrchestrator(
                market_client,
                indicator_service,
                signal_engine,
                cache_repository,
                signal_repository,
                strategy_use_cases=strategy_use_cases
            )
            
            # Step 1: Load active execution plans
            logger.info("Loading active execution plans", component="signal_worker")
            plans = await execution_plan_repository.get_active_plans()
            
            if not plans:
                logger.info("No active execution plans found, skipping signal generation", component="signal_worker")
                return
            
            logger.info(
                "Active execution plans loaded",
                component="signal_worker",
                plan_count=len(plans),
                total_stocks=sum(len(plan.stocks) for plan in plans)
            )
            
            # Step 2: Precompute market snapshots
            logger.info("Starting snapshot precomputation", component="signal_worker")
            snapshots = await snapshot_service.build_snapshots(plans)
            
            if not snapshots:
                logger.warning("No valid snapshots created", component="signal_worker")
                return
            
            logger.info(
                "Snapshot precomputation completed",
                component="signal_worker",
                snapshot_count=len(snapshots),
                unique_pairs=list(snapshots.keys())
            )
            
            # Step 3: Evaluate plans using snapshots
            logger.info("Starting plan evaluation using snapshots", component="signal_worker")
            
            total_evaluations = 0
            successful_signals = 0
            
            for plan in plans:
                try:
                    # Get strategy for this plan
                    strategy = strategy_use_cases.get_strategy(plan.strategy_id)
                    
                    if not strategy:
                        logger.warning(
                            "Strategy not found for plan",
                            component="signal_worker",
                            plan_id=str(plan.id),
                            strategy_id=str(plan.strategy_id)
                        )
                        continue
                    
                    logger.info(
                        "Plan evaluation started",
                        component="signal_worker",
                        plan_id=str(plan.id),
                        strategy_id=str(plan.strategy_id),
                        stock_count=len(plan.stocks)
                    )
                    
                    # Evaluate each stock using precomputed snapshots
                    for stock in plan.stocks:
                        total_evaluations += 1
                        
                        # Get snapshot for this (symbol, timeframe)
                        snapshot_key = (stock, plan.timeframe)
                        snapshot = snapshots.get(snapshot_key)
                        
                        if not snapshot:
                            logger.warning(
                                "No snapshot available for stock",
                                component="signal_worker",
                                symbol=stock,
                                timeframe=plan.timeframe,
                                plan_id=str(plan.id)
                            )
                            continue
                        
                        try:
                            # Generate signal using precomputed snapshot
                            signal = await orchestrator.generate_signal_from_snapshot(
                                strategy=strategy,
                                snapshot=snapshot
                            )
                            
                            if signal:
                                successful_signals += 1
                                logger.info(
                                    "Signal generated from snapshot",
                                    component="signal_worker",
                                    symbol=stock,
                                    timeframe=plan.timeframe,
                                    strategy_id=str(strategy.id),
                                    signal_action=signal.signal
                                )
                            else:
                                logger.debug(
                                    "No signal generated",
                                    component="signal_worker",
                                    symbol=stock,
                                    timeframe=plan.timeframe,
                                    strategy_id=str(strategy.id)
                                )
                                
                        except Exception as e:
                            logger.error(
                                "Snapshot signal generation failed",
                                component="signal_worker",
                                symbol=stock,
                                timeframe=plan.timeframe,
                                strategy_id=str(strategy.id),
                                error_type=type(e).__name__,
                                error_message=str(e)
                            )
                    
                    logger.info(
                        "Plan evaluation completed",
                        component="signal_worker",
                        plan_id=str(plan.id),
                        strategy_id=str(plan.strategy_id)
                    )
                    
                except Exception as e:
                    logger.error(
                        "Plan evaluation failed",
                        component="signal_worker",
                        plan_id=str(plan.id),
                        strategy_id=str(plan.strategy_id),
                        error_type=type(e).__name__,
                        error_message=str(e)
                    )
            
            logger.info(
                "Phase 4 signal generation completed",
                component="signal_worker",
                total_plans=len(plans),
                total_evaluations=total_evaluations,
                successful_signals=successful_signals,
                success_rate=f"{(successful_signals/total_evaluations*100):.1f}%" if total_evaluations > 0 else "0%"
            )
                    
    except Exception as e:
        logger.error(
            "Critical error in Phase 4 signal job",
            component="signal_worker",
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise
    finally:
        logger.info("Phase 4 signal generation job completed", component="signal_worker")
        await cache_repository.release_lock(lock_key, lock_value)
        logger.info("Signal job lock released", component="signal_worker", lock_key=lock_key)
