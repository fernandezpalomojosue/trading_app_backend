# tests/unit/application/test_indicators_dto.py
import pytest
from pydantic import ValidationError
from app.application.dto.indicators_dto import IndicatorDataPoint


class TestIndicatorDataPoint:
    """Tests for IndicatorDataPoint DTO"""

    def test_valid_data_point(self):
        """Should create valid data point with all fields"""
        data = IndicatorDataPoint(
            timestamp=1704067200000,
            symbol="AAPL",
            ema=150.5,
            sma=149.8,
            rsi=65.4,
            macd=1.2,
            macd_signal=0.8,
            histogram=0.4,
            close_price=150.0,
            fibonacci_levels={}
        )
        
        assert data.timestamp == 1704067200000
        assert data.ema == 150.5
        assert data.sma == 149.8
        assert data.rsi == 65.4
        assert data.macd == 1.2
        assert data.macd_signal == 0.8
        assert data.histogram == 0.4
        assert data.fibonacci_levels == {}

    def test_optional_fields_default_to_none(self):
        """Should default optional fields to None when not provided"""
        data = IndicatorDataPoint(
            timestamp=1704067200000,
            symbol="AAPL"
            # All optional fields omitted
        )
        
        assert data.ema is None
        assert data.sma is None
        assert data.rsi is None
        assert data.macd is None
        assert data.macd_signal is None
        assert data.histogram is None
        assert data.close_price is None
        assert data.open_price is None
        assert data.high_price is None
        assert data.low_price is None
        assert data.volume is None
        assert data.fibonacci_levels == {}

    def test_field_types(self):
        """Should enforce correct field types"""
        with pytest.raises(ValidationError) as exc_info:
            IndicatorDataPoint(
                timestamp="invalid_timestamp",
                symbol="AAPL",
                ema=150.5,
                sma=149.8,
                rsi=65.4,
                macd=1.2,
                macd_signal=0.8,
                histogram=0.4,
                fibonacci_levels={}
            )
        
        assert "timestamp" in str(exc_info.value)


class TestIndicatorDataPointList:
    """Tests for List[IndicatorDataPoint] response"""
    
    def test_list_of_data_points(self):
        """Should create valid list of data points"""
        data_points = [
            IndicatorDataPoint(
                timestamp=1704067200000,
                symbol="AAPL",
                ema=150.5,
                sma=149.8,
                rsi=65.4,
                macd=1.2,
                macd_signal=0.8,
                histogram=0.4,
                close_price=150.0,
                fibonacci_levels={}
            ),
            IndicatorDataPoint(
                timestamp=1704153600000,
                symbol="AAPL",
                ema=151.2,
                sma=150.1,
                rsi=67.8,
                macd=1.5,
                macd_signal=1.1,
                histogram=0.6,
                close_price=151.0,
                fibonacci_levels={}
            )
        ]
        
        assert len(data_points) == 2
        assert data_points[0].ema == 150.5
        assert data_points[1].ema == 151.2
    
    def test_list_serialization(self):
        """Should serialize list of data points correctly"""
        data_point = IndicatorDataPoint(
            timestamp=1704067200000,
            symbol="AAPL",
            ema=150.5,
            sma=149.8,
            rsi=65.4,
            macd=1.2,
            macd_signal=0.8,
            histogram=0.4,
            close_price=150.0,
            fibonacci_levels={}
        )
        
        data_points = [data_point]
        serialized = [point.model_dump() for point in data_points]
        
        assert len(serialized) == 1
        assert serialized[0]["timestamp"] == 1704067200000
        assert serialized[0]["ema"] == 150.5
