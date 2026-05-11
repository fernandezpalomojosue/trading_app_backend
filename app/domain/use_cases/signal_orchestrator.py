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
from app.domain.entities.market_context import MarketContext
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
    
    async def generate_signals_for_user(
        self,
        user_id: UUID,
        symbol: str,
        timespan: str = "day",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        indicators_window: int = 30,
        indicators_fast: int = 12,
        indicators_slow: int = 26,
        indicators_signal: int = 9
    ) -> List[SignalDataPoint]:
        """
        Generate signals for a symbol using all active user strategies.
        
        Args:
            user_id: User ID to fetch strategies for
            symbol: Stock symbol
            timespan: Candlestick timespan (e.g., "day", "hour")
            start_date: Start date for data fetching
            end_date: End date for data fetching
            indicators_window: Window for indicator calculation
            indicators_fast: Fast period for MACD
            indicators_slow: Slow period for MACD
            indicators_signal: Signal period for MACD
            
        Returns:
            List of SignalDataPoint (one per active strategy)
        """
        print(f"DEBUG: Starting generate_signals_for_user for {symbol}, user={user_id}")
        
        # 1. Fetch market data
        print(f"DEBUG: Fetching candlestick data for {symbol}")
        data = await self.market_client.fetch_candlestick_data(
            symbol, timespan, 1, 100, start_date, end_date
        )
        print(f"DEBUG: Got {len(data)} records for {symbol}")
        
        # 2. Calculate indicators
        print(f"DEBUG: Calculating indicators for {symbol}")
        indicators = await self.indicator_service.get_indicators(
            symbol,
            data=data,
            window=indicators_window,
            fast=indicators_fast,
            slow=indicators_slow,
            signal=indicators_signal,
            timespan=timespan,
            start_date=start_date,
            end_date=end_date,
            limit=100
        )
        print(f"DEBUG: Calculated {len(indicators)} indicator points for {symbol}")
        
        if len(indicators) < 2:
            print(f"WARNING: Insufficient indicator data for {symbol}")
            return []
        
        # 3. Build MarketContext for current and previous points
        current_point = indicators[-1]
        prev_point = indicators[-2]
        
        context = MarketContext.from_indicator_point(current_point)
        prev_context = MarketContext.from_indicator_point(prev_point)
        
        # 4. Fetch user strategies or use default
        strategies = await self._get_strategies_for_user(user_id)
        print(f"DEBUG: Found {len(strategies)} strategies for user {user_id}")
        
        # 5. Evaluate each strategy and generate signals
        signals = []
        for strategy in strategies:
            signal = await self._evaluate_strategy(
                strategy, symbol, current_point, prev_point, context, prev_context
            )
            if signal:
                signals.append(signal)
                # Save to repository
                await self.signal_repository.save_signal(symbol, signal, strategy.id)
                # Cache the signal
                await self.cache_client.set(f"signal_{symbol}_{strategy.id}", signal.model_dump(), ttl=60)
        
        print(f"DEBUG: Generated {len(signals)} signals for {symbol}")
        return signals
    
    async def _get_strategies_for_user(self, user_id: UUID) -> List[Strategy]:
        """
        Get active strategies for a user.
        
        If user has no strategies, returns the system default strategy.
        """
        if self.strategy_use_cases:
            # Fetch user's active strategies
            strategies = await self.strategy_use_cases.get_user_active_strategies(user_id)
            if strategies:
                return strategies
        
        # Fallback to default strategy
        from app.infrastructure.database.default_strategy_seed import get_default_strategy_entity
        return [get_default_strategy_entity()]
    
    async def _evaluate_strategy(
        self,
        strategy: Strategy,
        symbol: str,
        current_point,
        prev_point,
        context: MarketContext,
        prev_context: MarketContext
    ) -> Optional[SignalDataPoint]:
        """
        Evaluate a single strategy and generate signal.
        
        Args:
            strategy: Strategy to evaluate
            symbol: Stock symbol
            current_point: Current indicator data point
            prev_point: Previous indicator data point
            context: Current market context
            prev_context: Previous market context
            
        Returns:
            SignalDataPoint or None if evaluation failed
        """
        try:
            print(f"DEBUG: Evaluating strategy '{strategy.name}' for {symbol}")
            
            # Evaluate strategy conditions using StrategyEngine
            condition_met = self.strategy_engine.evaluate(strategy, context, prev_context)
            
            # Get explicit action from strategy DSL
            action = strategy.dsl_definition.get("action", "buy")
            
            print(f"DEBUG: Strategy '{strategy.name}' - condition_met={condition_met}, action={action}")
            
            # Build signal using SignalEngineUseCases
            signal = await self.signal_engine_service.calculate_single_signal(
                symbol=symbol,
                point=current_point,
                prev_point=prev_point,
                strategy_id=strategy.id,
                condition_met=condition_met,
                action=action,
                strategy_name=strategy.name
            )
            
            self.logger.debug(
                "Signal generated",
                component="signal_orchestrator",
                symbol=symbol,
                strategy_name=strategy.name,
                signal_generated=signal.signal
            )
            return signal
            
        except Exception as e:
            self.logger.error(
                "Strategy evaluation failed",
                component="signal_orchestrator",
                symbol=symbol,
                strategy_name=strategy.name,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            return None
    
    async def generate_signal_for_strategy(
        self,
        symbol: str,
        strategy_id: UUID,
        timeframe: str = "day",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        indicators_window: int = 30,
        indicators_fast: int = 12,
        indicators_slow: int = 26,
        indicators_signal: int = 9
    ) -> Optional[SignalDataPoint]:
        """
        Generate signal for a specific strategy and symbol.
        """
        # Get strategy by ID
        strategy = await self.strategy_use_cases.get_strategy(strategy_id)
        if not strategy:
            self.logger.error(
                "Strategy not found",
                component="signal_orchestrator",
                symbol=symbol,
                strategy_id=str(strategy_id)
            )
            return None
        
        if not strategy.is_active:
            self.logger.warning(
                "Strategy is inactive",
                component="signal_orchestrator",
                symbol=symbol,
                strategy_id=str(strategy_id)
            )
            return None
        
        # Use existing evaluation logic with specific strategy
        return await self._evaluate_strategy_for_symbol(symbol, strategy, timeframe, start_date, end_date)

    async def _evaluate_strategy_for_symbol(
        self, 
        symbol: str, 
        strategy: Strategy, 
        timeframe: str,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> Optional[SignalDataPoint]:
        """Extract strategy evaluation logic into reusable method"""
        try:
            # Generate idempotency key and check for duplicates
            time_bucket = self._get_time_bucket(timeframe)
            cache_key = f"signal:{strategy.id}:{symbol}:{time_bucket}"
            
            # Try to acquire idempotency lock
            lock_acquired = await self.cache_client.set_if_not_exists(cache_key, ttl=60)
            
            if not lock_acquired:
                self.logger.info(
                    "Signal generation skipped - duplicate in progress",
                    component="signal_orchestrator",
                    strategy_id=str(strategy.id),
                    symbol=symbol,
                    timeframe=timeframe,
                    time_bucket=time_bucket
                )
                return None
            
            self.logger.debug(
                "Idempotency lock acquired",
                component="signal_orchestrator",
                strategy_id=str(strategy.id),
                symbol=symbol,
                timeframe=timeframe,
                time_bucket=time_bucket
            )
            # Fetch market data
            data = await self.market_client.fetch_candlestick_data(
                symbol, timeframe, 1, 100, start_date or "2026-01-01", end_date or get_last_trading_day()
            )
            
            # Calculate indicators
            indicators = await self.indicator_service.get_indicators(
                symbol,
                data=data,
                window=30,
                fast=12,
                slow=26,
                signal=9,
                timespan=timeframe,
                start_date=start_date or "2026-01-01",
                end_date=end_date or get_last_trading_day(),
                limit=100
            )
            
            if len(indicators) < 2:
                self.logger.warning(
                    "Insufficient indicator data",
                    component="signal_orchestrator",
                    symbol=symbol,
                    strategy_id=str(strategy.id),
                    indicator_count=len(indicators)
                )
                return None
            
            # Build MarketContext for current and previous points
            current_point = indicators[-1]
            prev_point = indicators[-2]
            
            context = MarketContext.from_indicator_point(current_point)
            prev_context = MarketContext.from_indicator_point(prev_point)
            
            # Evaluate strategy condition
            condition_met = self.strategy_engine.evaluate(
                strategy, context, prev_context
            )
            
            # Determine action based on condition
            action = strategy.dsl_definition.get("action", "hold")
            if condition_met:
                action = strategy.dsl_definition.get("action", "buy") if action == "hold" else action
            
            # Generate signal
            signal = self.signal_engine_service.calculate_single_signal(
                symbol=symbol,
                point=current_point,
                prev_point=prev_point,
                strategy_id=strategy.id,
                condition_met=condition_met,
                action=action,
                strategy_name=strategy.name
            )
            
            if signal:
                await self.signal_repository.save_signal(symbol, signal, strategy.id)
                await self.cache_client.set(f"signal_{symbol}_{strategy.id}", signal.model_dump(), ttl=60)
            
            return signal
            
        except Exception as e:
            self.logger.error(
                "Strategy evaluation failed",
                component="signal_orchestrator",
                symbol=symbol,
                strategy_id=str(strategy.id),
                timeframe=timeframe,
                time_bucket=time_bucket,
                error_type=type(e).__name__,
                error_message=str(e)
            )
    
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
            
            # Build MarketContext objects from snapshot
            context, prev_context = snapshot.get_evaluation_context()
            
            # Add MarketSnapshot reference to context for offset support
            context._market_snapshot = snapshot
            if prev_context:
                prev_context._market_snapshot = snapshot
            
            # Evaluate strategy condition
            condition_met = self.strategy_engine.evaluate(
                strategy, context, prev_context
            )
            
            # Determine action based on condition
            action = strategy.dsl_definition.get("action", "hold")
            if condition_met:
                action = strategy.dsl_definition.get("action", "buy") if action == "hold" else action
            
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