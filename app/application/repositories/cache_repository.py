from abc import ABC, abstractmethod

class CacheRepository(ABC):
    @abstractmethod
    async def get(self, key: str):
        pass
    
    @abstractmethod
    async def set(self, key: str, value: dict, ttl: int = 60):
        pass
    
    @abstractmethod
    async def set_if_not_exists(self, key: str, value: any = "1", ttl: int = 60) -> bool:
        """Set key only if it doesn't exist (NX semantics). Returns True if set, False if exists."""
        pass