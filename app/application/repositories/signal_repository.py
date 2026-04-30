from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from app.domain.entities.signal_stock import SignalStockEntity
from app.application.dto.signals_dto import SignalDataPoint

class SignalRepository(ABC):

    @abstractmethod
    async def save_signal(
        self, 
        symbol: str, 
        signal: SignalDataPoint,
        strategy_id: Optional[UUID] = None
    ) -> SignalStockEntity:
        """
        Save a signal for a symbol.
        
        Args:
            symbol: Stock symbol
            signal: Signal data point to save
            strategy_id: Optional strategy ID that generated this signal
        """
        pass
    
    @abstractmethod
    async def get_by_symbol(self, symbol: str) -> Optional[SignalStockEntity]:
        """Get the most recent signal for a symbol"""
        pass
