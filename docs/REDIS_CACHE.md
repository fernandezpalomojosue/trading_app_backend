# Redis Cache Integration

This project now supports both memory cache and Redis cache for market data.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install "redis[hiredis]==5.0.1"
```

### 2. Setup Redis Server

#### Option A: Local Redis (Recommended for Development)
```bash
# Install and start Redis locally
./scripts/setup_redis.sh

# Or manually:
brew install redis
brew services start redis
```

#### Option B: Docker Redis
```bash
# Start Redis with Docker Compose
docker-compose up redis

# Or start all services
docker-compose up
```

### 3. Configure Cache Type

Edit `.env` file:
```bash
# Use Redis cache
CACHE_TYPE=redis
REDIS_URL=redis://localhost:6379/0
CACHE_DEFAULT_TTL=300
CACHE_KEY_PREFIX=trading_app:

# Or use memory cache (fallback)
CACHE_TYPE=memory
```

### 4. Test Configuration
```bash
# Test cache functionality
python scripts/test_cache.py
```

## 📋 Configuration Options

### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `CACHE_TYPE` | `memory` | Cache type: `memory` or `redis` |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `CACHE_DEFAULT_TTL` | `300` | Default TTL in seconds |
| `CACHE_KEY_PREFIX` | `trading_app:` | Key prefix for Redis |

### Redis URL Examples
```bash
# Local Redis
REDIS_URL=redis://localhost:6379/0

# Redis with password
REDIS_URL=redis://:password@localhost:6379/0

# Redis Cloud
REDIS_URL=redis://username:password@host:port/0

# Docker Redis
REDIS_URL=redis://redis:6379/0
```

## 🔄 Cache Comparison

### Memory Cache
- ✅ **Pros**: Fast, no dependencies, simple
- ❌ **Cons**: Not persistent, per-process only

### Redis Cache
- ✅ **Pros**: Persistent, distributed, scalable, advanced features
- ❌ **Cons**: Requires Redis server, network latency

## 🛠️ Development Workflow

### Switching Cache Types
```bash
# Switch to Redis
sed -i 's/CACHE_TYPE=memory/CACHE_TYPE=redis/' .env

# Switch to Memory
sed -i 's/CACHE_TYPE=redis/CACHE_TYPE=memory/' .env
```

### Monitoring Cache Performance
```python
# Cache stats are available in the API response
# or check programmatically:
cache_service.get_stats()
```

### Cache Keys
Redis keys are prefixed with `trading_app:` by default:
```bash
# View all cache keys
redis-cli keys "trading_app:*"

# View specific key
redis-cli get "trading_app:market_summary_stocks"

# Clear all cache
redis-cli flushdb
```

## 🐳 Docker Usage

### Development with Docker Compose
```bash
# Start all services (PostgreSQL + Redis + API)
docker-compose up

# Start only Redis
docker-compose up redis

# View logs
docker-compose logs redis

# Stop Redis
docker-compose stop redis
```

### Production Docker
```dockerfile
# Redis is included in docker-compose.yml
# No changes needed to Dockerfile
```

## 🧪 Testing

### Run Cache Tests
```bash
# Test both cache implementations
python scripts/test_cache.py

# Run full test suite
python -m pytest tests/

# Test with Redis specifically
CACHE_TYPE=redis python -m pytest tests/
```

### Test Coverage
- ✅ Redis connection and disconnection
- ✅ Set/get/delete operations
- ✅ TTL expiration
- ✅ Pattern-based clearing
- ✅ Error handling
- ✅ Statistics tracking

## 🔧 Troubleshooting

### Common Issues

#### Redis Connection Failed
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
brew services start redis
# or
docker-compose up redis
```

#### Permission Denied
```bash
# Make scripts executable
chmod +x scripts/setup_redis.sh
chmod +x scripts/test_cache.py
```

#### Cache Not Working
```bash
# Check configuration
grep CACHE_ .env

# Test Redis connection
python scripts/test_cache.py

# Check logs
docker-compose logs redis
```

### Performance Optimization

#### Redis Configuration
```bash
# Edit redis.conf for production
# Set maxmemory policy
maxmemory 256mb
maxmemory-policy allkeys-lru
```

#### Connection Pooling
```python
# Redis client uses connection pooling by default
# Adjust pool size in RedisMarketCache if needed
```

## 📊 Monitoring

### Cache Statistics
```python
# Get cache stats
stats = cache_service.get_stats()
print(f"Hit rate: {stats['hit_rate_percent']}%")
print(f"Total requests: {stats['total_requests']}")
```

### Redis Monitoring
```bash
# Redis info
redis-cli info

# Monitor commands
redis-cli monitor

# Check memory usage
redis-cli info memory
```

## 🚀 Production Deployment

### Environment Setup
```bash
# Production .env
CACHE_TYPE=redis
REDIS_URL=redis://your-redis-host:6379/0
CACHE_DEFAULT_TTL=3600
CACHE_KEY_PREFIX=prod_trading_app:
```

### Docker Production
```yaml
# docker-compose.prod.yml
services:
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    restart: always
```

### Health Checks
```bash
# Redis health check
redis-cli ping

# Application health check
curl http://localhost:8000/health
```

## 🔄 Migration Guide

### From Memory to Redis
1. Install Redis server
2. Update `.env` with `CACHE_TYPE=redis`
3. Test with `python scripts/test_cache.py`
4. Restart application

### From Redis to Memory
1. Update `.env` with `CACHE_TYPE=memory`
2. Restart application
3. No data migration needed (fresh start)

---

**🎉 Congratulations! You now have Redis cache integration with fallback to memory cache!**
