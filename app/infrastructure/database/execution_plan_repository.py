# app/infrastructure/database/execution_plan_repository.py
"""
SQL ExecutionPlan Repository Implementation

PostgreSQL implementation of ExecutionPlanRepository.
Uses SQLModel for ORM operations.
"""

import uuid
from typing import List, Optional

from sqlmodel import Session, select

from app.application.repositories.execution_plan_repository import ExecutionPlanRepository
from app.domain.entities.execution_plan import ExecutionPlan
from app.infrastructure.database.db_models.execution_plan_model import ExecutionPlanModel


class SQLExecutionPlanRepository(ExecutionPlanRepository):
    """
    PostgreSQL implementation of ExecutionPlanRepository.
    
    Stores execution plans in the database using SQLModel.
    """
    
    def __init__(self, session: Session):
        self._session = session
    
    async def get_active_plans(self) -> List[ExecutionPlan]:
        """Get all active execution plans."""
        stmt = select(ExecutionPlanModel).where(ExecutionPlanModel.is_active == True)
        result = await self._session.exec(stmt)
        models = result.all()
        return [model.to_entity() for model in models]
    
    async def create(self, plan: ExecutionPlan) -> ExecutionPlan:
        """Create a new execution plan."""
        model = ExecutionPlanModel.from_entity(plan)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return model.to_entity()
    
    async def update(self, plan: ExecutionPlan) -> ExecutionPlan:
        """Update an existing execution plan."""
        stmt = select(ExecutionPlanModel).where(ExecutionPlanModel.id == plan.id)
        result = await self._session.exec(stmt)
        model = result.first()
        
        if not model:
            raise ValueError(f"ExecutionPlan with id {plan.id} not found")
        
        # Update fields
        model.user_id = plan.user_id
        model.strategy_id = plan.strategy_id
        model.stocks = plan.stocks
        model.timeframe = plan.timeframe
        model.is_active = plan.is_active
        model.updated_at = plan.updated_at
        
        await self._session.commit()
        await self._session.refresh(model)
        return model.to_entity()
    
    async def get_by_id(self, plan_id: uuid.UUID) -> Optional[ExecutionPlan]:
        """Get execution plan by ID."""
        stmt = select(ExecutionPlanModel).where(ExecutionPlanModel.id == plan_id)
        result = await self._session.exec(stmt)
        model = result.first()
        return model.to_entity() if model else None
    
    async def get_by_user_id(self, user_id: uuid.UUID) -> List[ExecutionPlan]:
        """Get all execution plans for a specific user."""
        stmt = select(ExecutionPlanModel).where(ExecutionPlanModel.user_id == user_id)
        result = await self._session.exec(stmt)
        models = result.all()
        return [model.to_entity() for model in models]
    
    async def delete(self, plan_id: uuid.UUID) -> bool:
        """Delete an execution plan."""
        stmt = select(ExecutionPlanModel).where(ExecutionPlanModel.id == plan_id)
        result = await self._session.exec(stmt)
        model = result.first()
        
        if not model:
            return False
        
        await self._session.delete(model)
        await self._session.commit()
        return True
