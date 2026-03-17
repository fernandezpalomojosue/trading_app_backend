"""
Test script to verify Redis cache functionality
"""
import pytest
import pytest_asyncio
import asyncio
import sys
import os

# Add to project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.infrastructure.cache.redis_cache import RedisMarketCache
from app.infrastructure.cache.memory_cache import MemoryMarketCache


@pytest.mark.asyncio
async def test_redis_cache():
    """Test Redis cache functionality"""
    print("🧪 Testing Redis cache...")
    
    try:
        # Initialize Redis cache
        redis_cache = RedisMarketCache("redis://localhost:6379/0")
        
        # Test set and get
        await redis_cache.set("test_key", {"message": "Hello Redis!"}, ttl=60)
        result = await redis_cache.get("test_key")
        
        if result and result.get("message") == "Hello Redis!":
            print("✅ Redis cache test passed!")
        else:
            print("❌ Redis cache test failed!")
            return False
        
        # Test stats
        stats = redis_cache.get_stats()
        print(f"📊 Cache stats: {stats}")
        
        # Cleanup
        await redis_cache.delete("test_key")
        await redis_cache.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Redis cache test failed: {e}")
        return False


@pytest.mark.asyncio
async def test_memory_cache():
    """Test memory cache for comparison"""
    print("🧪 Testing memory cache...")
    
    try:
        # Initialize memory cache
        memory_cache = MemoryMarketCache()
        
        # Test set and get
        await memory_cache.set("test_key", {"message": "Hello Memory!"}, ttl=60)
        result = await memory_cache.get("test_key")
        
        if result and result.get("message") == "Hello Memory!":
            print("✅ Memory cache test passed!")
        else:
            print("❌ Memory cache test failed!")
            return False
        
        # Test stats
        stats = memory_cache.get_stats()
        print(f"📊 Cache stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Memory cache test failed: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 Starting cache tests...\n")
    
    # Test memory cache first (always works)
    memory_ok = await test_memory_cache()
    print()
    
    # Test Redis cache (requires Redis server)
    redis_ok = await test_redis_cache()
    print()
    
    # Summary
    if memory_ok and redis_ok:
        print("🎉 All cache tests passed!")
        print("✅ Ready to use Redis cache in production!")
    elif memory_ok:
        print("⚠️  Memory cache works, Redis cache failed")
        print("💡 Make sure Redis server is running:")
        print("   - Local: brew services start redis")
        print("   - Docker: docker-compose up redis")
    else:
        print("❌ Both cache implementations failed!")
    
    print("\n🔧 To switch cache types, update CACHE_TYPE in .env:")
    print("   CACHE_TYPE=memory  # Use memory cache")
    print("   CACHE_TYPE=redis   # Use Redis cache")


if __name__ == "__main__":
    asyncio.run(main())
