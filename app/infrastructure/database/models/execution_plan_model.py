# app/infrastructure/database/models/execution_plan_model.py
"""
ExecutionPlan SQLModel for Database Persistence

SQLModel implementation for ExecutionPlan entity using PostgreSQL.
Stores execution plan configuration in the database.
"""

import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel

from app.domain.entities.execution_plan import ExecutionPlan


class ExecutionPlanModel(SQLModel, table=True):
    """
    SQLModel for ExecutionPlan entity.
    
    Maps to the execution_plans table in PostgreSQL.
    """
    
    __tablename__ = "execution_plans"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    strategy_id: uuid.UUID = Field(foreign_key="strategies.id", nullable=False)
    stocks: List[str] = Field(sa_column=Column(JSON), default_factory=list)
    timeframe: str = Field(default="day", max_length=20)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @classmethod
    def from_entity(cls, plan: ExecutionPlan) -> "ExecutionPlanModel":
        """Create SQLModel from domain entity."""
        return cls(
            id=plan.id,
            user_id=plan.user_id,
            strategy_id=plan.strategy_id,
            stocks=plan.stocks,
            timeframe=plan.timeframe,
            is_active=plan.is_active,
            created_at=plan.created_at,
            updated_at=plan.updated_at
        )
    
    def to_entity(self) -> ExecutionPlan:
        """Convert SQLModel to domain entity."""
        return ExecutionPlan(
            id=self.id,
            user_id=self.user_id,
            strategy_id=self.strategy_id,
            stocks=self.stocks,
            timeframe=self.timeframe,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
