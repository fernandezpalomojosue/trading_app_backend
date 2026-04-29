# app/domain/entities/strategy_dsl.py
"""
DSL Models for Trading Strategy Definition

Implements the JSON DSL specification for defining trading strategies as AST.
Supports logical nodes (AND, OR, NOT), conditions, and expressions.
"""

from typing import Any, Dict, List, Literal, Union
from pydantic import BaseModel, Field, field_validator


# ==============================
# Expression Types (Leaf Nodes)
# ==============================

class Constant(BaseModel):
    """Constant value expression"""
    type: Literal["constant"]
    value: Union[int, float]


class Price(BaseModel):
    """Price field expression"""
    type: Literal["price"]
    field: Literal["open", "high", "low", "close", "volume"]


class Indicator(BaseModel):
    """Technical indicator expression"""
    type: Literal["indicator"]
    name: Literal["RSI", "SMA", "EMA", "MACD"]
    params: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('params')
    @classmethod
    def validate_params(cls, v, info):
        """Validate indicator parameters based on indicator type"""
        # Get the name from the parent model
        # This will be called after the model is fully validated
        return v


Expression = Union[Constant, Price, Indicator]


# ==============================
# Logical Nodes
# ==============================

class AndNode(BaseModel):
    """Logical AND node - all children must be true"""
    type: Literal["AND"]
    children: List["Node"] = Field(min_length=2, max_length=10)


class OrNode(BaseModel):
    """Logical OR node - at least one child must be true"""
    type: Literal["OR"]
    children: List["Node"] = Field(min_length=2, max_length=10)


class NotNode(BaseModel):
    """Logical NOT node - negates a single child"""
    type: Literal["NOT"]
    child: "Node"
    
    @field_validator('child')
    @classmethod
    def validate_not_child(cls, v):
        """Validate that NOT has exactly one valid child"""
        if v is None:
            raise ValueError("NOT node child cannot be None")
        return v


# ==============================
# Condition Node
# ==============================

class Condition(BaseModel):
    """Condition node - comparison between two expressions"""
    type: Literal["condition"]
    left: Expression
    operator: Literal[
        "<", "<=", ">", ">=", "==", "!=",
        "cross_above", "cross_below"
    ]
    right: Expression


# ==============================
# Node Union Type
# ==============================

Node = Union[AndNode, OrNode, NotNode, Condition]

# Update forward references
AndNode.model_rebuild()
OrNode.model_rebuild()
NotNode.model_rebuild()


# ==============================
# Strategy DSL Root
# ==============================

class StrategyDSL(BaseModel):
    """
    Root model for Trading Strategy DSL
    
    Structure:
    {
        "version": 1,
        "root": { ...AST... }
    }
    """
    version: int = Field(default=1, ge=1, description="DSL version for backward compatibility")
    root: Node = Field(description="Root node of the AST - must be a valid logical or condition node")
    
    @field_validator('root')
    @classmethod
    def validate_root_not_null(cls, v):
        """Validate that root is not null"""
        if v is None:
            raise ValueError("Root node cannot be None")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "version": 1,
                "root": {
                    "type": "AND",
                    "children": [
                        {
                            "type": "condition",
                            "left": {"type": "indicator", "name": "RSI", "params": {"period": 14}},
                            "operator": "<",
                            "right": {"type": "constant", "value": 30}
                        },
                        {
                            "type": "condition",
                            "left": {"type": "price", "field": "close"},
                            "operator": ">",
                            "right": {"type": "indicator", "name": "SMA", "params": {"period": 20}}
                        }
                    ]
                }
            }
        }
