# tests/unit/application/test_signal_engine_service.py
"""
Tests for SignalEngineUseCases - DSL-Based Signal Construction

These tests verify that SignalEngineUseCases correctly builds signals
based on StrategyEngine evaluation results and explicit DSL actions.
"""
import pytest
import math
from uuid import UUID
from app.domain.use_cases.signal_engine_use_cases import SignalEngineUseCases
from app.application.dto.indicators_dto import IndicatorDataPoint


# Test UUID for strategy identification
TEST_STRATEGY_ID = UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def signal_engine():
    """Fixture providing SignalEngineUseCases instance"""
    return SignalEngineUseCases()


@pytest.fixture
def valid_indicator_point():
    """Fixture providing a valid indicator data point"""
    return IndicatorDataPoint(
        timestamp=1234567890000,
        symbol="AAPL",
        rsi=25.0,
        macd=0.9,
        macd_signal=0.8,
        ema=145.0,
        sma=140.0,
        histogram=0.1,
        close_price=150.0,
        fibonacci_levels={"0.236": 145.0, "0.5": 147.5, "0.618": 149.0}
    )


class TestSignalEngineServiceBuySignals:
    """Tests for BUY signal generation with explicit DSL action"""

    def test_buy_when_condition_met_and_action_buy(self, signal_engine, valid_indicator_point):
        """Should return BUY when condition_met=True and action=buy"""
        signalpoint = signal_engine.calculate_single_signal(
            symbol="AAPL",
            point=valid_indicator_point,
            prev_point=None,
            strategy_id=TEST_STRATEGY_ID,
            condition_met=True,
            action="buy",
            strategy_name="RSI Oversold Buy"
        )
        
        assert signalpoint.signal == "buy"
        assert signalpoint.strategy_id == TEST_STRATEGY_ID
        assert "BUY:" in signalpoint.reason
        assert "conditions met" in signalpoint.reason
        assert signalpoint.stop_loss < signalpoint.take_profit  # Buy: SL < TP


class TestSignalEngineServiceSellSignals:
    """Tests for SELL signal generation with explicit DSL action"""

    def test_sell_when_condition_met_and_action_sell(self, signal_engine, valid_indicator_point):
        """Should return SELL when condition_met=True and action=sell"""
        signalpoint = signal_engine.calculate_single_signal(
            symbol="AAPL",
            point=valid_indicator_point,
            prev_point=None,
            strategy_id=TEST_STRATEGY_ID,
            condition_met=True,
            action="sell",
            strategy_name="RSI Overbought Sell"
        )
        
        assert signalpoint.signal == "sell"
        assert signalpoint.strategy_id == TEST_STRATEGY_ID
        assert "SELL:" in signalpoint.reason
        assert "conditions met" in signalpoint.reason
        assert signalpoint.stop_loss > signalpoint.take_profit  # Sell: SL > TP


class TestSignalEngineServiceHoldSignals:
    """Tests for HOLD signal generation"""

    def test_hold_when_condition_not_met(self, signal_engine, valid_indicator_point):
        """Should return HOLD when condition_met=False regardless of action"""
        signalpoint = signal_engine.calculate_single_signal(
            symbol="AAPL",
            point=valid_indicator_point,
            prev_point=None,
            strategy_id=TEST_STRATEGY_ID,
            condition_met=False,  # Condition not met
            action="buy",  # Action would be buy, but condition is false
            strategy_name="RSI Oversold Buy"
        )
        
        assert signalpoint.signal == "hold"
        assert signalpoint.strategy_id == TEST_STRATEGY_ID
        assert "HOLD:" in signalpoint.reason
        assert "conditions not met" in signalpoint.reason

    def test_hold_when_action_is_hold(self, signal_engine, valid_indicator_point):
        """Should return HOLD when action=hold even if condition_met=True"""
        signalpoint = signal_engine.calculate_single_signal(
            symbol="AAPL",
            point=valid_indicator_point,
            prev_point=None,
            strategy_id=TEST_STRATEGY_ID,
            condition_met=True,
            action="hold",
            strategy_name="Wait Strategy"
        )
        
        assert signalpoint.signal == "hold"
        assert "HOLD:" in signalpoint.reason


class TestSignalEngineServiceEdgeCases:
    """Tests for edge cases"""

    def test_hold_when_any_value_is_none(self, signal_engine):
        """Should return HOLD when any required value is None"""
        current_point = IndicatorDataPoint(
            timestamp=1234567890000,
            symbol="AAPL",
            rsi=None,  # None value
            macd=0.9,
            macd_signal=0.8,
            ema=145.0,
            sma=140.0,
            histogram=0.1,
            close_price=150.0,
            fibonacci_levels={}
        )
        
        signalpoint = signal_engine.calculate_single_signal(
            symbol="AAPL",
            point=current_point,
            prev_point=None,
            strategy_id=TEST_STRATEGY_ID,
            condition_met=True,
            action="buy",
            strategy_name="Test Strategy"
        )
        
        assert signalpoint.signal == "hold"
        assert "Insufficient or invalid" in signalpoint.reason
        assert signalpoint.strategy_id == TEST_STRATEGY_ID

    def test_hold_when_any_value_is_nan(self, signal_engine):
        """Should return HOLD when any required value is NaN"""
        current_point = IndicatorDataPoint(
            timestamp=1234567890000,
            symbol="AAPL",
            rsi=25.0,
            macd=float('nan'),  # NaN value
            macd_signal=0.8,
            ema=145.0,
            sma=140.0,
            histogram=0.1,
            close_price=145.0,
            fibonacci_levels={}
        )
        
        signalpoint = signal_engine.calculate_single_signal(
            symbol="AAPL",
            point=current_point,
            prev_point=None,
            strategy_id=TEST_STRATEGY_ID,
            condition_met=True,
            action="buy",
            strategy_name="Test Strategy"
        )
        
        assert signalpoint.signal == "hold"
        assert "Insufficient or invalid" in signalpoint.reason
        assert signalpoint.strategy_id == TEST_STRATEGY_ID

    def test_fibonacci_levels_used_for_sl_tp(self, signal_engine):
        """Should use Fibonacci levels for dynamic SL/TP calculation"""
        current_point = IndicatorDataPoint(
            timestamp=1234567890000,
            symbol="AAPL",
            rsi=25.0,
            macd=0.9,
            macd_signal=0.8,
            ema=145.0,
            sma=140.0,
            histogram=0.1,
            close_price=150.0,
            fibonacci_levels={
                "0.236": 145.0,
                "0.382": 147.0,
                "0.5": 147.5,
                "0.618": 149.0
            }
        )
        
        signalpoint = signal_engine.calculate_single_signal(
            symbol="AAPL",
            point=current_point,
            prev_point=None,
            strategy_id=TEST_STRATEGY_ID,
            condition_met=True,
            action="buy",
            strategy_name="Test Strategy"
        )
        
        # With buy action, SL should be nearest support (fibonacci level below price)
        # TP should be nearest resistance (fibonacci level above price)
        assert signalpoint.stop_loss > 0
        assert signalpoint.take_profit > 0
        assert signalpoint.signal == "buy"

    def test_fallback_sl_tp_without_fibonacci(self, signal_engine):
        """Should use 5% fallback when Fibonacci levels are empty"""
        current_point = IndicatorDataPoint(
            timestamp=1234567890000,
            symbol="AAPL",
            rsi=25.0,
            macd=0.9,
            macd_signal=0.8,
            ema=145.0,
            sma=140.0,
            histogram=0.1,
            close_price=100.0,
            fibonacci_levels={}  # Empty Fibonacci levels
        )
        
        signalpoint = signal_engine.calculate_single_signal(
            symbol="AAPL",
            point=current_point,
            prev_point=None,
            strategy_id=TEST_STRATEGY_ID,
            condition_met=True,
            action="buy",
            strategy_name="Test Strategy"
        )
        
        # Fallback: 5% calculation
        expected_sl = 95.0  # 100 * 0.95
        expected_tp = 105.0  # 100 * 1.05
        assert signalpoint.stop_loss == expected_sl
        assert signalpoint.take_profit == expected_tp


class TestSignalEngineServiceStrategyTraceability:
    """Tests for signal traceability with strategy_id"""

    def test_signal_includes_strategy_id(self, signal_engine, valid_indicator_point):
        """All signals must include the strategy_id for traceability"""
        signalpoint = signal_engine.calculate_single_signal(
            symbol="AAPL",
            point=valid_indicator_point,
            prev_point=None,
            strategy_id=TEST_STRATEGY_ID,
            condition_met=True,
            action="buy",
            strategy_name="Test Strategy"
        )
        
        assert signalpoint.strategy_id is not None
        assert signalpoint.strategy_id == TEST_STRATEGY_ID

    def test_signal_includes_strategy_name_in_reason(self, signal_engine, valid_indicator_point):
        """Signal reason should include strategy name for context"""
        signalpoint = signal_engine.calculate_single_signal(
            symbol="AAPL",
            point=valid_indicator_point,
            prev_point=None,
            strategy_id=TEST_STRATEGY_ID,
            condition_met=True,
            action="buy",
            strategy_name="My Custom Strategy"
        )
        
        assert "My Custom Strategy" in signalpoint.reason
