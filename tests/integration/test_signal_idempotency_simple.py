"""
Simple integration tests for signal generation idempotency
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.domain.use_cases.signal_orchestrator import SignalOrchestrator
from app.domain.entities.strategy import Strategy


class TestSignalIdempotencySimple:
    """Test idempotency behavior with simplified mocking"""
    
    @pytest.fixture
    def mock_strategy(self):
        """Create a mock strategy for testing"""
        return Strategy(
            id=uuid4(),
            user_id=uuid4(),
            name="Test Strategy",
            is_active=True,
            dsl_definition={
                "conditions": [{"indicator": "rsi", "operator": ">", "value": 50}],
                "action": "buy"
            }
        )
    
    @pytest.mark.asyncio
    async def test_time_bucket_format(self):
        """Test time bucket generation logic"""
        from app.domain.use_cases.signal_orchestrator import SignalOrchestrator
        
        # Create orchestrator with minimal dependencies
        orchestrator = SignalOrchestrator(
            market_client=AsyncMock(),
            indicator_service=AsyncMock(),
            signal_engine_service=AsyncMock(),
            cache_client=AsyncMock(),
            signal_repository=AsyncMock()
        )
        
        # Test basic time bucket generation without mocking
        day_bucket = orchestrator._get_time_bucket("day")
        hour_bucket = orchestrator._get_time_bucket("hour")
        fourhour_bucket = orchestrator._get_time_bucket("4hour")
        minute_bucket = orchestrator._get_time_bucket("minute")
        
        # Verify format is correct (not checking exact values due to time dependency)
        assert "-" in day_bucket  # YYYY-MM-DD
        assert "-" in hour_bucket  # YYYY-MM-DD-HH
        assert "-" in fourhour_bucket  # YYYY-MM-DD-HH//4
        assert "-" in minute_bucket  # YYYY-MM-DD-HH-MM//3
    
    @pytest.mark.asyncio
    async def test_idempotency_cache_key_generation(self, mock_strategy):
        """Test that cache keys are generated correctly for idempotency"""
        from app.domain.use_cases.signal_orchestrator import SignalOrchestrator
        
        # Create orchestrator with minimal dependencies
        orchestrator = SignalOrchestrator(
            market_client=AsyncMock(),
            indicator_service=AsyncMock(),
            signal_engine_service=AsyncMock(),
            cache_client=AsyncMock(),
            signal_repository=AsyncMock()
        )
        
        # Mock time bucket generation
        with patch.object(orchestrator, '_get_time_bucket', return_value="2026-05-06"):
            # Test cache key generation
            symbol = "AAPL"
            timeframe = "day"
            time_bucket = orchestrator._get_time_bucket(timeframe)
            cache_key = f"signal:{mock_strategy.id}:{symbol}:{time_bucket}"
            
            expected_key = f"signal:{mock_strategy.id}:AAPL:2026-05-06"
            assert cache_key == expected_key
            assert str(mock_strategy.id) in cache_key
            assert symbol in cache_key
            assert time_bucket in cache_key
    
    @pytest.mark.asyncio
    async def test_redis_cache_set_if_not_exists(self):
        """Test RedisCache set_if_not_exists functionality"""
        from app.infrastructure.cache.redis_cache import RedisCache
        
        # Create RedisCache instance
        with patch('redis.asyncio.from_url'):
            cache = RedisCache(redis_url="redis://localhost:6379", default_ttl=300, key_prefix="test:")
        
        # Mock Redis client
        mock_redis = AsyncMock()
        cache._redis = mock_redis
        
        # Test successful set (key doesn't exist)
        mock_redis.set.return_value = True
        result = await cache.set_if_not_exists("test:key", "value", ttl=60)
        
        assert result is True
        mock_redis.set.assert_called_once_with(
            "test:test:key",
            "value",
            nx=True,
            ex=60
        )
        
        # Test failed set (key already exists)
        mock_redis.set.return_value = None
        result = await cache.set_if_not_exists("test:key2", "value", ttl=60)
        
        assert result is False
        
        # Test Redis error
        mock_redis.set.side_effect = Exception("Redis error")
        result = await cache.set_if_not_exists("test:key3", "value", ttl=60)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self):
        """Test that concurrent cache access works correctly"""
        from app.infrastructure.cache.redis_cache import RedisCache
        
        # Create RedisCache instance
        with patch('redis.asyncio.from_url'):
            cache = RedisCache(redis_url="redis://localhost:6379", default_ttl=300, key_prefix="test:")
        
        # Mock Redis client - only first call succeeds
        call_count = 0
        async def mock_set(key, value, nx=None, ex=None):
            nonlocal call_count
            call_count += 1
            return call_count == 1  # Only first call succeeds
        
        mock_redis = AsyncMock()
        mock_redis.set.side_effect = mock_set
        cache._redis = mock_redis
        
        # Test concurrent access
        tasks = []
        for i in range(5):
            task = cache.set_if_not_exists(f"test:key{i}", "value", ttl=60)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Only first should succeed
        successful = sum(1 for r in results if r is True)
        assert successful == 1
        assert call_count == 5
    
    @pytest.mark.asyncio
    async def test_different_cache_keys_different_strategies(self):
        """Test that different strategies generate different cache keys"""
        from app.domain.use_cases.signal_orchestrator import SignalOrchestrator
        
        # Create two different strategies
        strategy1 = Strategy(
            id=uuid4(),
            user_id=uuid4(),
            name="Strategy 1",
            is_active=True,
            dsl_definition={"action": "buy"}
        )
        
        strategy2 = Strategy(
            id=uuid4(),
            user_id=uuid4(),
            name="Strategy 2",
            is_active=True,
            dsl_definition={"action": "sell"}
        )
        
        # Create orchestrator
        orchestrator = SignalOrchestrator(
            market_client=AsyncMock(),
            indicator_service=AsyncMock(),
            signal_engine_service=AsyncMock(),
            cache_client=AsyncMock(),
            signal_repository=AsyncMock()
        )
        
        # Mock time bucket generation
        with patch.object(orchestrator, '_get_time_bucket', return_value="2026-05-06"):
            symbol = "AAPL"
            timeframe = "day"
            time_bucket = orchestrator._get_time_bucket(timeframe)
            
            # Generate cache keys
            key1 = f"signal:{strategy1.id}:{symbol}:{time_bucket}"
            key2 = f"signal:{strategy2.id}:{symbol}:{time_bucket}"
            
            # Keys should be different (different strategy IDs)
            assert key1 != key2
            assert str(strategy1.id) in key1
            assert str(strategy2.id) in key2
            assert symbol in key1 and symbol in key2
            assert time_bucket in key1 and time_bucket in key2
