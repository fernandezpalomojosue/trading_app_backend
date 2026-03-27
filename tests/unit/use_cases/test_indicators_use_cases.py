# tests/unit/use_cases/test_indicators_use_cases.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
import pandas as pd

from app.domain.use_cases.indicators_use_cases import IndicatorsUseCases
from app.application.dto.indicators_dto import CombinedIndicatorsResponse
from app.domain.use_cases.signal_engine_use_cases import SignalEngineUseCases


@pytest.fixture
def mock_market_client():
    """Mock market client with sample candlestick data"""
    client = MagicMock()
    
    # Generate 50 days of sample data (enough for MACD with slow=26 + signal=9)
    base_timestamp = int(datetime(2024, 1, 1).timestamp() * 1000)
    sample_data = []
    
    for i in range(50):
        # Generate slightly increasing prices
        close_price = 100 + i * 0.5 + (i % 5) * 0.2
        sample_data.append({
            "t": base_timestamp + i * 86400000,  # Daily intervals
            "o": close_price - 0.5,
            "h": close_price + 1.0,
            "l": close_price - 1.0,
            "c": close_price,
            "v": 1000000 + i * 1000
        })
    
    client.fetch_candlestick_data = AsyncMock(return_value=sample_data)
    return client


@pytest.fixture
def mock_cache():
    """Mock cache service"""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    return cache


@pytest.fixture
def indicators_use_cases(mock_market_client, mock_cache):
    """Fixture for IndicatorsUseCases with mocked dependencies including signal engine"""
    return IndicatorsUseCases(mock_market_client, mock_cache)


class TestIndicatorsUseCasesDTO:
    """Tests for IndicatorsUseCases returning CombinedIndicatorsResponse"""

    @pytest.mark.asyncio
    async def test_returns_combined_indicators_response(self, indicators_use_cases, mock_market_client, mock_cache):
        """Should return CombinedIndicatorsResponse DTO"""
        result = await indicators_use_cases.get_indicators(
            symbol="AAPL",
            window=14,
            fast=12,
            slow=26,
            signal=9,
            timespan="day",
            start_date="2024-01-01",
            end_date="2024-03-01"
        )
        
        assert isinstance(result, CombinedIndicatorsResponse)
        assert result.symbol == "AAPL"
        assert len(result.results) > 0
        
        # Verify all data points have required fields
        for point in result.results:
            assert hasattr(point, 't')
            assert hasattr(point, 'ema')
            assert hasattr(point, 'sma')
            assert hasattr(point, 'rsi')
            assert hasattr(point, 'macd')
            assert hasattr(point, 'signal')
            assert hasattr(point, 'histogram')

    @pytest.mark.asyncio
    async def test_response_structure_matches_dto(self, indicators_use_cases):
        """Should return data that can be serialized to JSON"""
        result = await indicators_use_cases.get_indicators(
            symbol="AAPL",
            window=14,
            fast=12,
            slow=26,
            signal=9,
            timespan="day"
        )
        
        # Serialize and verify structure
        serialized = result.model_dump()
        
        assert "symbol" in serialized
        assert "results" in serialized
        assert isinstance(serialized["results"], list)
        
        if len(serialized["results"]) > 0:
            first_result = serialized["results"][0]
            assert "t" in first_result
            assert "ema" in first_result
            assert "sma" in first_result
            assert "rsi" in first_result
            assert "macd" in first_result
            assert "signal" in first_result
            assert "histogram" in first_result
            assert "order_signal" in first_result
            assert "signal_reason" in first_result

    @pytest.mark.asyncio
    async def test_returns_dto_for_empty_data(self, indicators_use_cases, mock_market_client):
        """Should return CombinedIndicatorsResponse even when no data"""
        mock_market_client.fetch_candlestick_data = AsyncMock(return_value=[])
        
        result = await indicators_use_cases.get_indicators(
            symbol="AAPL",
            window=14,
            fast=12,
            slow=26,
            signal=9,
            timespan="day"
        )
        
        assert isinstance(result, CombinedIndicatorsResponse)
        assert result.symbol == "AAPL"
        assert result.results == []

    @pytest.mark.asyncio
    async def test_returns_dto_for_insufficient_data(self, indicators_use_cases, mock_market_client):
        """Should return CombinedIndicatorsResponse when insufficient data for calculation"""
        # Return only 10 data points (not enough for slow=26)
        mock_market_client.fetch_candlestick_data = AsyncMock(return_value=[
            {"t": 1704067200000 + i * 86400000, "c": 100 + i} 
            for i in range(10)
        ])
        
        result = await indicators_use_cases.get_indicators(
            symbol="AAPL",
            window=14,
            fast=12,
            slow=26,
            signal=9,
            timespan="day"
        )
        
        assert isinstance(result, CombinedIndicatorsResponse)
        assert result.symbol == "AAPL"
        assert result.results == []

    @pytest.mark.asyncio
    async def test_response_values_are_numeric(self, indicators_use_cases):
        """Should return numeric values for all indicator fields"""
        result = await indicators_use_cases.get_indicators(
            symbol="AAPL",
            window=14,
            fast=12,
            slow=26,
            signal=9,
            timespan="day"
        )
        
        for point in result.results:
            assert isinstance(point.t, int)
            assert isinstance(point.ema, float)
            assert isinstance(point.sma, float)
            assert isinstance(point.rsi, float)
            assert isinstance(point.macd, float)
            assert isinstance(point.signal, float)
            assert isinstance(point.histogram, float)

    @pytest.mark.asyncio
    async def test_order_signal_and_reason_are_populated(self, indicators_use_cases):
        """Should have order_signal and signal_reason populated"""
        result = await indicators_use_cases.get_indicators(
            symbol="AAPL",
            window=14,
            fast=12,
            slow=26,
            signal=9,
            timespan="day"
        )
        
        for point in result.results:
            assert point.order_signal in ["buy", "sell", "hold"]
            assert point.signal_reason is not None
            assert len(point.signal_reason) > 0
