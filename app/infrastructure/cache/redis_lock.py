import uuid
import asyncio

class RedisLock:
    def __init__(self, redis_client, key: str, ttl: int = 120):
        self.redis = redis_client
        self.key = key
        self.ttl = ttl
        self.value = str(uuid.uuid4())

    async def acquire(self) -> bool:
        return await self.redis.set(
            self.key,
            self.value,
            nx=True,   # only if not exists
            ex=self.ttl
        )

    async def release(self):
        # release only if it's OUR lock (avoid race condition)
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        await self.redis.eval(script, 1, self.key, self.value)