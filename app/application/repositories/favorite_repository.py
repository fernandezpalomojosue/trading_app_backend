# app/application/repositories/favorite_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from app.domain.entities.favorite_stock import FavoriteStockEntity


class FavoriteRepository(ABC):
    """Abstract interface for favorite stock operations"""
    
    @abstractmethod
    async def add_favorite(self, user_id: UUID, symbol: str) -> FavoriteStockEntity:
        """Add a stock to user's favorites"""
        pass
    
    @abstractmethod
    async def remove_favorite(self, user_id: UUID, symbol: str) -> Optional[FavoriteStockEntity]:
        """Remove a stock from user's favorites"""
        pass
    
    @abstractmethod
    async def get_user_favorites(self, user_id: UUID) -> List[FavoriteStockEntity]:
        """Get all favorite stocks for a user"""
        pass
    
    @abstractmethod
    async def is_favorite(self, user_id: UUID, symbol: str) -> bool:
        """Check if a stock is in user's favorites"""
        pass
    
    @abstractmethod
    async def get_favorite_by_user_and_symbol(self, user_id: UUID, symbol: str) -> Optional[FavoriteStockEntity]:
        """Get specific favorite by user and symbol"""
        pass
    
    @abstractmethod
    async def get_all_favorites(self) -> List[str]:
        """Get all favorites"""
        pass
