from abc import ABC, abstractmethod
from typing import List, Optional
import uuid
from app.domain.entities.portfolio import PortfolioHolding, Transaction

class PortfolioRepository(ABC):
    """Abstract repository for portfolio operations"""
    
    @abstractmethod
    async def get_user_holdings(self, user_id: uuid.UUID) -> List[PortfolioHolding]:
        pass
    
    @abstractmethod
    async def get_user_transactions(self, user_id: uuid.UUID) -> List[Transaction]:
        pass
    
    @abstractmethod
    async def get_holding_by_symbol(self, user_id: uuid.UUID, symbol: str) -> Optional[PortfolioHolding]:
        pass
    
    @abstractmethod
    async def create_holding(self, holding: PortfolioHolding) -> PortfolioHolding:
        pass
    
    @abstractmethod
    async def update_holding(self, holding: PortfolioHolding) -> PortfolioHolding:
        pass

    @abstractmethod
    async def is_a_holding(self, user_id: uuid.UUID, symbol: str) -> bool:
        pass
    
    @abstractmethod
    async def delete_holding(self, holding_id: uuid.UUID) -> bool:
        pass
    
    @abstractmethod
    async def create_transaction(self, transaction: Transaction) -> Transaction:
        pass
    
    @abstractmethod
    async def update_user_balance(self, user_id: uuid.UUID, new_balance: float) -> bool:
        pass
    
    @abstractmethod
    async def get_user_balance(self, user_id: uuid.UUID) -> float:
        pass
