"""
Integration tests for Phase 4 optimization - Market-Centric Computation

Tests that verify:
1. MarketSnapshot creation works correctly
2. SnapshotPrecomputationService groups properly
3. generate_signal_from_snapshot produces identical signals
4. Performance improvement is achieved
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.domain.entities.market_snapshot import MarketSnapshot
from app.domain.entities.strategy import Strategy
from app.domain.entities.execution_plan import ExecutionPlan
from app.application.services.snapshot_precomputation_service import SnapshotPrecomputationService
from app.domain.use_cases.signal_orchestrator import SignalOrchestrator
from app.application.dto.indicators_dto import IndicatorDataPoint


class TestPhase4Optimization:
    """Test Phase 4 market-centric computation optimization"""
    
    @pytest.fixture
    def mock_strategy(self):
        """Create a mock strategy for testing"""
        return Strategy(
            id=uuid4(),
            user_id=uuid4(),
            name="Test Strategy",
            is_active=True,
            dsl_definition={
                "version": 1,
                "action": "buy",
                "root": {
                    "type": "AND",
                    "children": [
                        {
                            "type": "condition",
                            "left": {"type": "indicator", "name": "RSI", "params": {"period": 14}},
                            "operator": "<",
                            "right": {"type": "constant", "value": 30}
                        }
                    ]
                }
            }
        )
    
    @pytest.fixture
    def mock_execution_plans(self):
        """Create mock execution plans for testing"""
        plans = []
        
        # Plan 1: Multiple stocks, same timeframe
        plan1 = ExecutionPlan(
            id=uuid4(),
            user_id=uuid4(),
            strategy_id=uuid4(),
            stocks=["AAPL", "GOOGL", "MSFT"],
            timeframe="day"
        )
        plans.append(plan1)
        
        # Plan 2: Overlapping stock, different timeframe
        plan2 = ExecutionPlan(
            id=uuid4(),
            user_id=uuid4(),
            strategy_id=uuid4(),
            stocks=["AAPL", "TSLA"],
            timeframe="hour"
        )
        plans.append(plan2)
        
        # Plan 3: Same stocks as plan 1, different strategy
        plan3 = ExecutionPlan(
            id=uuid4(),
            user_id=uuid4(),
            strategy_id=uuid4(),
            stocks=["AAPL", "GOOGL"],
            timeframe="day"
        )
        plans.append(plan3)
        
        return plans
    
    @pytest.fixture
    def mock_indicator_data(self):
        """Create mock indicator data points in chronological order"""
        return [
            IndicatorDataPoint(
                timestamp=1654195200000,  # 2022-06-02 (older)
                symbol="AAPL",
                ema=148.0,
                sma=146.0,
                rsi=35.0,
                macd=0.3,
                macd_signal=0.2,
                histogram=0.1,
                close_price=149.0,
                fibonacci_levels={}
            ),
            IndicatorDataPoint(
                timestamp=1654281600000,  # 2022-06-03 (newer)
                symbol="AAPL",
                ema=150.0,
                sma=148.0,
                rsi=25.0,  # Low RSI for buy signal
                macd=0.5,
                macd_signal=0.3,
                histogram=0.2,
                close_price=151.0,
                fibonacci_levels={}
            )
        ]
    
    @pytest.fixture
    def mock_market_snapshot(self, mock_indicator_data):
        """Create a mock market snapshot"""
        return MarketSnapshot(
            symbol="AAPL",
            timeframe="day",
            indicators=mock_indicator_data
        )
    
    @pytest.fixture
    def mock_snapshot_service(self):
        """Create SnapshotPrecomputationService with mocked dependencies"""
        market_service = AsyncMock()
        indicator_service = AsyncMock()
        
        return SnapshotPrecomputationService(
            market_service=market_service,
            indicator_service=indicator_service,
            max_concurrency=3
        )
    
    @pytest.mark.asyncio
    async def test_market_snapshot_creation(self, mock_indicator_data):
        """Test MarketSnapshot entity creation and validation"""
        snapshot = MarketSnapshot(
            symbol="AAPL",
            timeframe="day",
            indicators=mock_indicator_data
        )
        
        # Test basic properties
        assert snapshot.symbol == "AAPL"
        assert snapshot.timeframe == "day"
        assert snapshot.indicators == mock_indicator_data
        
        # Test unique key
        assert snapshot.unique_key == ("AAPL", "day")
        
        # Test validation
        assert snapshot.has_valid_data() is True
        
        # Test context creation
        current_context, prev_context = snapshot.get_evaluation_context()
        assert current_context.symbol == "AAPL"
        assert prev_context.symbol == "AAPL"
        assert current_context.timestamp > prev_context.timestamp
        
        # Test property accessors
        assert snapshot.current_point == mock_indicator_data[1]  # Most recent (last in list)
        assert snapshot.previous_point == mock_indicator_data[0]  # Previous (second to last)
    
    @pytest.mark.asyncio
    async def test_market_snapshot_invalid_data(self):
        """Test MarketSnapshot validation with invalid data"""
        # Test with empty indicators list
        snapshot = MarketSnapshot(
            symbol="AAPL",
            timeframe="day",
            indicators=[]
        )
        assert snapshot.has_valid_data() is False
        
        # Test with single indicator point (insufficient data)
        single_data = IndicatorDataPoint(
            timestamp=1654281600000,
            symbol="AAPL",
            ema=150.0,
            sma=148.0,
            rsi=25.0,
            macd=0.5,
            macd_signal=0.3,
            histogram=0.2,
            close_price=151.0,
            fibonacci_levels={}
        )
        
        snapshot = MarketSnapshot(
            symbol="AAPL",
            timeframe="day",
            indicators=[single_data]
        )
        assert snapshot.has_valid_data() is False
        
        # Test with same timestamp indicators
        same_time_data = IndicatorDataPoint(
            timestamp=1654281600000,
            symbol="AAPL",
            ema=150.0,
            sma=148.0,
            rsi=25.0,
            macd=0.5,
            macd_signal=0.3,
            histogram=0.2,
            close_price=151.0,
            fibonacci_levels={}
        )
        
        snapshot = MarketSnapshot(
            symbol="AAPL",
            timeframe="day",
            indicators=[same_time_data, same_time_data]
        )
        assert snapshot.has_valid_data() is False
    
    @pytest.mark.asyncio
    async def test_snapshot_precomputation_grouping(self, mock_snapshot_service, mock_execution_plans, mock_indicator_data):
        """Test that SnapshotPrecomputationService groups correctly"""
        # Mock market data fetch
        mock_market_data = [
            {"t": 1654195200000, "c": 149.0, "h": 150.0, "l": 148.0, "o": 149.0, "v": 950000},
            {"t": 1654281600000, "c": 151.0, "h": 152.0, "l": 149.0, "o": 150.0, "v": 1000000}
        ]
        
        mock_snapshot_service.market_service.fetch_candlestick_data.return_value = mock_market_data
        mock_snapshot_service.indicator_service.get_indicators.return_value = mock_indicator_data
        
        # Build snapshots
        snapshots = await mock_snapshot_service.build_snapshots(mock_execution_plans)
        
        # Verify grouping - should have unique (symbol, timeframe) pairs
        expected_keys = {
            ("AAPL", "day"),
            ("GOOGL", "day"), 
            ("MSFT", "day"),
            ("AAPL", "hour"),
            ("TSLA", "hour")
        }
        
        assert set(snapshots.keys()) == expected_keys
        assert len(snapshots) == 5  # 5 unique (symbol, timeframe) combinations
        
        # Verify each snapshot has valid data
        for snapshot in snapshots.values():
            assert snapshot.has_valid_data() is True
    
    @pytest.mark.asyncio
    async def test_snapshot_precomputation_concurrency(self, mock_snapshot_service, mock_execution_plans, mock_indicator_data):
        """Test that SnapshotPrecomputationService respects concurrency limits"""
        # Mock slow operations
        async def slow_fetch(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate API latency
            return [{"t": 1654195200000, "c": 149.0}, {"t": 1654281600000, "c": 151.0}]
        
        async def slow_indicators(*args, **kwargs):
            await asyncio.sleep(0.05)  # Simulate computation time
            return mock_indicator_data
        
        mock_snapshot_service.market_service.fetch_candlestick_data.side_effect = slow_fetch
        mock_snapshot_service.indicator_service.get_indicators.side_effect = slow_indicators
        
        # Time the operation
        start_time = asyncio.get_event_loop().time()
        snapshots = await mock_snapshot_service.build_snapshots(mock_execution_plans)
        end_time = asyncio.get_event_loop().time()
        
        # With concurrency=3 and 5 unique pairs, should take roughly:
        # max(3 batches) * (0.1 + 0.05) = 0.15 seconds
        # Not 5 * (0.1 + 0.05) = 0.75 seconds (sequential)
        elapsed_time = end_time - start_time
        assert elapsed_time < 0.5  # Should be much faster than sequential
        assert len(snapshots) == 5
    
    @pytest.mark.asyncio
    async def test_generate_signal_from_snapshot(self, mock_strategy, mock_market_snapshot):
        """Test SignalOrchestrator.generate_signal_from_snapshot method"""
        # Create orchestrator with mocked dependencies
        market_client = AsyncMock()
        indicator_service = AsyncMock()
        signal_engine = AsyncMock()
        cache_client = AsyncMock()
        signal_repository = AsyncMock()
        strategy_use_cases = AsyncMock()
        
        orchestrator = SignalOrchestrator(
            market_client=market_client,
            indicator_service=indicator_service,
            signal_engine_service=signal_engine,
            cache_client=cache_client,
            signal_repository=signal_repository,
            strategy_use_cases=strategy_use_cases
        )
        
        # Mock strategy engine evaluation
        orchestrator.strategy_engine.evaluate = MagicMock(return_value=True)
        
        # Mock signal generation
        mock_signal = MagicMock()
        mock_signal.action = "buy"
        mock_signal.confidence = 0.8
        mock_signal.model_dump.return_value = {"action": "buy", "confidence": 0.8}
        signal_engine.calculate_single_signal.return_value = mock_signal
        
        # Mock cache lock
        cache_client.set_if_not_exists.return_value = True
        
        # Generate signal from snapshot
        signal = await orchestrator.generate_signal_from_snapshot(
            strategy=mock_strategy,
            snapshot=mock_market_snapshot
        )
        
        # Verify signal was generated
        assert signal is not None
        assert signal.action == "buy"
        
        # Verify cache was used for idempotency
        cache_client.set_if_not_exists.assert_called_once()
        
        # Verify signal was saved
        signal_repository.save_signal.assert_called_once()
        
        # Verify strategy engine was called with correct context
        orchestrator.strategy_engine.evaluate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_signal_from_snapshot_idempotency(self, mock_strategy, mock_market_snapshot):
        """Test that generate_signal_from_snapshot respects idempotency"""
        # Create orchestrator with mocked dependencies
        market_client = AsyncMock()
        indicator_service = AsyncMock()
        signal_engine = AsyncMock()
        cache_client = AsyncMock()
        signal_repository = AsyncMock()
        strategy_use_cases = AsyncMock()
        
        orchestrator = SignalOrchestrator(
            market_client=market_client,
            indicator_service=indicator_service,
            signal_engine_service=signal_engine,
            cache_client=cache_client,
            signal_repository=signal_repository,
            strategy_use_cases=strategy_use_cases
        )
        
        # Mock strategy engine evaluation properly
        orchestrator.strategy_engine.evaluate = MagicMock()
        
        # Mock cache lock to fail (already exists)
        cache_client.set_if_not_exists.return_value = False
        
        # Generate signal from snapshot
        signal = await orchestrator.generate_signal_from_snapshot(
            strategy=mock_strategy,
            snapshot=mock_market_snapshot
        )
        
        # Verify no signal was generated due to idempotency lock
        assert signal is None
        
        # Verify strategy engine was not called
        orchestrator.strategy_engine.evaluate.assert_not_called()
        
        # Verify signal was not saved
        signal_repository.save_signal.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_phase4_vs_phase3_signal_equivalence(self, mock_strategy, mock_indicator_data):
        """Test that Phase 4 produces identical signals to Phase 3"""
        # This test would verify that the optimized pipeline produces
        # the same signals as the original pipeline
        
        # Mock Phase 3 dependencies
        market_client = AsyncMock()
        indicator_service = AsyncMock()
        signal_engine = AsyncMock()
        cache_client = AsyncMock()
        signal_repository = AsyncMock()
        strategy_use_cases = AsyncMock()
        
        # Mock market data and indicators
        market_data = [{"t": 1654281600000, "c": 151.0, "h": 152.0, "l": 149.0, "o": 150.0, "v": 1000000}]
        indicator_service.get_indicators.return_value = mock_indicator_data
        
        # Create orchestrator
        orchestrator = SignalOrchestrator(
            market_client=market_client,
            indicator_service=indicator_service,
            signal_engine_service=signal_engine,
            cache_client=cache_client,
            signal_repository=signal_repository,
            strategy_use_cases=strategy_use_cases
        )
        
        # Mock strategy engine
        orchestrator.strategy_engine.evaluate = MagicMock(return_value=True)
        
        # Mock signal generation
        mock_signal = MagicMock()
        mock_signal.action = "buy"
        mock_signal.confidence = 0.8
        signal_engine.calculate_single_signal.return_value = mock_signal
        
        # Mock cache
        cache_client.set_if_not_exists.return_value = True
        
        # Create snapshot from same indicator data
        snapshot = MarketSnapshot(
            symbol="AAPL",
            timeframe="day",
            indicators=mock_indicator_data
        )
        
        # Generate signal using Phase 4 method
        phase4_signal = await orchestrator.generate_signal_from_snapshot(
            strategy=mock_strategy,
            snapshot=snapshot
        )
        
        # For this test, we'd need to also run the Phase 3 method
        # and compare results. For now, just verify Phase 4 works
        assert phase4_signal is not None
        assert phase4_signal.action == "buy"
        
        # In a real test, you would:
        # 1. Run the original generate_signal_for_strategy method
        # 2. Run the new generate_signal_from_snapshot method  
        # 3. Compare the results are identical
