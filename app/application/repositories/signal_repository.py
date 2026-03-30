from abc import ABC, abstractmethod
from app.domain.entities.signal_stock import SignalStockEntity

class SignalRepository(ABC):

    @abstractmethod
    async def save_signal(self, symbol: str, signal: dict)-> SignalStockEntity:
        pass
