"""
Data Transfer Objects for AI Strategy Generation

Request/Response models for the AI-powered strategy generation API.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ==============================
# Request DTOs
# ==============================

class StrategyGenerateRequest(BaseModel):
    """Request to generate a strategy from natural language."""
    
    prompt: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Natural language description of the trading strategy"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Create a strategy that buys when RSI is below 30 and price crosses above the 20-day EMA"
            }
        }


# ==============================
# Response DTOs
# ==============================

class StrategyGenerateResponse(BaseModel):
    """Successful strategy generation response."""
    
    name: str = Field(..., description="Generated strategy name")
    description: str = Field(..., description="Strategy description")
    action: Literal["buy", "sell", "hold"] = Field(
        ...,
        description="Strategy action: buy, sell, or hold"
    )
    dsl_definition: Dict[str, Any] = Field(
        ...,
        description="Generated DSL definition (validated)"
    )
    is_valid: bool = Field(
        default=True,
        description="Whether the generated DSL passed validation"
    )
    validation_errors: List[str] = Field(
        default_factory=list,
        description="Validation errors (empty if is_valid=True)"
    )
    attempts_made: int = Field(
        ...,
        description="Number of AI attempts (1-3)",
        ge=1,
        le=3
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "RSI Oversold EMA Crossover",
                "description": "Buy signal when RSI indicates oversold conditions (<30) and price confirms uptrend by crossing above 20-day EMA",
                "action": "buy",
                "dsl_definition": {
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
                                "operator": "cross_above",
                                "right": {"type": "indicator", "name": "EMA", "params": {"period": 20}}
                            }
                        ]
                    }
                },
                "is_valid": True,
                "validation_errors": [],
                "attempts_made": 1
            }
        }


class StrategyGenerationError(BaseModel):
    """Error response when strategy generation fails."""
    
    error_type: Literal[
        "rate_limit",
        "timeout",
        "invalid_json",
        "validation_failed",
        "ai_error"
    ] = Field(..., description="Type of error")
    
    message: str = Field(..., description="Human-readable error message")
    
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_type": "validation_failed",
                "message": "AI generated invalid DSL after 2 retries",
                "details": {
                    "validation_errors": ["AND node must have at least 2 children, got 1"],
                    "attempts_made": 3
                }
            }
        }


class StrategyGenerationPreviewResponse(BaseModel):
    """
    Preview response for DSL debugging.
    
    Useful for:
    - Showing generated DSL in UI
    - Debugging AI-generated strategies
    - Validating before saving
    """
    
    is_valid: bool
    name: str
    description: str
    action: Literal["buy", "sell", "hold"]
    dsl_definition: Dict[str, Any]
    dsl_depth: int
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)
    attempts_made: int
    pretty_print: Optional[str] = Field(
        default=None,
        description="Formatted DSL for display"
    )
