# app/domain/entities/execution_plan.py
"""
ExecutionPlan Entity

Represents a plan to execute a specific strategy on a set of stocks.
Phase 2: Database abstraction for strategy execution configuration.
"""

import uuid
from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel, Field


class ExecutionPlan(BaseModel):
    """
    Execution Plan entity defining strategy execution configuration.
    
    This entity represents a plan to execute a specific strategy on a set of stocks.
    It serves as the database abstraction for the execution system in Phase 2.
    
    Attributes:
        id: Unique identifier for the execution plan
        user_id: Owner of this execution plan (required for ownership/auditing)
        strategy_id: Strategy to execute (required - no implicit defaults)
        stocks: List of stock symbols to evaluate (must have at least 1)
        timeframe: Timeframe for execution (optional, defaults to "day")
        is_active: Whether this plan is active for execution
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique identifier")
    user_id: uuid.UUID = Field(..., description="Owner of this execution plan")
    strategy_id: uuid.UUID = Field(..., description="Strategy to execute")
    stocks: List[str] = Field(..., min_length=1, description="Stock symbols to evaluate")
    timeframe: str = Field(default="day", description="Timeframe for execution")
    is_active: bool = Field(default=True, description="Whether this plan is active")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")
    
    @property
    def stock_count(self) -> int:
        """Number of stocks in this execution plan."""
        return len(self.stocks)
