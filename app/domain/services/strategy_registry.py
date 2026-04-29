# app/domain/services/strategy_registry.py
"""
Operator and Indicator Registry

Single source of truth for:
- Valid operators in conditions
- Valid indicators in expressions
- Parameter schemas for indicators

Used by DSLValidator (Sprint 1) and StrategyEngine (Sprint 2).
Prevents inconsistencies between validation and evaluation.
"""

from typing import Dict, List, Set, Any
from dataclasses import dataclass, field


@dataclass(frozen=True)
class IndicatorSpec:
    """Specification for a technical indicator"""
    name: str
    required_params: List[str] = field(default_factory=list)
    optional_params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


class StrategyRegistry:
    """
    Registry of valid operators and indicators.
    
    This is a singleton-style class that provides:
    - Valid operators: <, <=, >, >=, ==, !=, cross_above, cross_below
    - Valid indicators: SMA, EMA, RSI, MACD with their parameter specs
    """
    
    # Comparison operators
    COMPARISON_OPERATORS: Set[str] = {
        "<", "<=", ">", ">=", "==", "!="
    }
    
    # Event operators (for crossovers)
    EVENT_OPERATORS: Set[str] = {
        "cross_above",
        "cross_below"
    }
    
    # All valid operators
    ALL_OPERATORS: Set[str] = COMPARISON_OPERATORS | EVENT_OPERATORS
    
    # Indicator specifications
    INDICATORS: Dict[str, IndicatorSpec] = {
        "SMA": IndicatorSpec(
            name="SMA",
            required_params=["period"],
            optional_params={},
            description="Simple Moving Average"
        ),
        "EMA": IndicatorSpec(
            name="EMA",
            required_params=["period"],
            optional_params={},
            description="Exponential Moving Average"
        ),
        "RSI": IndicatorSpec(
            name="RSI",
            required_params=["period"],
            optional_params={},
            description="Relative Strength Index"
        ),
        "MACD": IndicatorSpec(
            name="MACD",
            required_params=["fast", "slow", "signal"],
            optional_params={},
            description="Moving Average Convergence Divergence"
        )
    }
    
    # Price fields
    PRICE_FIELDS: Set[str] = {
        "open", "high", "low", "close", "volume"
    }
    
    # Node types
    LOGICAL_NODE_TYPES: Set[str] = {"AND", "OR", "NOT"}
    CONDITION_TYPE: str = "condition"
    EXPRESSION_TYPES: Set[str] = {"constant", "price", "indicator"}
    
    @classmethod
    def is_valid_operator(cls, operator: str) -> bool:
        """Check if an operator is valid"""
        return operator in cls.ALL_OPERATORS
    
    @classmethod
    def is_valid_indicator(cls, indicator: str) -> bool:
        """Check if an indicator is valid"""
        return indicator in cls.INDICATORS
    
    @classmethod
    def get_indicator_spec(cls, indicator: str) -> IndicatorSpec:
        """Get the specification for an indicator"""
        if not cls.is_valid_indicator(indicator):
            raise ValueError(f"Unknown indicator: {indicator}")
        return cls.INDICATORS[indicator]
    
    @classmethod
    def is_valid_price_field(cls, field: str) -> bool:
        """Check if a price field is valid"""
        return field in cls.PRICE_FIELDS
    
    @classmethod
    def is_logical_node(cls, node_type: str) -> bool:
        """Check if a node type is logical"""
        return node_type in cls.LOGICAL_NODE_TYPES
    
    @classmethod
    def is_expression_type(cls, expr_type: str) -> bool:
        """Check if an expression type is valid"""
        return expr_type in cls.EXPRESSION_TYPES
    
    @classmethod
    def get_all_operators(cls) -> List[str]:
        """Get all valid operators"""
        return sorted(cls.ALL_OPERATORS)
    
    @classmethod
    def get_all_indicators(cls) -> List[str]:
        """Get all valid indicators"""
        return sorted(cls.INDICATORS.keys())
    
    @classmethod
    def validate_indicator_params(cls, indicator: str, params: Dict[str, Any]) -> List[str]:
        """
        Validate indicator parameters.
        Returns list of error messages (empty if valid).
        """
        errors = []
        
        if not cls.is_valid_indicator(indicator):
            errors.append(f"Unknown indicator: {indicator}")
            return errors
        
        spec = cls.INDICATORS[indicator]
        
        # Check required params
        for req_param in spec.required_params:
            if req_param not in params:
                errors.append(f"Missing required parameter '{req_param}' for {indicator}")
        
        # Check for unknown params
        all_allowed = set(spec.required_params) | set(spec.optional_params.keys())
        for param in params.keys():
            if param not in all_allowed:
                errors.append(f"Unknown parameter '{param}' for {indicator}")
        
        return errors
