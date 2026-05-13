"""
SignalOrchestrator - DSL-Based Signal Generation

Orchestrates the signal generation process using user-defined strategies.
Generates one signal per active strategy per symbol.
"""
from typing import List, Optional
from uuid import UUID

from app.application.repositories.market_repository import MarketRepository
from app.application.services.indicators_service import IndicatorsService
from app.application.services.signal_engine_service import SignalEngineService
from app.application.repositories.signal_repository import SignalRepository
from app.application.repositories.cache_repository import CacheRepository
from app.domain.entities.market_snapshot import MarketSnapshot
from app.domain.services.strategy_engine import StrategyEngine
from app.domain.entities.strategy import Strategy
from app.application.dto.signals_dto import SignalDataPoint
from app.domain.use_cases.strategy_use_cases import StrategyUseCases
from app.core.logging_config import get_logger
from app.utils.date_utils import get_last_trading_day


class SignalOrchestrator:
    """
    Orchestrates the signal generation process.
    
    For each symbol, generates one signal per active user strategy.
    Uses StrategyEngine to evaluate DSL conditions against market data.
    """
    
    def __init__(
        self,
        market_client: MarketRepository,
        indicator_service: IndicatorsService,
        signal_engine_service: SignalEngineService,
        cache_client: CacheRepository,
        signal_repository: SignalRepository,
        strategy_use_cases: Optional[StrategyUseCases] = None
    ):
        self.logger = get_logger(__name__)
        self.market_client = market_client
        self.indicator_service = indicator_service
        self.signal_engine_service = signal_engine_service
        self.cache_client = cache_client
        self.signal_repository = signal_repository
        self.strategy_use_cases = strategy_use_cases
        self.strategy_engine = StrategyEngine()
    
    def _get_time_bucket(self, timeframe: str) -> str:
        """
        Generate time bucket based on timeframe for idempotency.
        
        Args:
            timeframe: Timeframe string (e.g., "day", "hour", "minute")
            
        Returns:
            Time bucket string for cache key
        """
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        
        if timeframe == "day":
            return now.strftime("%Y-%m-%d")
        elif timeframe == "hour":
            return now.strftime("%Y-%m-%d-%H")
        elif timeframe == "4hour":
            hour_bucket = now.hour // 4
            return now.strftime(f"%Y-%m-%d-{hour_bucket:02d}")
        elif timeframe == "minute":
            minute_bucket = now.minute // 3  # Group minutes into 3-minute buckets
            return now.strftime(f"%Y-%m-%d-%H-{minute_bucket:02d}")
        else:
            # Default to hourly for unknown timeframes
            return now.strftime("%Y-%m-%d-%H")
    
    async def generate_signal_from_snapshot(
        self,
        strategy: Strategy,
        snapshot: MarketSnapshot
    ) -> Optional[SignalDataPoint]:
        """
        Generate signal using precomputed market snapshot.
        
        Phase 4 optimized method that uses precomputed MarketSnapshot
        instead of fetching market data and computing indicators.
        
        Args:
            strategy: Strategy entity with DSL definition
            snapshot: Precomputed MarketSnapshot with indicator data
            
        Returns:
            SignalDataPoint if conditions met, None otherwise
        """
        try:
            # Validate snapshot has sufficient data
            if not snapshot.has_valid_data():
                self.logger.warning(
                    "invalid_snapshot_for_evaluation",
                    component="signal_orchestrator",
                    symbol=snapshot.symbol,
                    timeframe=snapshot.timeframe,
                    strategy_id=str(strategy.id),
                    reason="insufficient_data"
                )
                return None
            
            # Get time bucket for idempotency
            time_bucket = self._get_time_bucket(snapshot.timeframe)
            
            # Apply idempotency lock using Redis NX semantics
            idempotency_key = f"signal:{strategy.id}:{snapshot.symbol}:{time_bucket}"
            lock_acquired = await self.cache_client.set_if_not_exists(
                idempotency_key, 
                "1", 
                ttl=60
            )
            
            if not lock_acquired:
                self.logger.info(
                    "signal_already_generated",
                    component="signal_orchestrator",
                    symbol=snapshot.symbol,
                    timeframe=snapshot.timeframe,
                    strategy_id=str(strategy.id),
                    time_bucket=time_bucket,
                    idempotency_key=idempotency_key
                )
                return None
            
            # Evaluate strategy condition using full snapshot
            condition_met = self.strategy_engine.evaluate(
                strategy, snapshot
            )
            
            # Determine action based on condition
            action = strategy.dsl_definition.get("action", "hold")
            if condition_met:
                action = strategy.dsl_definition.get("action", "buy") if action == "hold" else action
            
            # Get current and previous points for signal calculation
            context = snapshot.current_point
            prev_context = snapshot.previous_point if len(snapshot.indicators) >= 2 else None
            
            # Generate signal
            signal = await self.signal_engine_service.calculate_single_signal(
                symbol=snapshot.symbol,
                point=context,
                prev_point=prev_context,
                strategy_id=strategy.id,
                condition_met=condition_met,
                action=action,
                strategy_name=strategy.name
            )
            
            if signal:
                await self.signal_repository.save_signal(
                    snapshot.symbol, signal, strategy.id
                )
                await self.cache_client.set(
                    f"signal_{snapshot.symbol}_{strategy.id}", 
                    signal.model_dump(), 
                    ttl=60
                )
                
                self.logger.info(
                    "signal_generated_from_snapshot",
                    component="signal_orchestrator",
                    symbol=snapshot.symbol,
                    timeframe=snapshot.timeframe,
                    strategy_id=str(strategy.id),
                    time_bucket=time_bucket,
                    signal_action=signal.signal,
                    signal_confidence=signal.confidence
                )
            
            return signal
            
        except Exception as e:
            self.logger.error(
                "snapshot_signal_generation_failed",
                component="signal_orchestrator",
                symbol=snapshot.symbol,
                timeframe=snapshot.timeframe,
                strategy_id=str(strategy.id),
                error_type=type(e).__name__,
                error_message=str(e)
            )
            return None