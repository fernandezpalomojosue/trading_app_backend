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
    
    # Unsupported features for prompt validation
    UNSUPPORTED_FEATURES: Set[str] = {
        "news sentiment",
        "social sentiment", 
        "sentiment analysis",
        "options flow",
        "options trading",
        "futures",
        "crypto",
        "forex",
        "commodities",
        "market manipulation detection",
        "ai prediction",
        "machine learning prediction",
        "neural network"
    }
    
    # Unsupported trading concepts
    UNSUPPORTED_CONCEPTS: Set[str] = {
        "discretionary trading",
        "emotional analysis",
        "psychology-based trading",
        "macroeconomic intuition",
        "gut feeling",
        "market intuition",
        "fundamental analysis",
        "technical analysis patterns",  # beyond basic indicators
        "chart patterns",
        "candlestick patterns",
        "elliott wave",
        "harmonic patterns"
    }
    
    # Supported actions
    SUPPORTED_ACTIONS: Set[str] = {"buy", "sell", "hold"}
    
    # Ambiguous terms that trigger rejection
    AMBIGUOUS_TERMS: Set[str] = {
        "good stocks",
        "bad stocks", 
        "strong companies",
        "weak companies",
        "profitable strategy",
        "make money",
        "winning strategy",
        "successful trading",
        "best stocks",
        "top stocks",
        "quality companies"
    }
    
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
    
    @classmethod
    def has_unsupported_features(cls, prompt: str) -> List[str]:
        """Check if prompt contains unsupported features."""
        found_features = []
        prompt_lower = prompt.lower()
        
        for feature in cls.UNSUPPORTED_FEATURES:
            if feature in prompt_lower:
                found_features.append(f"Unsupported feature: {feature}")
        
        return found_features
    
    @classmethod
    def has_unsupported_concepts(cls, prompt: str) -> List[str]:
        """Check if prompt contains unsupported trading concepts."""
        found_concepts = []
        prompt_lower = prompt.lower()
        
        for concept in cls.UNSUPPORTED_CONCEPTS:
            if concept in prompt_lower:
                found_concepts.append(f"Unsupported concept: {concept}")
        
        return found_concepts
    
    @classmethod
    def has_ambiguous_terms(cls, prompt: str) -> List[str]:
        """Check if prompt contains ambiguous terms."""
        found_terms = []
        prompt_lower = prompt.lower()
        
        for term in cls.AMBIGUOUS_TERMS:
            if term in prompt_lower:
                found_terms.append(f"Ambiguous term: {term}")
        
        return found_terms
    
    @classmethod
    def has_contradictory_logic(cls, prompt: str) -> List[str]:
        """Check for obvious logical contradictions in prompt."""
        contradictions = []
        prompt_lower = prompt.lower()
        
        # Check for contradictory RSI conditions
        if "rsi >" in prompt_lower and "rsi <" in prompt_lower:
            # Extract numbers to check for actual contradiction
            import re
            greater_matches = re.findall(r'rsi\s*>\s*(\d+)', prompt_lower)
            lesser_matches = re.findall(r'rsi\s*<\s*(\d+)', prompt_lower)
            
            for greater_num in greater_matches:
                for lesser_num in lesser_matches:
                    if int(greater_num) > int(lesser_num):
                        contradictions.append("Contradictory logic: RSI cannot be both greater than and less than conflicting values")
        
        # Check for impossible AND conditions
        if "and" in prompt_lower:
            # Look for obvious contradictions like "buy and sell at same time"
            if "buy" in prompt_lower and "sell" in prompt_lower:
                contradictions.append("Contradictory logic: Cannot buy and sell simultaneously")
        
        return contradictions
    
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
    
    @classmethod
    def get_dsl_schema_json(cls) -> str:
        """
        Export DSL schema as JSON string for AI prompts.
        
        Returns:
            JSON string describing valid DSL structure
        """
        import json
        
        schema = {
            "version": 1,
            "description": "Root strategy definition",
            "properties": {
                "version": {"type": "integer", "minimum": 1},
                "action": {"enum": ["buy", "sell", "hold"]},
                "dsl_definition": {
                    "type": "object",
                    "properties": {
                        "version": {"type": "integer", "minimum": 1},
                        "root": {
                            "type": "object",
                            "oneOf": [
                                {
                                    "type": "object",
                                    "properties": {
                                        "type": {"const": "AND"},
                                        "children": {
                                            "type": "array",
                                            "items": {"$ref": "#/$defs/node"},
                                            "minItems": 2,
                                            "maxItems": 10
                                        }
                                    },
                                    "required": ["type", "children"]
                                },
                                {
                                    "type": "object",
                                    "properties": {
                                        "type": {"const": "OR"},
                                        "children": {
                                            "type": "array",
                                            "items": {"$ref": "#/$defs/node"},
                                            "minItems": 2,
                                            "maxItems": 10
                                        }
                                    },
                                    "required": ["type", "children"]
                                },
                                {
                                    "type": "object",
                                    "properties": {
                                        "type": {"const": "NOT"},
                                        "child": {"$ref": "#/$defs/node"}
                                    },
                                    "required": ["type", "child"]
                                },
                                {
                                    "type": "object",
                                    "properties": {
                                        "type": {"const": "condition"},
                                        "left": {"$ref": "#/$defs/expression"},
                                        "operator": {"enum": list(cls.ALL_OPERATORS)},
                                        "right": {"$ref": "#/$defs/expression"}
                                    },
                                    "required": ["type", "left", "operator", "right"]
                                }
                            ]
                        }
                    },
                    "required": ["version", "root"]
                }
            },
            "required": ["name", "description", "action", "dsl_definition"],
            "$defs": {
                "node": {
                    "anyOf": [
                        {"type": "object", "properties": {"type": {"const": "AND"}}},
                        {"type": "object", "properties": {"type": {"const": "OR"}}},
                        {"type": "object", "properties": {"type": {"const": "NOT"}}},
                        {"type": "object", "properties": {"type": {"const": "condition"}}}
                    ]
                },
                "expression": {
                    "anyOf": [
                        {
                            "type": "object",
                            "properties": {
                                "type": {"const": "constant"},
                                "value": {"type": "number"}
                            },
                            "required": ["type", "value"]
                        },
                        {
                            "type": "object",
                            "properties": {
                                "type": {"const": "price"},
                                "field": {"enum": list(cls.PRICE_FIELDS)}
                            },
                            "required": ["type", "field"]
                        },
                        {
                            "type": "object",
                            "properties": {
                                "type": {"const": "indicator"},
                                "name": {"enum": list(cls.INDICATORS.keys())},
                                "params": {"type": "object"}
                            },
                            "required": ["type", "name"]
                        }
                    ]
                }
            }
        }
        
        return json.dumps(schema, indent=2)
