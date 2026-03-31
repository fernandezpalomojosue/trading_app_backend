# tests/unit/use_cases/test_indicators_use_cases.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
import pandas as pd

from app.domain.use_cases.indicators_use_cases import IndicatorsUseCases
from app.application.dto.indicators_dto import IndicatorDataPoint
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
def indicators_use_cases(mock_cache):
    """Fixture for IndicatorsUseCases with mocked dependencies"""
    return IndicatorsUseCases(mock_cache)


class TestIndicatorsUseCasesDTO:
    """Tests for IndicatorsUseCases returning CombinedIndicatorsResponse"""

    @pytest.mark.asyncio
    async def test_returns_combined_indicators_response(self, indicators_use_cases):
        """Should return CombinedIndicatorsResponse DTO"""
        # Sample candlestick data for testing
        sample_data = [
            {"t": 1704067200000, "c": 150.0, "h": 152.0, "l": 148.0, "o": 149.0, "v": 1000},
            {"t": 1704153600000, "c": 151.5, "h": 153.0, "l": 149.0, "o": 150.5, "v": 1200},
            {"t": 1704240000000, "c": 152.0, "h": 154.0, "l": 150.0, "o": 151.5, "v": 900},
            {"t": 1704326400000, "c": 150.5, "h": 152.5, "l": 148.5, "o": 152.0, "v": 1100},
            {"t": 1704412800000, "c": 153.0, "h": 155.0, "l": 151.0, "o": 150.5, "v": 1300},
            {"t": 1704499200000, "c": 154.5, "h": 156.0, "l": 152.5, "o": 153.0, "v": 1400},
            {"t": 1704585600000, "c": 155.0, "h": 157.0, "l": 153.0, "o": 154.5, "v": 1500},
            {"t": 1704672000000, "c": 156.5, "h": 158.0, "l": 154.5, "o": 155.0, "v": 1600},
            {"t": 1704758400000, "c": 157.0, "h": 159.0, "l": 155.0, "o": 156.5, "v": 1700},
            {"t": 1704844800000, "c": 158.5, "h": 160.0, "l": 156.5, "o": 157.0, "v": 1800},
            {"t": 1704931200000, "c": 159.0, "h": 161.0, "l": 157.0, "o": 158.5, "v": 1900},
            {"t": 1705017600000, "c": 160.5, "h": 162.0, "l": 158.0, "o": 159.0, "v": 2000},
            {"t": 1705104000000, "c": 161.0, "h": 163.0, "l": 159.0, "o": 160.5, "v": 2100},
            {"t": 1705190400000, "c": 162.5, "h": 164.0, "l": 160.0, "o": 161.0, "v": 2200},
            {"t": 1705276800000, "c": 163.0, "h": 165.0, "l": 161.0, "o": 162.5, "v": 2300},
            {"t": 1705363200000, "c": 164.5, "h": 166.0, "l": 162.0, "o": 163.0, "v": 2400},
            {"t": 1705449600000, "c": 165.0, "h": 167.0, "l": 163.0, "o": 164.5, "v": 2500},
            {"t": 1705536000000, "c": 166.5, "h": 168.0, "l": 164.0, "o": 165.0, "v": 2600},
            {"t": 1705622400000, "c": 167.0, "h": 169.0, "l": 165.0, "o": 166.5, "v": 2700},
            {"t": 1705708800000, "c": 168.5, "h": 170.0, "l": 166.0, "o": 167.0, "v": 2800},
            {"t": 1705795200000, "c": 169.0, "h": 171.0, "l": 167.0, "o": 168.5, "v": 2900},
            {"t": 1705881600000, "c": 170.5, "h": 172.0, "l": 168.0, "o": 169.0, "v": 3000},
            {"t": 1705968000000, "c": 171.0, "h": 173.0, "l": 169.0, "o": 170.5, "v": 3100},
            {"t": 1706054400000, "c": 172.5, "h": 174.0, "l": 170.0, "o": 171.0, "v": 3200},
            {"t": 1706140800000, "c": 173.0, "h": 175.0, "l": 171.0, "o": 172.5, "v": 3300},
            {"t": 1706227200000, "c": 174.5, "h": 176.0, "l": 172.0, "o": 173.0, "v": 3400},
            {"t": 1706313600000, "c": 175.0, "h": 177.0, "l": 173.0, "o": 174.5, "v": 3500},
            {"t": 1706400000000, "c": 176.5, "h": 178.0, "l": 174.0, "o": 175.0, "v": 3600},
            {"t": 1706486400000, "c": 177.0, "h": 179.0, "l": 175.0, "o": 176.5, "v": 3700},
            {"t": 1706572800000, "c": 178.5, "h": 180.0, "l": 176.0, "o": 177.0, "v": 3800},
            {"t": 1706659200000, "c": 179.0, "h": 181.0, "l": 177.0, "o": 178.5, "v": 3900},
            {"t": 1706745600000, "c": 180.5, "h": 182.0, "l": 178.0, "o": 179.0, "v": 4000},
            {"t": 1706832000000, "c": 181.0, "h": 183.0, "l": 179.0, "o": 180.5, "v": 4100},
            {"t": 1706918400000, "c": 182.5, "h": 184.0, "l": 180.0, "o": 181.0, "v": 4200},
            {"t": 1707004800000, "c": 183.0, "h": 185.0, "l": 181.0, "o": 182.5, "v": 4300},
            {"t": 1707091200000, "c": 184.5, "h": 186.0, "l": 182.0, "o": 183.0, "v": 4400},
            {"t": 1707177600000, "c": 185.0, "h": 187.0, "l": 183.0, "o": 184.5, "v": 4500},
            {"t": 1707264000000, "c": 186.5, "h": 188.0, "l": 184.0, "o": 185.0, "v": 4600},
            {"t": 1707350400000, "c": 187.0, "h": 189.0, "l": 185.0, "o": 186.5, "v": 4700},
            {"t": 1707436800000, "c": 188.5, "h": 190.0, "l": 186.0, "o": 187.0, "v": 4800},
            {"t": 1707523200000, "c": 189.0, "h": 191.0, "l": 187.0, "o": 188.5, "v": 4900},
            {"t": 1707609600000, "c": 190.5, "h": 192.0, "l": 188.0, "o": 189.0, "v": 5000}
        ]
        
        result = await indicators_use_cases.get_indicators(
            symbol="AAPL",
            data=sample_data,
            window=14,
            fast=12,
            slow=26,
            signal=9,
            timespan="day",
            start_date="2025-01-01",
            end_date="2025-03-01"
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Verify all data points have required fields
        for point in result:
            assert isinstance(point, IndicatorDataPoint)
            assert 'timestamp' in point.model_dump()
            assert 'ema' in point.model_dump()
            assert 'sma' in point.model_dump()
            assert 'rsi' in point.model_dump()
            assert 'macd' in point.model_dump()
            assert 'macd_signal' in point.model_dump()
            assert 'histogram' in point.model_dump()
            assert 'symbol' in point.model_dump()
            assert 'fibonacci_levels' in point.model_dump()

    @pytest.mark.asyncio
    async def test_response_structure_matches_dto(self, indicators_use_cases):
        """Should return data that can be serialized to JSON"""
        result = await indicators_use_cases.get_indicators(
            symbol="AAPL",
            data=[],
            window=14,
            fast=12,
            slow=26,
            signal=9,
            timespan="day"
        )
        
        if len(result) > 0:
            first_result = result[0]
            assert "timestamp" in first_result.model_dump()
            assert "ema" in first_result.model_dump()
            assert "sma" in first_result.model_dump()
            assert "rsi" in first_result.model_dump()
            assert "macd" in first_result.model_dump()
            assert "signal" in first_result.model_dump()
            assert "histogram" in first_result.model_dump()

    @pytest.mark.asyncio
    async def test_returns_dto_for_empty_data(self, indicators_use_cases, mock_market_client):
        """Should return CombinedIndicatorsResponse even when no data"""
        mock_market_client.fetch_candlestick_data = AsyncMock(return_value=[])
        
        result = await indicators_use_cases.get_indicators(
            symbol="AAPL",
            data=[],
            window=14,
            fast=12,
            slow=26,
            signal=9,
            timespan="day"
        )
        
        assert isinstance(result, list)
        assert result == []

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
            data=[],
            window=14,
            fast=12,
            slow=26,
            signal=9,
            timespan="day"
        )
        
        assert isinstance(result, list)
        assert result == []

    @pytest.mark.asyncio
    async def test_response_values_are_numeric(self, indicators_use_cases):
        """Should return numeric values for all indicator fields"""
        result = await indicators_use_cases.get_indicators(
            symbol="AAPL",
            data=[],
            window=14,
            fast=12,
            slow=26,
            signal=9,
            timespan="day"
        )
        
        for point in result:
            assert isinstance(point.model_dump()["timestamp"], int)
            assert isinstance(point.model_dump()["ema"], float)
            assert isinstance(point.model_dump()["sma"], float)
            assert isinstance(point.model_dump()["rsi"], float)
            assert isinstance(point.model_dump()["macd"], float)
            assert isinstance(point.model_dump()["signal"], float)
            assert isinstance(point.model_dump()["histogram"], float)

    @pytest.mark.asyncio
    async def test_order_signal_and_reason_are_populated(self, indicators_use_cases):
        """Should have order_signal and signal_reason populated"""
        result = await indicators_use_cases.get_indicators(
            symbol="AAPL",
            data=[],
            window=14,
            fast=12,
            slow=26,
            signal=9,
            timespan="day"
        )
        
        for point in result:
            assert point.model_dump()["order_signal"] in ["buy", "sell", "hold"]
            assert point.model_dump()["signal_reason"] is not None
            assert len(point.model_dump()["signal_reason"]) > 0
