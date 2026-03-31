# tests/unit/application/test_signal_engine_service.py
import pytest
import math
from app.domain.use_cases.signal_engine_use_cases import SignalEngineUseCases


@pytest.fixture
def signal_engine():
    """Fixture providing SignalEngineUseCases instance"""
    return SignalEngineUseCases()


class TestSignalEngineServiceBuySignals:
    """Tests for BUY signal generation"""

    async def test_buy_when_all_conditions_met(self, signal_engine):
        """Should return BUY when RSI<30, MACD crosses up, price>EMA"""
        prev_point = {
            "rsi": 35, "macd": 0.5, "signal": 0.8,
            "ema": 145.0, "close": 150.0
        }
        current_point = {
            "rsi": 25, "macd": 0.9, "signal": 0.8,
            "ema": 145.0, "close": 150.0
        }
        
        signalpoint = await signal_engine.calculate_single_signal(symbol="AAPL", point=current_point, prev_point=prev_point)
        assert signalpoint.signal == "buy"
        assert "BUY:" in signalpoint.reason
        assert "RSI" in signalpoint.reason


class TestSignalEngineServiceSellSignals:
    """Tests for SELL signal generation"""

    async def test_sell_when_all_conditions_met(self, signal_engine):
        """Should return SELL when RSI>70, MACD crosses down, price<EMA"""
        prev_point = {
            "rsi": 65, "macd": 0.9, "signal": 0.5,
            "ema": 155.0, "close": 145.0
        }
        current_point = {
            "rsi": 75, "macd": 0.4, "signal": 0.5,
            "ema": 155.0, "close": 145.0
        }
        
        signalpoint = await signal_engine.calculate_single_signal(symbol="AAPL", point=current_point, prev_point=prev_point)
        assert signalpoint.signal == "sell"
        assert "SELL:" in signalpoint.reason
        assert "RSI" in signalpoint.reason


class TestSignalEngineServiceCalculateSignals:
    """Tests for calculate_signals method"""

    async def test_first_point_is_always_hold(self, signal_engine):
        """First data point should be HOLD (no previous point for crossover)"""
        data = [{"rsi": 25, "macd": 0.9, "signal": 0.8, "ema": 145.0, "close": 150.0}]
        
        results = await signal_engine.calculate_signals(symbol="AAPL", data_points=data)
        assert len(results) == 1
        signalpoint = results[0]
        assert signalpoint.signal == "hold"
        assert "No previous data" in signalpoint.reason

    async def test_multiple_points_with_buy_and_hold(self, signal_engine):
        """Should calculate signals for multiple data points"""
        data = [
            {"rsi": 35, "macd": 0.5, "signal": 0.8, "ema": 145.0, "close": 150.0},
            {"rsi": 25, "macd": 0.9, "signal": 0.8, "ema": 145.0, "close": 150.0},
            {"rsi": 45, "macd": 1.0, "signal": 0.8, "ema": 145.0, "close": 150.0},
        ]
        
        results = await signal_engine.calculate_signals(symbol="AAPL", data_points=data)
        assert len(results) == 3
        assert results[0].signal == "hold"  # First point is always hold
        assert results[1].signal == "buy"   # Second point meets buy conditions
        assert results[2].signal == "hold"  # Third point is hold

    async def test_empty_list_returns_empty(self, signal_engine):
        """Empty input should return empty list"""
        results = await signal_engine.calculate_signals(symbol="AAPL", data_points=[])
        assert results == []


class TestSignalEngineServiceEdgeCases:
    """Tests for edge cases"""

    async def test_hold_when_any_value_is_none(self, signal_engine):
        """Should return HOLD when any required value is None"""
        prev_point = {"rsi": 35, "macd": 0.5, "signal": 0.8, "ema": 145.0, "close": 150.0}
        current_point = {"rsi": None, "macd": 0.9, "signal": 0.8, "ema": 145.0, "close": 150.0}
        
        signalpoint = await signal_engine.calculate_single_signal(symbol="AAPL", point=current_point, prev_point=prev_point)
        assert signalpoint.signal == "hold"
        assert "Insufficient data" in signalpoint.reason

    async def test_hold_when_any_value_is_nan(self, signal_engine):
        """Should return HOLD when any required value is NaN"""
        prev_point = {"rsi": 35, "macd": 0.5, "signal": 0.8, "ema": 145.0, "close": 150.0}
        current_point = {"rsi": 25, "macd": float('nan'), "signal": 0.8, "ema": 145.0, "close": 150.0}
        
        signalpoint = await signal_engine.calculate_single_signal(symbol="AAPL", point=current_point, prev_point=prev_point)
        assert signalpoint.signal == "hold"
        assert "Insufficient data" in signalpoint.reason
