# tests/unit/application/test_indicators_dto.py
import pytest
from pydantic import ValidationError
from app.application.dto.indicators_dto import (
    CombinedIndicatorDataPoint,
    CombinedIndicatorsResponse
)


class TestCombinedIndicatorDataPoint:
    """Tests for CombinedIndicatorDataPoint DTO"""

    def test_valid_data_point(self):
        """Should create valid data point with all fields"""
        data = CombinedIndicatorDataPoint(
            t=1704067200000,
            ema=150.5,
            sma=149.8,
            rsi=65.4,
            macd=1.2,
            signal=0.8,
            histogram=0.4,
            order_signal=None
        )
        
        assert data.t == 1704067200000
        assert data.ema == 150.5
        assert data.sma == 149.8
        assert data.rsi == 65.4
        assert data.macd == 1.2
        assert data.signal == 0.8
        assert data.histogram == 0.4
        assert data.order_signal is None

    def test_optional_order_signal(self):
        """Should allow order_signal to be None by default"""
        data = CombinedIndicatorDataPoint(
            t=1704067200000,
            ema=150.5,
            sma=149.8,
            rsi=65.4,
            macd=1.2,
            signal=0.8,
            histogram=0.4
        )
        
        assert data.order_signal is None

    def test_order_signal_values(self):
        """Should accept valid order signal values"""
        for signal in ["buy", "sell", "hold", None]:
            data = CombinedIndicatorDataPoint(
                t=1704067200000,
                ema=150.5,
                sma=149.8,
                rsi=65.4,
                macd=1.2,
                signal=0.8,
                histogram=0.4,
                order_signal=signal
            )
            assert data.order_signal == signal

    def test_required_fields(self):
        """Should fail when required fields are missing"""
        with pytest.raises(ValidationError) as exc_info:
            CombinedIndicatorDataPoint(
                t=1704067200000,
                # Missing ema
                sma=149.8,
                rsi=65.4,
                macd=1.2,
                signal=0.8,
                histogram=0.4
            )
        
        assert "ema" in str(exc_info.value)

    def test_field_types(self):
        """Should enforce correct field types"""
        with pytest.raises(ValidationError) as exc_info:
            CombinedIndicatorDataPoint(
                t="invalid_timestamp",
                ema=150.5,
                sma=149.8,
                rsi=65.4,
                macd=1.2,
                signal=0.8,
                histogram=0.4
            )
        
        assert "t" in str(exc_info.value)


class TestCombinedIndicatorsResponse:
    """Tests for CombinedIndicatorsResponse DTO"""

    def test_valid_response(self):
        """Should create valid response with symbol and results"""
        data_points = [
            CombinedIndicatorDataPoint(
                t=1704067200000,
                ema=150.5,
                sma=149.8,
                rsi=65.4,
                macd=1.2,
                signal=0.8,
                histogram=0.4
            ),
            CombinedIndicatorDataPoint(
                t=1704153600000,
                ema=151.2,
                sma=150.1,
                rsi=68.9,
                macd=1.5,
                signal=0.9,
                histogram=0.6
            )
        ]
        
        response = CombinedIndicatorsResponse(
            symbol="AAPL",
            results=data_points
        )
        
        assert response.symbol == "AAPL"
        assert len(response.results) == 2
        assert response.results[0].t == 1704067200000
        assert response.results[1].t == 1704153600000

    def test_empty_results(self):
        """Should allow empty results list"""
        response = CombinedIndicatorsResponse(
            symbol="AAPL",
            results=[]
        )
        
        assert response.symbol == "AAPL"
        assert response.results == []

    def test_response_serialization(self):
        """Should serialize response to dict correctly"""
        data_point = CombinedIndicatorDataPoint(
            t=1704067200000,
            ema=150.5,
            sma=149.8,
            rsi=65.4,
            macd=1.2,
            signal=0.8,
            histogram=0.4,
            order_signal="buy"
        )
        
        response = CombinedIndicatorsResponse(
            symbol="AAPL",
            results=[data_point]
        )
        
        serialized = response.model_dump()
        
        assert serialized["symbol"] == "AAPL"
        assert len(serialized["results"]) == 1
        assert serialized["results"][0]["t"] == 1704067200000
        assert serialized["results"][0]["ema"] == 150.5
        assert serialized["results"][0]["order_signal"] == "buy"

    def test_required_symbol(self):
        """Should fail when symbol is missing"""
        with pytest.raises(ValidationError) as exc_info:
            CombinedIndicatorsResponse(
                results=[]
            )
        
        assert "symbol" in str(exc_info.value)

    def test_symbol_type(self):
        """Should enforce string type for symbol"""
        with pytest.raises(ValidationError) as exc_info:
            CombinedIndicatorsResponse(
                symbol=123,
                results=[]
            )
        
        assert "symbol" in str(exc_info.value)

    def test_response_from_dict(self):
        """Should create response from dict"""
        data = {
            "symbol": "MSFT",
            "results": [
                {
                    "t": 1704067200000,
                    "ema": 150.5,
                    "sma": 149.8,
                    "rsi": 65.4,
                    "macd": 1.2,
                    "signal": 0.8,
                    "histogram": 0.4,
                    "order_signal": None
                }
            ]
        }
        
        response = CombinedIndicatorsResponse.model_validate(data)
        
        assert response.symbol == "MSFT"
        assert len(response.results) == 1
        assert response.results[0].ema == 150.5
