# app/infrastructure/cache/memory_cache.py
import re
import time
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from app.domain.use_cases.market_use_cases import MarketDataCache


class MemoryMarketCache(MarketDataCache):
    """In-memory implementation of market data cache"""
    
    def __init__(self, default_ttl: int = 300):
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self._cache:
            self._misses += 1
            return None
        
        entry = self._cache[key]
        if self._is_expired(entry):
            del self._cache[key]
            self._misses += 1
            return None
        
        self._hits += 1
        return entry["value"]
    
    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set value in cache"""
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl
        
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": time.time()
        }
    
    async def delete(self, key: str) -> None:
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]
    
    async def clear_pattern(self, pattern: str) -> None:
        """Clear keys matching pattern"""
        keys_to_delete = []
        for key in self._cache.keys():
            if re.search(pattern, key):
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self._cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        # Estimate memory usage (rough calculation)
        memory_usage = sum(len(str(entry)) for entry in self._cache.values())
        
        return {
            "entries": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2),
            "memory_usage_bytes": memory_usage,
            "memory_usage": f"{memory_usage / 1024:.2f} KB" if memory_usage > 1024 else f"{memory_usage} B"
        }
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired"""
        return time.time() > entry["expires_at"]
    
    async def clear_all(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
