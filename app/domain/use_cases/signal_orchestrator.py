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
from app.domain.services.strategy_engine import StrategyEngine
from app.domain.entities.strategy import Strategy
from app.application.dto.signals_dto import SignalDataPoint
from app.domain.use_cases.strategy_use_cases import StrategyUseCases
from app.core.logging_config import get_logger


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
            signal = self.signal_engine_service.calculate_single_signal(
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
    
    async def generate_signal(
        self,
        symbol: str,
        timespan: str,
        start_date: str,
        end_date: str,
        indicators_window=30,
        indicators_fast=12,
        indicators_slow=26,
        indicators_signal=9
    ):
        """
        Legacy method for backward compatibility.
        
        Uses default strategy (system default).
        """
        from app.infrastructure.database.default_strategy_seed import get_default_strategy_entity
        
        self.logger.debug(
            "Legacy generate_signal method started",
            component="signal_orchestrator",
            symbol=symbol
        )
        
        # Fetch data
        data = await self.market_client.fetch_candlestick_data(symbol, timespan, 1, 100, start_date, end_date)
        indicators = await self.indicator_service.get_indicators(
            symbol, data=data, window=indicators_window, fast=indicators_fast,
            slow=indicators_slow, signal=indicators_signal, timespan=timespan,
            start_date=start_date, end_date=end_date, limit=100
        )
        
        if len(indicators) < 2:
            print(f"WARNING: Insufficient data for {symbol}")
            return None
        
        # Use default strategy
        default_strategy = get_default_strategy_entity()
        
        # Build contexts
        context = MarketContext.from_indicator_point(indicators[-1])
        prev_context = MarketContext.from_indicator_point(indicators[-2])
        
        # Evaluate and generate signal
        signal = await self._evaluate_strategy(
            default_strategy, symbol, indicators[-1], indicators[-2], context, prev_context
        )
        
        if signal:
            await self.signal_repository.save_signal(symbol, signal, default_strategy.id)
            await self.cache_client.set(f"signal_{symbol}", signal.model_dump(), ttl=60)
        
        return signal