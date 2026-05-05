# app/domain/entities/evaluation_target.py
"""
EvaluationTarget - Unit of Work for Signal Generation

Represents what should be evaluated during signal generation.
Phase 1: Simple collection of stocks for default strategy.
Future phases: Will include strategy_id, timeframe, scheduling, etc.
"""

from typing import List
from pydantic import BaseModel, Field


class EvaluationTarget(BaseModel):
    """
    Represents a unit of work to be evaluated by the signal generation system.
    
    For Phase 1, this is intentionally simple - just a collection of stocks
    to be evaluated with the default strategy. Future phases will add
    strategy_id, timeframe, scheduling, etc.
    
    Attributes:
        stocks: List of stock symbols to evaluate
        
    Example:
        >>> target = EvaluationTarget(stocks=["AAPL", "TSLA", "NVDA"])
    """
    stocks: List[str] = Field(
        ...,
        min_length=1,
        description="Stock symbols to evaluate"
    )
    
    @property
    def stock_count(self) -> int:
        """Number of stocks in this target."""
        return len(self.stocks)
