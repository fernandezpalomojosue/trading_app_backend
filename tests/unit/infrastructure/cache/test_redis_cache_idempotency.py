"""
Unit tests for RedisCache idempotency functionality
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.infrastructure.cache.redis_cache import RedisCache


class TestRedisCacheIdempotency:
    """Test RedisCache idempotency methods"""
    
    @pytest.fixture
    def redis_cache(self):
        """Create RedisCache instance for testing"""
        with patch('redis.asyncio.from_url'):
            cache = RedisCache(redis_url="redis://localhost:6379", default_ttl=300, key_prefix="test:")
            return cache
    
    @pytest.mark.asyncio
    async def test_set_if_not_exists_success(self, redis_cache):
        """Test successful set_if_not_exists when key doesn't exist"""
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True
        redis_cache._redis = mock_redis
        
        # Test the method
        result = await redis_cache.set_if_not_exists("test:key", "value", ttl=60)
        
        # Verify the call
        mock_redis.set.assert_called_once_with(
            "test:test:key",
            "value",
            nx=True,
            ex=60
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_set_if_not_exists_key_exists(self, redis_cache):
        """Test set_if_not_exists when key already exists"""
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.set.return_value = None  # Redis returns None when NX fails
        redis_cache._redis = mock_redis
        
        # Test the method
        result = await redis_cache.set_if_not_exists("test:key", "value", ttl=60)
        
        # Verify the call
        mock_redis.set.assert_called_once_with(
            "test:test:key",
            "value",
            nx=True,
            ex=60
        )
        assert result is False
    
    @pytest.mark.asyncio
    async def test_set_if_not_exists_default_values(self, redis_cache):
        """Test set_if_not_exists with default parameters"""
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True
        redis_cache._redis = mock_redis
        
        # Test with default values
        result = await redis_cache.set_if_not_exists("test:key")
        
        # Verify the call with defaults
        mock_redis.set.assert_called_once_with(
            "test:test:key",
            "1",  # Default value
            nx=True,
            ex=60  # Default TTL
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_set_if_not_exists_redis_error(self, redis_cache):
        """Test set_if_not_exists when Redis raises an exception"""
        # Mock Redis client to raise exception
        mock_redis = AsyncMock()
        mock_redis.set.side_effect = Exception("Redis connection failed")
        redis_cache._redis = mock_redis
        
        # Test the method
        result = await redis_cache.set_if_not_exists("test:key", "value", ttl=60)
        
        # Verify error handling
        assert result is False
    
    @pytest.mark.asyncio
    async def test_set_if_not_exists_lazy_initialization(self, redis_cache):
        """Test that set_if_not_exists works with lazy initialization"""
        # Mock the _get_redis method to return a mock client
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True
        
        with patch.object(redis_cache, '_get_redis', return_value=mock_redis):
            # Test the method
            result = await redis_cache.set_if_not_exists("test:key", "value", ttl=60)
            
            # Verify Redis client was used correctly
            mock_redis.set.assert_called_once_with(
                "test:test:key",
                "value",
                nx=True,
                ex=60
            )
            assert result is True


class TestSignalOrchestratorTimeBucket:
    """Test SignalOrchestrator time bucket functionality"""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Create SignalOrchestrator with mocked dependencies"""
        from app.domain.use_cases.signal_orchestrator import SignalOrchestrator
        
        # Mock all dependencies
        mock_market_client = AsyncMock()
        mock_indicator_service = AsyncMock()
        mock_signal_engine = AsyncMock()
        mock_cache_client = AsyncMock()
        mock_signal_repository = AsyncMock()
        
        orchestrator = SignalOrchestrator(
            market_client=mock_market_client,
            indicator_service=mock_indicator_service,
            signal_engine_service=mock_signal_engine,
            cache_client=mock_cache_client,
            signal_repository=mock_signal_repository
        )
        
        return orchestrator
    
    def test_get_time_bucket_day(self, mock_orchestrator):
        """Test time bucket generation for daily timeframe"""
        with patch('datetime.datetime') as mock_datetime:
            # Mock current time: 2026-05-06 14:30:00 UTC
            mock_now = MagicMock()
            mock_now.strftime.side_effect = lambda fmt: {
                "%Y-%m-%d": "2026-05-06",
                "%Y-%m-%d-%H": "2026-05-06-14",
                "%Y-%m-%d-{hour:02d}".format(hour=14//4): "2026-05-06-03"
            }[fmt]
            
            mock_datetime.now.return_value = mock_now
            
            result = mock_orchestrator._get_time_bucket("day")
            assert result == "2026-05-06"
    
    def test_get_time_bucket_hour(self, mock_orchestrator):
        """Test time bucket generation for hourly timeframe"""
        with patch('datetime.datetime') as mock_datetime:
            # Mock current time: 2026-05-06 14:30:00 UTC
            mock_now = MagicMock()
            mock_now.strftime.side_effect = lambda fmt: {
                "%Y-%m-%d": "2026-05-06",
                "%Y-%m-%d-%H": "2026-05-06-14",
                "%Y-%m-%d-{hour:02d}".format(hour=14//4): "2026-05-06-03"
            }[fmt]
            
            mock_datetime.now.return_value = mock_now
            
            result = mock_orchestrator._get_time_bucket("hour")
            assert result == "2026-05-06-14"
    
    def test_get_time_bucket_4hour(self, mock_orchestrator):
        """Test time bucket generation for 4-hour timeframe"""
        with patch('datetime.datetime') as mock_datetime:
            # Mock current time: 2026-05-06 14:30:00 UTC (14:30 is in 12:00-15:59 bucket)
            mock_now = MagicMock()
            mock_now.hour = 14
            mock_now.strftime.side_effect = lambda fmt: {
                "%Y-%m-%d": "2026-05-06",
                "%Y-%m-%d-%H": "2026-05-06-14",
                "%Y-%m-%d-{hour:02d}".format(hour=14//4): "2026-05-06-03"
            }[fmt]
            
            mock_datetime.now.return_value = mock_now
            
            result = mock_orchestrator._get_time_bucket("4hour")
            assert result == "2026-05-06-03"  # 14 // 4 = 3 (12:00-15:59 bucket)
    
    def test_get_time_bucket_4hour_boundary(self, mock_orchestrator):
        """Test 4-hour time bucket at boundary (11:59 -> 12:00)"""
        with patch('datetime.datetime') as mock_datetime:
            # Mock current time: 2026-05-06 11:59:00 UTC (11:59 is in 8:00-11:59 bucket)
            mock_now = MagicMock()
            mock_now.hour = 11
            mock_now.strftime.side_effect = lambda fmt: {
                "%Y-%m-%d": "2026-05-06",
                "%Y-%m-%d-%H": "2026-05-06-11",
                "%Y-%m-%d-{hour:02d}".format(hour=11//4): "2026-05-06-02"
            }[fmt]
            
            mock_datetime.now.return_value = mock_now
            
            result = mock_orchestrator._get_time_bucket("4hour")
            assert result == "2026-05-06-02"  # 11 // 4 = 2 (8:00-11:59 bucket)
    
    def test_get_time_bucket_unknown_timeframe(self, mock_orchestrator):
        """Test time bucket generation for unknown timeframe (defaults to hourly)"""
        with patch('datetime.datetime') as mock_datetime:
            # Mock current time: 2026-05-06 14:30:00 UTC
            mock_now = MagicMock()
            mock_now.strftime.side_effect = lambda fmt: {
                "%Y-%m-%d": "2026-05-06",
                "%Y-%m-%d-%H": "2026-05-06-14",
                "%Y-%m-%d-{hour:02d}".format(hour=14//4): "2026-05-06-03"
            }[fmt]
            
            mock_datetime.now.return_value = mock_now
            
            result = mock_orchestrator._get_time_bucket("unknown")
            assert result == "2026-05-06-14"  # Defaults to hourly
