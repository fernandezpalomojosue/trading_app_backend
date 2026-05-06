# app/domain/entities/evaluation_target.py
"""
EvaluationTarget - Unit of Work for Signal Generation

Represents what should be evaluated during signal generation.
Phase 1: Simple collection of stocks for default strategy.
Phase 2: Includes strategy_id and timeframe for execution plan support.
"""

import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class EvaluationTarget(BaseModel):
    """
    Represents a unit of work to be evaluated by the signal generation system.
    
    Phase 2: Strategy-aware evaluation target with explicit strategy_id.
    This replaces the implicit default strategy from Phase 1.
    
    Attributes:
        strategy_id: Strategy ID to execute (required - no implicit defaults)
        stocks: List of stock symbols to evaluate
        timeframe: Optional timeframe for execution (defaults to "day")
        
    Example:
        >>> target = EvaluationTarget(
        ...     strategy_id=uuid.UUID("12345678-1234-5678-9abc-123456789012"),
        ...     stocks=["AAPL", "TSLA", "NVDA"],
        ...     timeframe="day"
        ... )
    """
    strategy_id: uuid.UUID = Field(
        ...,
        description="Strategy ID to execute (required - no implicit defaults)"
    )
    stocks: List[str] = Field(
        ...,
        min_length=1,
        description="Stock symbols to evaluate"
    )
    timeframe: Optional[str] = Field(
        default="day",
        description="Timeframe for execution (optional, defaults to 'day')"
    )
    
    @property
    def stock_count(self) -> int:
        """Number of stocks in this target."""
        return len(self.stocks)
