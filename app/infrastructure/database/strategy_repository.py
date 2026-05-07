# app/infrastructure/database/strategy_repository.py
"""
SQL Strategy Repository Implementation

PostgreSQL implementation of StrategyRepository.
Uses SQLModel for ORM operations.
"""

import uuid
from typing import List, Optional
from sqlmodel import Session, select

from app.application.repositories.strategy_repository import StrategyRepository
from app.domain.entities.strategy import Strategy


class SQLStrategyRepository(StrategyRepository):
    """
    PostgreSQL implementation of StrategyRepository.
    
    Stores strategy DSL as JSONB in the database.
    """
    
    def __init__(self, session: Session):
        self._session = session
    
    async def create(self, strategy: Strategy) -> Strategy:
        """Create a new strategy"""
        from app.infrastructure.database.models import StrategyModel
        
        db_strategy = StrategyModel(
            id=strategy.id,
            user_id=strategy.user_id,
            name=strategy.name,
            description=strategy.description,
            is_active=strategy.is_active,
            dsl_definition=strategy.dsl_definition,
            dsl_hash=strategy.dsl_hash,
            version=strategy.version,
            created_at=strategy.created_at,
            updated_at=strategy.updated_at
        )
        
        self._session.add(db_strategy)
        self._session.commit()
        self._session.refresh(db_strategy)
        
        return self._to_entity(db_strategy)
    
    async def get_by_id(self, strategy_id: uuid.UUID) -> Optional[Strategy]:
        """Get strategy by ID"""
        from app.core.logging_config import get_logger
        from app.infrastructure.database.models import StrategyModel
        
        logger = get_logger(__name__)
        
        logger.debug(
            "SQLStrategyRepository.get_by_id started",
            component="strategy_repository",
            strategy_id=str(strategy_id),
            session_is_none=self._session is None,
            session_type=type(self._session).__name__ if self._session else "None"
        )
        
        statement = select(StrategyModel).where(StrategyModel.id == strategy_id)
        logger.debug(
            "Executing database query",
            component="strategy_repository",
            statement=str(statement)
        )
        
        result = self._session.exec(statement).first()
        logger.debug(
            "Database query executed",
            component="strategy_repository",
            result_is_none=result is None,
            result_type=type(result).__name__ if result else "None"
        )
        
        if result is None:
            logger.debug(
                "Strategy not found in database",
                component="strategy_repository",
                strategy_id=str(strategy_id)
            )
            return None
        
        strategy = self._to_entity(result)
        logger.debug(
            "Strategy converted to entity",
            component="strategy_repository",
            strategy_id=str(strategy_id),
            strategy_name=strategy.name if strategy else "None",
            strategy_type=type(strategy).__name__
        )
        
        return strategy
    
    async def get_by_user(
        self, 
        user_id: uuid.UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Strategy]:
        """Get all strategies for a user"""
        from app.infrastructure.database.models import StrategyModel
        
        statement = (
            select(StrategyModel)
            .where(StrategyModel.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(StrategyModel.created_at.desc())
        )
        
        results = self._session.exec(statement).all()
        return [self._to_entity(r) for r in results]
    
    async def update(self, strategy: Strategy) -> Strategy:
        """Update an existing strategy"""
        from app.infrastructure.database.models import StrategyModel
        
        db_strategy = self._session.get(StrategyModel, strategy.id)
        if db_strategy is None:
            raise ValueError(f"Strategy not found: {strategy.id}")
        
        # Update fields
        db_strategy.name = strategy.name
        db_strategy.description = strategy.description
        db_strategy.is_active = strategy.is_active
        db_strategy.dsl_definition = strategy.dsl_definition
        db_strategy.dsl_hash = strategy.dsl_hash
        db_strategy.version = strategy.version
        db_strategy.updated_at = strategy.updated_at
        
        self._session.add(db_strategy)
        self._session.commit()
        self._session.refresh(db_strategy)
        
        return self._to_entity(db_strategy)
    
    async def delete(self, strategy_id: uuid.UUID) -> bool:
        """Delete a strategy"""
        from app.infrastructure.database.models import StrategyModel
        
        db_strategy = self._session.get(StrategyModel, strategy_id)
        if db_strategy is None:
            return False
        
        self._session.delete(db_strategy)
        self._session.commit()
        
        return True
    
    def _to_entity(self, db_strategy) -> Strategy:
        """Convert database model to domain entity"""
        return Strategy(
            id=db_strategy.id,
            user_id=db_strategy.user_id,
            name=db_strategy.name,
            description=db_strategy.description,
            is_active=db_strategy.is_active,
            dsl_definition=db_strategy.dsl_definition,
            dsl_hash=db_strategy.dsl_hash,
            version=db_strategy.version,
            created_at=db_strategy.created_at,
            updated_at=db_strategy.updated_at
        )
