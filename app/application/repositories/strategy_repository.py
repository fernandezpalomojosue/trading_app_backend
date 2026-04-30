# app/application/repositories/strategy_repository.py
"""
Strategy Repository Interface

Abstract interface for strategy persistence.
Implementations can use PostgreSQL, Redis, or other storage.
"""

import uuid
from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.strategy import Strategy


class StrategyRepository(ABC):
    """
    Abstract repository for Strategy entity.
    
    Provides CRUD operations for trading strategies.
    """
    
    @abstractmethod
    async def create(self, strategy: Strategy) -> Strategy:
        """
        Create a new strategy.
        
        Args:
            strategy: Strategy entity to create
            
        Returns:
            Created strategy with assigned ID
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, strategy_id: uuid.UUID) -> Optional[Strategy]:
        """
        Get a strategy by ID.
        
        Args:
            strategy_id: Strategy UUID
            
        Returns:
            Strategy if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_user(
        self, 
        user_id: uuid.UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Strategy]:
        """
        Get all strategies for a user.
        
        Args:
            user_id: User UUID
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of strategies
        """
        pass
    
    @abstractmethod
    async def update(self, strategy: Strategy) -> Strategy:
        """
        Update an existing strategy.
        
        Args:
            strategy: Strategy entity with updated values
            
        Returns:
            Updated strategy
        """
        pass
    
    @abstractmethod
    async def delete(self, strategy_id: uuid.UUID) -> bool:
        """
        Delete a strategy.
        
        Args:
            strategy_id: Strategy UUID
            
        Returns:
            True if deleted, False if not found
        """
        pass
