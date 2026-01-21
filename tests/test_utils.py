# tests/test_utils.py
import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

from app.utils.market_utils import process_market_results, get_paginated_results, get_top_assets
from app.utils.date_utils import get_last_trading_day, is_trading_day, get_previous_trading_days
from app.utils.cache_utils import TTLCache, market_cache, cached


class TestMarketUtils:
    """Test market utility functions"""
    
    def test_process_market_results_valid_data(self):
        """Test processing valid market results"""
        raw_data = [
            {"T": "AAPL", "o": 100.0, "c": 105.0, "h": 106.0, "l": 99.0, "v": 1000000, "vw": 102.5},
            {"T": "MSFT", "o": 200.0, "c": 195.0, "h": 201.0, "l": 194.0, "v": 500000}
        ]
        
        result = process_market_results(raw_data)
        
        assert len(result) == 2
        assert result[0]["symbol"] == "AAPL"
        assert result[0]["change"] == 5.0
        assert result[0]["change_percent"] == 5.0
        assert result[1]["symbol"] == "MSFT"
        assert result[1]["change"] == -5.0
        assert result[1]["change_percent"] == -2.5
    
    def test_process_market_results_missing_fields(self):
        """Test processing results with missing fields"""
        raw_data = [
            {"T": "AAPL", "o": 100.0, "c": 105.0, "v": 1000000},  # Missing h, l
            {"T": "INVALID", "o": 100.0},  # Missing required fields
            {"T": "MSFT", "o": 200.0, "c": 195.0, "v": 500000, "h": 201.0, "l": 194.0}
        ]
        
        result = process_market_results(raw_data)
        
        # Should only process valid entries
        assert len(result) == 2
        assert result[0]["symbol"] == "AAPL"
        assert result[0]["high"] == 105.0  # Should default to close
        assert result[0]["low"] == 105.0   # Should default to close
        assert result[1]["symbol"] == "MSFT"
    
    def test_process_market_results_zero_division(self):
        """Test handling zero division for open price"""
        raw_data = [
            {"T": "AAPL", "o": 0.0, "c": 105.0, "v": 1000000}
        ]
        
        result = process_market_results(raw_data)
        
        assert len(result) == 1
        assert result[0]["change_percent"] == 0  # Should handle zero division
    
    def test_process_market_results_with_max_limit(self):
        """Test processing with max results limit"""
        raw_data = [
            {"T": f"STOCK{i}", "o": 100.0, "c": 105.0, "v": 1000000}
            for i in range(10)
        ]
        
        result = process_market_results(raw_data, max_results=5)
        
        assert len(result) == 5
    
    def test_get_paginated_results(self):
        """Test pagination functionality"""
        data = list(range(20))
        
        # Test with offset and limit
        result = get_paginated_results(data, offset=5, limit=10)
        assert result == list(range(5, 15))
        
        # Test with only offset
        result = get_paginated_results(data, offset=15)
        assert result == list(range(15, 20))
        
        # Test with no parameters
        result = get_paginated_results(data)
        assert result == data
    
    def test_get_top_assets(self):
        """Test getting top gainers, losers, and most active"""
        processed_results = [
            {"symbol": "AAPL", "change_percent": 5.0, "volume": 1000000},
            {"symbol": "MSFT", "change_percent": -3.0, "volume": 2000000},
            {"symbol": "GOOGL", "change_percent": 10.0, "volume": 500000},
            {"symbol": "TSLA", "change_percent": -8.0, "volume": 3000000}
        ]
        
        result = get_top_assets(processed_results, top_n=2)
        
        assert len(result["top_gainers"]) == 2
        assert result["top_gainers"][0]["symbol"] == "GOOGL"  # Highest gain
        assert result["top_gainers"][1]["symbol"] == "AAPL"
        
        assert len(result["top_losers"]) == 2
        assert result["top_losers"][0]["symbol"] == "TSLA"  # Highest loss
        assert result["top_losers"][1]["symbol"] == "MSFT"
        
        assert len(result["most_active"]) == 2
        assert result["most_active"][0]["symbol"] == "TSLA"  # Highest volume
        assert result["most_active"][1]["symbol"] == "MSFT"


class TestDateUtils:
    """Test date utility functions"""
    
    @patch('app.utils.date_utils.datetime')
    def test_get_last_trading_day_monday(self, mock_datetime):
        """Test getting last trading day when today is Monday"""
        # Monday 2023-01-02
        mock_datetime.utcnow.return_value = datetime(2023, 1, 2)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        result = get_last_trading_day()
        
        # Should be Friday 2022-12-30 (previous year due to New Year's)
        assert result == "2022-12-30"
    
    @patch('app.utils.date_utils.datetime')
    def test_get_last_trading_day_tuesday(self, mock_datetime):
        """Test getting last trading day when today is Tuesday"""
        # Tuesday 2023-01-03
        mock_datetime.utcnow.return_value = datetime(2023, 1, 3)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        result = get_last_trading_day()
        
        # Should be Monday 2023-01-02
        assert result == "2023-01-02"
    
    @patch('app.utils.date_utils.datetime')
    def test_get_last_trading_day_saturday(self, mock_datetime):
        """Test getting last trading day when today is Saturday"""
        # Saturday 2023-01-07
        mock_datetime.utcnow.return_value = datetime(2023, 1, 7)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        result = get_last_trading_day()
        
        # Should be Friday 2023-01-06
        assert result == "2023-01-06"
    
    @patch('app.utils.date_utils.datetime')
    def test_get_last_trading_day_sunday(self, mock_datetime):
        """Test getting last trading day when today is Sunday"""
        # Sunday 2023-01-08
        mock_datetime.utcnow.return_value = datetime(2023, 1, 8)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        result = get_last_trading_day()
        
        # Should be Friday 2023-01-06
        assert result == "2023-01-06"
    
    def test_is_trading_day_weekday(self):
        """Test checking if weekday is trading day"""
        monday = datetime(2023, 1, 2)   # Monday
        wednesday = datetime(2023, 1, 4) # Wednesday
        friday = datetime(2023, 1, 6)    # Friday
        
        assert is_trading_day(monday) is True
        assert is_trading_day(wednesday) is True
        assert is_trading_day(friday) is True
    
    def test_is_trading_day_weekend(self):
        """Test checking if weekend is not trading day"""
        saturday = datetime(2023, 1, 7)  # Saturday
        sunday = datetime(2023, 1, 8)    # Sunday
        
        assert is_trading_day(saturday) is False
        assert is_trading_day(sunday) is False
    
    @patch('app.utils.date_utils.datetime')
    def test_get_previous_trading_days(self, mock_datetime):
        """Test getting previous N trading days"""
        # Wednesday 2023-01-04
        mock_datetime.utcnow.return_value = datetime(2023, 1, 4)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        result = get_previous_trading_days(3)
        
        # Should be Tue, Mon, Fri (skipping weekend)
        expected = ["2023-01-03", "2023-01-02", "2022-12-30"]
        assert result == expected


class TestCacheUtils:
    """Test cache utility functions"""
    
    @pytest.fixture
    def cache(self):
        """Create a test cache instance"""
        return TTLCache(ttl_seconds=1)
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, cache):
        """Test setting and getting cache values"""
        await cache.set("test_method", "test_value", "arg1", key1="value1")
        
        result = await cache.get("test_method", "arg1", key1="value1")
        assert result == "test_value"
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, cache):
        """Test cache miss returns None"""
        result = await cache.get("nonexistent_method", "arg1")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache):
        """Test cache expiration after TTL"""
        await cache.set("test_method", "test_value", "arg1")
        
        # Should be available immediately
        result = await cache.get("test_method", "arg1")
        assert result == "test_value"
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired
        result = await cache.get("test_method", "arg1")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_clear(self, cache):
        """Test clearing cache"""
        await cache.set("method1", "value1", "arg1")
        await cache.set("method2", "value2", "arg1")
        
        assert await cache.get("method1", "arg1") == "value1"
        assert await cache.get("method2", "arg1") == "value2"
        
        await cache.clear()
        
        assert await cache.get("method1", "arg1") is None
        assert await cache.get("method2", "arg1") is None
    
    @pytest.mark.asyncio
    async def test_cache_clear_pattern(self, cache):
        """Test clearing cache by pattern"""
        await cache.set("method1", "value1", "arg1")
        await cache.set("method2", "value2", "arg1")
        await cache.set("other_method", "value3", "arg1")
        
        await cache.clear_pattern("method")
        
        assert await cache.get("method1", "arg1") is None
        assert await cache.get("method2", "arg1") is None
        assert await cache.get("other_method", "arg1") == "value3"
    
    def test_cache_stats(self, cache):
        """Test getting cache statistics"""
        # Initially empty
        stats = cache.get_stats()
        assert stats["total_entries"] == 0
        assert stats["ttl_seconds"] == 1
        assert stats["keys"] == []
        
        # Add entries (synchronously for test)
        cache._cache["key1"] = {"value": "value1", "timestamp": time.time()}
        cache._cache["key2"] = {"value": "value2", "timestamp": time.time()}
        
        stats = cache.get_stats()
        assert stats["total_entries"] == 2
        assert len(stats["keys"]) == 2
    
    def test_cache_key_generation(self, cache):
        """Test cache key generation"""
        key1 = cache._generate_key("method", "arg1", key1="value1")
        key2 = cache._generate_key("method", "arg1", key1="value1")
        key3 = cache._generate_key("method", "arg2", key1="value1")
        
        assert key1 == key2
        assert key1 != key3
        assert "method" in key1
        assert "arg1" in key1
        assert "key1=value1" in key1
    
    @pytest.mark.asyncio
    async def test_cached_decorator(self):
        """Test cached decorator functionality"""
        call_count = 0
        
        @cached(ttl_seconds=1)
        async def test_function(self, arg1, arg2=None):
            nonlocal call_count
            call_count += 1
            return f"result_{arg1}_{arg2}"
        
        # First call should execute function
        result1 = await test_function(None, "test", arg2="value")
        assert result1 == "result_test_value"
        assert call_count == 1
        
        # Second call should use cache
        result2 = await test_function(None, "test", arg2="value")
        assert result2 == "result_test_value"
        assert call_count == 1  # Should not increment
        
        # Different args should execute function
        result3 = await test_function(None, "different", arg2="value")
        assert result3 == "result_different_value"
        assert call_count == 2
