# app/domain/services/strategy_evaluator.py
"""
Strategy Evaluator - Core DSL Evaluation Logic

Pure function layer for evaluating Trading Strategy DSL AST.
Stateless, deterministic, testable - no side effects.

Supports:
- Logical nodes: AND, OR, NOT
- Condition nodes with operators: <, <=, >, >=, ==, !=, cross_above, cross_below
- Expression evaluation: constant, price, indicator
"""
from typing import Optional, Any, Dict
import logging

from app.domain.entities.strategy_dsl import (
    Node, Expression,
    AndNode, OrNode, NotNode, Condition,
    Constant, Price, Indicator
)
from app.domain.entities.market_context import MarketContext

logger = logging.getLogger(__name__)


class StrategyEvaluator:
    """
    Pure function layer for DSL evaluation.
    
    Evaluates DSL AST against MarketContext to determine if conditions are met.
    Returns boolean - True if conditions met, False otherwise.
    """
    
    @classmethod
    def evaluate_dsl(cls, dsl_root: Node, context: MarketContext, prev_context: Optional[MarketContext] = None) -> bool:
        """
        Evaluate DSL AST root node against market context.
        
        Args:
            dsl_root: Root node of DSL AST (AndNode, OrNode, NotNode, or Condition)
            context: Current market context with indicators
            prev_context: Previous market context for crossover detection (optional)
            
        Returns:
            True if conditions are met, False otherwise
        """
        return cls.evaluate_node(dsl_root, context, prev_context)
    
    @classmethod
    def evaluate_node(cls, node: Node, context: MarketContext, prev_context: Optional[MarketContext] = None) -> bool:
        """
        Recursively evaluate AST node.
        
        Args:
            node: AST node to evaluate
            context: Current market context
            prev_context: Previous context for crossover detection
            
        Returns:
            Boolean evaluation result
        """
        if isinstance(node, AndNode):
            return cls._evaluate_and(node, context, prev_context)
        elif isinstance(node, OrNode):
            return cls._evaluate_or(node, context, prev_context)
        elif isinstance(node, NotNode):
            return cls._evaluate_not(node, context, prev_context)
        elif isinstance(node, Condition):
            return cls._evaluate_condition(node, context, prev_context)
        else:
            logger.warning(f"Unknown node type: {type(node)}")
            return False
    
    @classmethod
    def _evaluate_and(cls, node: AndNode, context: MarketContext, prev_context: Optional[MarketContext]) -> bool:
        """Evaluate AND node - all children must be true"""
        if not node.children:
            return False
        return all(cls.evaluate_node(child, context, prev_context) for child in node.children)
    
    @classmethod
    def _evaluate_or(cls, node: OrNode, context: MarketContext, prev_context: Optional[MarketContext]) -> bool:
        """Evaluate OR node - at least one child must be true"""
        if not node.children:
            return False
        return any(cls.evaluate_node(child, context, prev_context) for child in node.children)
    
    @classmethod
    def _evaluate_not(cls, node: NotNode, context: MarketContext, prev_context: Optional[MarketContext]) -> bool:
        """Evaluate NOT node - negate child result"""
        if node.child is None:
            return False
        return not cls.evaluate_node(node.child, context, prev_context)
    
    @classmethod
    def _evaluate_condition(cls, condition: Condition, context: MarketContext, prev_context: Optional[MarketContext]) -> bool:
        """
        Evaluate condition node.
        
        Supports operators:
        - Comparison: <, <=, >, >=, ==, !=
        - Crossover: cross_above, cross_below
        """
        logger.debug(f"Evaluating condition: {condition.operator}")
        
        left_val = cls._evaluate_expression(condition.left, context)
        right_val = cls._evaluate_expression(condition.right, context)
        
        logger.debug(f"Condition values: left={left_val}, right={right_val}")
        
        # Handle None values
        if left_val is None or right_val is None:
            logger.debug(f"Cannot evaluate condition - missing values: left={left_val}, right={right_val}")
            return False
        
        operator = condition.operator
        
        logger.debug(f"Applying operator: {operator}")
        
        # Handle crossover operators
        if operator == "cross_above":
            result = cls._evaluate_cross_above(left_val, right_val, condition.left, condition.right, prev_context)
            logger.debug(f"Cross_above result: {result}")
            return result
        elif operator == "cross_below":
            result = cls._evaluate_cross_below(left_val, right_val, condition.left, condition.right, prev_context)
            logger.debug(f"Cross_below result: {result}")
            return result
        
        # Handle comparison operators
        result = cls._evaluate_comparison(left_val, right_val, operator)
        logger.debug(f"Comparison result: {result}")
        return result
    
    @classmethod
    def _evaluate_cross_above(cls, left_val: float, right_val: float, 
                               left_expr: Expression, right_expr: Expression,
                               prev_context: Optional[MarketContext]) -> bool:
        """
        Evaluate cross_above - left crosses from below to above right.
        
        Requires prev_context to detect the crossover.
        """
        if prev_context is None:
            # Without previous context, just check if left > right
            return left_val > right_val
        
        prev_left = cls._evaluate_expression(left_expr, prev_context)
        prev_right = cls._evaluate_expression(right_expr, prev_context)
        
        if prev_left is None or prev_right is None:
            return left_val > right_val
        
        # Crossover: previously left <= right, now left > right
        return prev_left <= prev_right and left_val > right_val
    
    @classmethod
    def _evaluate_cross_below(cls, left_val: float, right_val: float,
                               left_expr: Expression, right_expr: Expression,
                               prev_context: Optional[MarketContext]) -> bool:
        """
        Evaluate cross_below - left crosses from above to below right.
        
        Requires prev_context to detect the crossover.
        """
        if prev_context is None:
            # Without previous context, just check if left < right
            return left_val < right_val
        
        prev_left = cls._evaluate_expression(left_expr, prev_context)
        prev_right = cls._evaluate_expression(right_expr, prev_context)
        
        if prev_left is None or prev_right is None:
            return left_val < right_val
        
        # Crossover: previously left >= right, now left < right
        return prev_left >= prev_right and left_val < right_val
    
    @classmethod
    def _evaluate_comparison(cls, left: float, right: float, operator: str) -> bool:
        """Evaluate comparison operators"""
        if operator == "<":
            return left < right
        elif operator == "<=":
            return left <= right
        elif operator == ">":
            return left > right
        elif operator == ">=":
            return left >= right
        elif operator == "==":
            return left == right
        elif operator == "!=":
            return left != right
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False
    
    @classmethod
    def _evaluate_expression(cls, expression: Expression, context: MarketContext) -> Optional[float]:
        """
        Evaluate expression to get numeric value.
        
        Supports:
        - Constant: returns constant value
        - Price: returns price field from context (with optional offset for historical)
        - Indicator: returns indicator value from context (with optional offset for historical)
        
        Note: offset handling for historical data requires MarketContext with historical access.
        Currently only offset=0 (current candle) is fully supported in execution.
        """
        logger.debug(f"Evaluating expression: {expression}")
        
        if isinstance(expression, Constant):
            value = float(expression.value)
            logger.debug(f"Constant expression value: {value}")
            return value
        elif isinstance(expression, Price):
            # Implement offset handling for historical price access
            offset = getattr(expression, 'offset', 0) or 0
            logger.debug(f"Price expression: field={expression.field}, offset={offset}")
            
            if offset == 0:
                # Current candle - use context directly
                value = context.get_value(expression.field)
                logger.debug(f"Current price value: field={expression.field}, value={value}")
                return value
            else:
                # Historical candle - access from MarketSnapshot if available
                if hasattr(context, '_market_snapshot') and context._market_snapshot:
                    snapshot = context._market_snapshot
                    indicators = snapshot.indicators
                    
                    logger.debug(f"Market snapshot available with {len(indicators)} indicators")
                    
                    # Calculate index for historical data
                    # offset=1 means previous candle, offset=2 means 2 candles back, etc.
                    if offset <= len(indicators):
                        historical_index = -(offset)  # Negative index from end
                        historical_point = indicators[historical_index]
                        
                        logger.debug(f"Evaluating price expression with offset={offset}, historical_index={historical_index}")
                        
                        # Create temporary context from historical point using new method
                        from app.domain.entities.market_context import MarketContext
                        historical_context = MarketContext.from_snapshot(snapshot, historical_index)
                        historical_value = historical_context.get_value(expression.field)
                        
                        logger.debug(f"Price expression evaluation: field={expression.field}, offset={offset}, historical_value={historical_value}")
                        
                        return historical_value
                    else:
                        logger.warning(f"Price offset={offset} exceeds available historical data ({len(indicators)} candles), using current candle")
                        value = context.get_value(expression.field)
                        logger.debug(f"Fallback to current price: field={expression.field}, value={value}")
                        return value
                else:
                    logger.warning(f"Price offset={offset} not available (no MarketSnapshot), using current candle")
                    value = context.get_value(expression.field)
                    logger.debug(f"Fallback to current price: field={expression.field}, value={value}")
                    return value
        elif isinstance(expression, Indicator):
            return cls._evaluate_indicator(expression, context)
        else:
            logger.warning(f"Unknown expression type: {type(expression)}")
            return None
    
    @classmethod
    def _evaluate_indicator(cls, indicator: Indicator, context: MarketContext) -> Optional[float]:
        """
        Evaluate indicator expression.
        
        Maps indicator name to context value.
        Supports: RSI, SMA, EMA, MACD
        
        Note: offset handling for historical indicator values requires MarketContext with historical access.
        Currently only offset=0 (current candle) is fully supported in execution.
        """
        name = indicator.name
        params = indicator.params or {}
        
        # Offset handling for historical indicator access
        # For now, only current candle (offset=0 or None) is supported
        offset = getattr(indicator, 'offset', 0) or 0
        if offset != 0:
            logger.warning(f"Indicator offset={offset} not yet implemented in execution, using current candle")
        
        # Map indicator names to context fields
        indicator_map = {
            "RSI": context.rsi,
            "SMA": context.sma,
            "EMA": context.ema,
            "MACD": context.macd,
        }
        
        # For MACD, check params to return specific component
        if name == "MACD" and params:
            field = params.get("field")
            if field == "signal":
                return context.macd_signal
            elif field == "histogram":
                return context.macd_histogram
            # Default to MACD line
            return context.macd
        
        return indicator_map.get(name)
