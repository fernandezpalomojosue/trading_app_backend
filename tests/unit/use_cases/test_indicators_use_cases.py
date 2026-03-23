"""
Tests for indicators use cases
Tests EMA, SMA, RSI, and MACD indicator calculations and data retrieval
"""
import pytest
from app.domain.use_cases.indicators_use_cases import IndicatorsUseCases
from tests.fixtures.indicators_fixtures import MockIndicatorsClient
from tests.fixtures.market_fixtures import MockMarketDataCache


@pytest.mark.asyncio
class TestIndicatorsUseCases:
    """Test technical indicators use cases"""
    
    @pytest.fixture
    def mock_cache(self):
        return MockMarketDataCache()
    
    @pytest.fixture
    def mock_client(self):
        return MockIndicatorsClient()
    
    @pytest.fixture
    def indicators_use_cases(self, mock_client, mock_cache):
        return IndicatorsUseCases(mock_client, mock_cache)
    
    async def test_get_ema_returns_correct_data(self, indicators_use_cases):
        """EMA data should be returned with correct structure"""
        result = await indicators_use_cases.get_ema(
            symbol="AAPL",
            window=14,
            timespan="day",
            limit=100
        )
        
        assert result.symbol == "AAPL"
        assert result.window == 14
        assert result.timespan == "day"
        assert len(result.results) == 3
        assert result.results[0].t == 1773028800000
        assert result.results[0].v == 150.5
    
    async def test_get_sma_returns_correct_data(self, indicators_use_cases):
        """SMA data should be returned with correct structure"""
        result = await indicators_use_cases.get_sma(
            symbol="AAPL",
            window=20,
            timespan="day",
            limit=100
        )
        
        assert result.symbol == "AAPL"
        assert result.window == 20
        assert result.timespan == "day"
        assert len(result.results) == 3
        assert result.results[0].v == 148.0
    
    async def test_get_rsi_returns_correct_data(self, indicators_use_cases):
        """RSI data should be returned with correct structure"""
        result = await indicators_use_cases.get_rsi(
            symbol="AAPL",
            window=14,
            timespan="day",
            limit=100
        )
        
        assert result.symbol == "AAPL"
        assert result.window == 14
        assert len(result.results) == 3
        # RSI values should be between 0 and 100
        assert 0 <= result.results[0].v <= 100
        assert result.results[0].v == 65.5
    
    async def test_get_macd_returns_correct_data(self, indicators_use_cases):
        """MACD data should be returned with correct structure"""
        result = await indicators_use_cases.get_macd(
            symbol="AAPL",
            fast=12,
            slow=26,
            signal=9,
            timespan="day",
            limit=100
        )
        
        assert result.symbol == "AAPL"
        assert result.fast == 12
        assert result.slow == 26
        assert result.signal_period == 9
        assert len(result.results) == 3
        assert result.results[0].macd == 2.5
        assert result.results[0].signal == 1.8
        assert result.results[0].histogram == 0.7
    
    async def test_indicators_caching(self, indicators_use_cases, mock_cache):
        """Indicators should be cached after first fetch"""
        # First call - should fetch from API
        result1 = await indicators_use_cases.get_ema(
            symbol="AAPL",
            window=14,
            timespan="day"
        )
        
        # Second call - should use cache
        result2 = await indicators_use_cases.get_ema(
            symbol="AAPL",
            window=14,
            timespan="day"
        )
        
        # Both results should be identical
        assert result1.symbol == result2.symbol
        assert len(result1.results) == len(result2.results)
    
    async def test_indicators_with_date_range(self, indicators_use_cases):
        """Indicators should support date range parameters"""
        result = await indicators_use_cases.get_ema(
            symbol="AAPL",
            window=14,
            timespan="day",
            start_date="2024-01-01",
            end_date="2024-03-31",
            limit=50
        )
        
        assert result.symbol == "AAPL"
        assert len(result.results) > 0
