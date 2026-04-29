# app/domain/services/strategy_engine.py
"""
Strategy Engine Placeholder

Interface for future strategy evaluation engine.
Implementation deferred to Sprint 2.

This module defines the contract for:
- DSL evaluation (recursive AST traversal)
- Market context integration
- Indicator calculation
- Signal generation
"""

from typing import Any, Dict
from app.domain.entities.strategy import Strategy
from app.domain.entities.strategy_dsl import StrategyDSL


class StrategyEngine:
    """
    Strategy Evaluation Engine - Placeholder.
    
    This class will be implemented in Sprint 2 to:
    1. Evaluate DSL conditions against market data
    2. Generate trading signals
    3. Support backtesting
    
    Current implementation raises NotImplementedError to prevent
    accidental usage before full implementation.
    """
    
    def evaluate(self, strategy: Strategy, context: Dict[str, Any] = None) -> None:
        """
        Evaluate a strategy against market context.
        
        Args:
            strategy: Strategy entity with DSL definition
            context: Market context with OHLCV data, indicators, etc.
            
        Raises:
            NotImplementedError: Engine implementation in Sprint 2
        """
        raise NotImplementedError(
            "StrategyEngine.evaluate() implementation deferred to Sprint 2. "
            "Current sprint focuses on DSL definition and validation only."
        )
    
    def evaluate_dsl(self, dsl: StrategyDSL, context: Dict[str, Any] = None) -> None:
        """
        Evaluate a DSL definition directly.
        
        Args:
            dsl: StrategyDSL object
            context: Market context with OHLCV data, indicators, etc.
            
        Raises:
            NotImplementedError: Engine implementation in Sprint 2
        """
        raise NotImplementedError(
            "StrategyEngine.evaluate_dsl() implementation deferred to Sprint 2. "
            "Current sprint focuses on DSL definition and validation only."
        )


class MarketContext:
    """
    Market Context for Strategy Evaluation - Placeholder.
    
    Will contain:
    - OHLCV data for symbol(s)
    - Calculated indicators
    - Current timestamp
    - Historical data window
    
    Implementation deferred to Sprint 2.
    """
    
    def __init__(self) -> None:
        raise NotImplementedError(
            "MarketContext implementation deferred to Sprint 2. "
            "Current sprint focuses on DSL definition and validation only."
        )
