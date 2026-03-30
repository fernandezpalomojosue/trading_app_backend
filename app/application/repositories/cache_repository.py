from abc import ABC, abstractmethod

class CacheRepository(ABC):
    @abstractmethod
    async def get(self, key: str):
        pass
    
    @abstractmethod
    async def set(self, key: str, value: dict, ttl: int = 60):
        pass