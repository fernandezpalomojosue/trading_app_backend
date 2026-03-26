# tests/unit/application/test_signal_engine_service.py
import pytest
import math
from app.application.services.signal_engine_service import SignalEngineService


@pytest.fixture
def signal_engine():
    """Fixture providing SignalEngineService instance"""
    return SignalEngineService()


class TestSignalEngineServiceBuySignals:
    """Tests for BUY signal generation"""

    def test_buy_when_all_conditions_met(self, signal_engine):
        """Should return BUY when RSI<30, MACD crosses up, price>EMA"""
        prev_point = {
            "rsi": 35, "macd": 0.5, "signal": 0.8,
            "ema": 145.0, "c": 150.0
        }
        current_point = {
            "rsi": 25, "macd": 0.9, "signal": 0.8,
            "ema": 145.0, "c": 150.0
        }
        
        result = signal_engine._calculate_single_signal(current_point, prev_point)
        assert result == "buy"


class TestSignalEngineServiceSellSignals:
    """Tests for SELL signal generation"""

    def test_sell_when_all_conditions_met(self, signal_engine):
        """Should return SELL when RSI>70, MACD crosses down, price<EMA"""
        prev_point = {
            "rsi": 65, "macd": 0.9, "signal": 0.5,
            "ema": 155.0, "c": 145.0
        }
        current_point = {
            "rsi": 75, "macd": 0.4, "signal": 0.5,
            "ema": 155.0, "c": 145.0
        }
        
        result = signal_engine._calculate_single_signal(current_point, prev_point)
        assert result == "sell"


class TestSignalEngineServiceCalculateSignals:
    """Tests for calculate_signals method"""

    def test_first_point_is_always_hold(self, signal_engine):
        """First data point should be HOLD (no previous point for crossover)"""
        data = [{"rsi": 25, "macd": 0.9, "signal": 0.8, "ema": 145.0, "c": 150.0}]
        
        results = signal_engine.calculate_signals(data)
        assert results == ["hold"]

    def test_multiple_points_with_buy_and_hold(self, signal_engine):
        """Should calculate signals for multiple data points"""
        data = [
            {"rsi": 35, "macd": 0.5, "signal": 0.8, "ema": 145.0, "c": 150.0},
            {"rsi": 25, "macd": 0.9, "signal": 0.8, "ema": 145.0, "c": 150.0},
            {"rsi": 45, "macd": 1.0, "signal": 0.8, "ema": 145.0, "c": 150.0},
        ]
        
        results = signal_engine.calculate_signals(data)
        assert results == ["hold", "buy", "hold"]

    def test_empty_list_returns_empty(self, signal_engine):
        """Empty input should return empty list"""
        results = signal_engine.calculate_signals([])
        assert results == []


class TestSignalEngineServiceEdgeCases:
    """Tests for edge cases"""

    def test_hold_when_any_value_is_none(self, signal_engine):
        """Should return HOLD when any required value is None"""
        prev_point = {"rsi": 35, "macd": 0.5, "signal": 0.8, "ema": 145.0, "c": 150.0}
        current_point = {"rsi": None, "macd": 0.9, "signal": 0.8, "ema": 145.0, "c": 150.0}
        
        result = signal_engine._calculate_single_signal(current_point, prev_point)
        assert result == "hold"

    def test_hold_when_any_value_is_nan(self, signal_engine):
        """Should return HOLD when any required value is NaN"""
        prev_point = {"rsi": 35, "macd": 0.5, "signal": 0.8, "ema": 145.0, "c": 150.0}
        current_point = {"rsi": 25, "macd": float('nan'), "signal": 0.8, "ema": 145.0, "c": 150.0}
        
        result = signal_engine._calculate_single_signal(current_point, prev_point)
        assert result == "hold"
