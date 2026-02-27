# app/infrastructure/cache/redis_cache.py
import json
import redis.asyncio as redis
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from app.domain.use_cases.market_use_cases import MarketDataCache


class RedisMarketCache(MarketDataCache):
    """Redis implementation of market data cache"""
    
    def __init__(self, redis_url: str, default_ttl: int = 300, key_prefix: str = "market:"):
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self._redis = None
        self._redis_url = redis_url
        self._hits = 0
        self._misses = 0
    
    async def _get_redis(self):
        """Get Redis connection (lazy initialization)"""
        if self._redis is None:
            self._redis = await redis.from_url(self._redis_url, decode_responses=True)
        return self._redis
    
    def _make_key(self, key: str) -> str:
        """Add prefix to key"""
        return f"{self.key_prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        try:
            redis_client = await self._get_redis()
            redis_key = self._make_key(key)
            
            value = await redis_client.get(redis_key)
            if value is None:
                self._misses += 1
                return None
            
            self._hits += 1
            return json.loads(value) if value else None
            
        except Exception as e:
            print(f"Redis get error: {e}")
            self._misses += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in Redis cache with TTL"""
        try:
            redis_client = await self._get_redis()
            redis_key = self._make_key(key)
            
            serialized_value = json.dumps(value, default=str)
            await redis_client.setex(redis_key, ttl or self.default_ttl, serialized_value)
            
        except Exception as e:
            print(f"Redis set error: {e}")
    
    async def delete(self, key: str) -> None:
        """Delete key from Redis cache"""
        try:
            redis_client = await self._get_redis()
            redis_key = self._make_key(key)
            await redis_client.delete(redis_key)
            
        except Exception as e:
            print(f"Redis delete error: {e}")
    
    async def clear_pattern(self, pattern: str) -> None:
        """Clear keys matching pattern"""
        try:
            redis_client = await self._get_redis()
            redis_pattern = self._make_key(pattern)
            
            keys = await redis_client.keys(redis_pattern)
            if keys:
                await redis_client.delete(*keys)
                
        except Exception as e:
            print(f"Redis clear pattern error: {e}")
    
    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_type": "redis"
        }
