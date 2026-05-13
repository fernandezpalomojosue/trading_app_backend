# app/domain/services/strategy_engine.py
"""
Strategy Evaluation Engine

Evaluates Trading Strategy DSL against market context.
Uses StrategyEvaluator for recursive AST evaluation.
"""

from typing import Any, Dict, Optional
from app.domain.entities.strategy import Strategy
from app.domain.entities.strategy_dsl import StrategyDSL
from app.domain.entities.market_snapshot import MarketSnapshot
from app.domain.services.strategy_evaluator import StrategyEvaluator


class StrategyEngine:
    """
    Strategy Evaluation Engine.
    
    Evaluates DSL conditions against market data to determine if strategy conditions are met.
    Returns boolean - True if conditions met, False otherwise.
    
    Usage:
        engine = StrategyEngine()
        condition_met = engine.evaluate(strategy, context)
        
        if condition_met:
            signal_action = strategy.dsl_definition.get("action", "buy")
            # Generate signal with signal_action
    """
    
    def __init__(self):
        """Initialize StrategyEngine with evaluator."""
        self._evaluator = StrategyEvaluator()
    
    def evaluate(self, strategy: Strategy, context: MarketSnapshot, prev_context: Optional[MarketSnapshot] = None) -> bool:
        """
        Evaluate a strategy against market context.
        
        Args:
            strategy: Strategy entity with DSL definition
            context: MarketSnapshot with OHLCV data, indicators, etc.
            prev_context: Previous MarketSnapshot for crossover detection (optional)
            
        Returns:
            True if strategy conditions are met, False otherwise
            
        Example:
            >>> engine = StrategyEngine()
            >>> result = engine.evaluate(strategy, context)
            >>> if result:
            ...     print(f"Conditions met - generate {strategy.dsl_definition.get('action', 'buy')} signal")
        """
        # Parse DSL from strategy entity
        dsl_json = strategy.dsl_definition
        
        # Create StrategyDSL object
        try:
            dsl = StrategyDSL.model_validate(dsl_json)
        except Exception as e:
            raise ValueError(f"Invalid DSL definition: {e}")
        
        # Evaluate DSL against context
        return self._evaluator.evaluate_dsl(dsl.root, context, prev_context)
    
    def evaluate_dsl(self, dsl: StrategyDSL, context: MarketSnapshot, prev_context: Optional[MarketSnapshot] = None) -> bool:
        """
        Evaluate a DSL definition directly.
        
        Args:
            dsl: StrategyDSL object
            context: MarketSnapshot with OHLCV data, indicators, etc.
            prev_context: Previous MarketSnapshot for crossover detection (optional)
            
        Returns:
            True if DSL conditions are met, False otherwise
        """
        return self._evaluator.evaluate_dsl(dsl.root, context, prev_context)
    
    def evaluate_json(self, dsl_json: Dict[str, Any], context: MarketSnapshot, prev_context: Optional[MarketSnapshot] = None) -> bool:
        """
        Evaluate DSL from JSON dict.
        
        Args:
            dsl_json: DSL definition as JSON dict
            context: MarketSnapshot with OHLCV data, indicators, etc.
            prev_context: Previous MarketSnapshot for crossover detection (optional)
            
        Returns:
            True if DSL conditions are met, False otherwise
        """
        try:
            dsl = StrategyDSL.model_validate(dsl_json)
        except Exception as e:
            raise ValueError(f"Invalid DSL definition: {e}")
        
        return self._evaluator.evaluate_dsl(dsl.root, context, prev_context)


class StrategyResult:
    """
    Result of strategy evaluation.
    
    Contains evaluation result and metadata for signal generation.
    """
    
    def __init__(self, condition_met: bool, action: str, strategy_name: str, strategy_id: Any):
        self.condition_met = condition_met
        self.action = action
        self.strategy_name = strategy_name
        self.strategy_id = strategy_id
    
    @property
    def should_signal(self) -> bool:
        """True if conditions met and action is not 'hold'."""
        return self.condition_met and self.action != "hold"
    
    def __repr__(self) -> str:
        return f"StrategyResult(condition_met={self.condition_met}, action='{self.action}', strategy='{self.strategy_name}')"
