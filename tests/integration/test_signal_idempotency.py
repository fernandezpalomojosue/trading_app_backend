"""
Integration tests for signal generation idempotency
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.domain.use_cases.signal_orchestrator import SignalOrchestrator
from app.domain.entities.strategy import Strategy


class TestSignalIdempotencyIntegration:
    """Test idempotency behavior with concurrent executions"""
    
    @pytest.fixture
    def mock_strategy(self):
        """Create a mock strategy for testing"""
        return Strategy(
            id=uuid4(),
            user_id=uuid4(),
            name="Test Strategy",
            is_active=True,
            dsl_definition={
                "conditions": [{"indicator": "rsi", "operator": ">", "value": 50}],
                "action": "buy"
            }
        )
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Create SignalOrchestrator with mocked dependencies"""
        # Mock all dependencies
        mock_market_client = AsyncMock()
        mock_indicator_service = AsyncMock()
        mock_signal_engine = AsyncMock()
        mock_cache_client = AsyncMock()
        mock_signal_repository = AsyncMock()
        
        orchestrator = SignalOrchestrator(
            market_client=mock_market_client,
            indicator_service=mock_indicator_service,
            signal_engine_service=mock_signal_engine,
            cache_client=mock_cache_client,
            signal_repository=mock_signal_repository
        )
        
        # Mock the strategy engine evaluation
        orchestrator.strategy_engine.evaluate.return_value = True
        
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_concurrent_signal_generation_idempotency(self, mock_orchestrator, mock_strategy):
        """Test that concurrent signal generation is idempotent"""
        symbol = "AAPL"
        timeframe = "day"
        
        # Mock successful market data and indicators
        mock_orchestrator.market_client.fetch_candlestick_data.return_value = [
            {"timestamp": "2026-05-06", "open": 150, "high": 155, "low": 149, "close": 154, "volume": 1000000}
        ]
        
        mock_orchestrator.indicator_service.get_indicators.return_value = [
            {"timestamp": "2026-05-06", "rsi": 55, "macd": 0.5, "signal": 0.3}
        ]
        
        # Mock signal engine to return a signal
        mock_signal = MagicMock()
        mock_signal.model_dump.return_value = {"signal": "buy", "confidence": 0.8}
        mock_orchestrator.signal_engine_service.calculate_single_signal.return_value = mock_signal
        
        # Mock cache client to return True for first call, False for subsequent calls
        call_count = 0
        async def mock_set_if_not_exists(key, value="1", ttl=60):
            nonlocal call_count
            call_count += 1
            return call_count == 1  # Only first call succeeds
        
        mock_orchestrator.cache_client.set_if_not_exists.side_effect = mock_set_if_not_exists
        
        # Run concurrent signal generation
        tasks = []
        for _ in range(5):
            task = mock_orchestrator._evaluate_strategy_for_symbol(
                symbol, mock_strategy, timeframe, None, None
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify only one signal was generated
        successful_signals = [r for r in results if r is not None and not isinstance(r, Exception)]
        assert len(successful_signals) == 1
        
        # Verify cache_client.set_if_not_exists was called 5 times
        assert mock_orchestrator.cache_client.set_if_not_exists.call_count == 5
        
        # Verify signal repository was called only once
        assert mock_orchestrator.signal_repository.save_signal.call_count == 1
    
    @pytest.mark.asyncio
    async def test_different_time_buckets_allow_generation(self, mock_orchestrator, mock_strategy):
        """Test that different time buckets allow signal generation"""
        symbol = "AAPL"
        timeframe1 = "day"
        timeframe2 = "hour"
        
        # Mock successful market data and indicators
        mock_orchestrator.market_client.fetch_candlestick_data.return_value = [
            {"timestamp": "2026-05-06", "open": 150, "high": 155, "low": 149, "close": 154, "volume": 1000000}
        ]
        
        mock_orchestrator.indicator_service.get_indicators.return_value = [
            {"timestamp": "2026-05-06", "rsi": 55, "macd": 0.5, "signal": 0.3}
        ]
        
        # Mock signal engine to return a signal
        mock_signal = MagicMock()
        mock_signal.model_dump.return_value = {"signal": "buy", "confidence": 0.8}
        mock_orchestrator.signal_engine_service.calculate_single_signal.return_value = mock_signal
        
        # Mock cache client to always succeed (different keys)
        mock_orchestrator.cache_client.set_if_not_exists.return_value = True
        
        # Generate signals for different timeframes
        signal1 = await mock_orchestrator._evaluate_strategy_for_symbol(
            symbol, mock_strategy, timeframe1, None, None
        )
        signal2 = await mock_orchestrator._evaluate_strategy_for_symbol(
            symbol, mock_strategy, timeframe2, None, None
        )
        
        # Both should succeed (different cache keys)
        assert signal1 is not None
        assert signal2 is not None
        
        # Verify both signals were saved
        assert mock_orchestrator.signal_repository.save_signal.call_count == 2
    
    @pytest.mark.asyncio
    async def test_redis_failure_fails_open(self, mock_orchestrator, mock_strategy):
        """Test that Redis failures result in fail-open behavior"""
        symbol = "AAPL"
        timeframe = "day"
        
        # Mock successful market data and indicators
        mock_orchestrator.market_client.fetch_candlestick_data.return_value = [
            {"timestamp": "2026-05-06", "open": 150, "high": 155, "low": 149, "close": 154, "volume": 1000000}
        ]
        
        mock_orchestrator.indicator_service.get_indicators.return_value = [
            {"timestamp": "2026-05-06", "rsi": 55, "macd": 0.5, "signal": 0.3}
        ]
        
        # Mock signal engine to return a signal
        mock_signal = MagicMock()
        mock_signal.model_dump.return_value = {"signal": "buy", "confidence": 0.8}
        mock_orchestrator.signal_engine_service.calculate_single_signal.return_value = mock_signal
        
        # Mock cache client to raise exception (Redis failure)
        mock_orchestrator.cache_client.set_if_not_exists.side_effect = Exception("Redis connection failed")
        
        # Generate signal
        result = await mock_orchestrator._evaluate_strategy_for_symbol(
            symbol, mock_strategy, timeframe, None, None
        )
        
        # Should still generate signal (fail-open)
        assert result is not None
        
        # Verify signal was saved
        assert mock_orchestrator.signal_repository.save_signal.call_count == 1
    
    @pytest.mark.asyncio
    async def test_different_strategies_different_cache_keys(self, mock_orchestrator):
        """Test that different strategies use different cache keys"""
        strategy1 = Strategy(
            id=uuid4(),
            user_id=uuid4(),
            name="Strategy 1",
            is_active=True,
            dsl_definition={"action": "buy"}
        )
        
        strategy2 = Strategy(
            id=uuid4(),
            user_id=uuid4(),
            name="Strategy 2", 
            is_active=True,
            dsl_definition={"action": "sell"}
        )
        
        symbol = "AAPL"
        timeframe = "day"
        
        # Mock successful market data and indicators
        mock_orchestrator.market_client.fetch_candlestick_data.return_value = [
            {"timestamp": "2026-05-06", "open": 150, "high": 155, "low": 149, "close": 154, "volume": 1000000}
        ]
        
        mock_orchestrator.indicator_service.get_indicators.return_value = [
            {"timestamp": "2026-05-06", "rsi": 55, "macd": 0.5, "signal": 0.3}
        ]
        
        # Mock signal engine to return a signal
        mock_signal = MagicMock()
        mock_signal.model_dump.return_value = {"signal": "buy", "confidence": 0.8}
        mock_orchestrator.signal_engine_service.calculate_single_signal.return_value = mock_signal
        
        # Mock cache client to always succeed
        mock_orchestrator.cache_client.set_if_not_exists.return_value = True
        
        # Generate signals for different strategies
        signal1 = await mock_orchestrator._evaluate_strategy_for_symbol(
            symbol, strategy1, timeframe, None, None
        )
        signal2 = await mock_orchestrator._evaluate_strategy_for_symbol(
            symbol, strategy2, timeframe, None, None
        )
        
        # Both should succeed (different cache keys due to different strategy IDs)
        assert signal1 is not None
        assert signal2 is not None
        
        # Verify both signals were saved
        assert mock_orchestrator.signal_repository.save_signal.call_count == 2
        
        # Verify cache was called with different keys
        call_args = mock_orchestrator.cache_client.set_if_not_exists.call_args_list
        key1 = call_args[0][0][0]  # First call, first argument (cache key)
        key2 = call_args[1][0][0]  # Second call, first argument (cache key)
        
        assert key1 != key2  # Different strategy IDs should create different keys
        assert str(strategy1.id) in key1
        assert str(strategy2.id) in key2
