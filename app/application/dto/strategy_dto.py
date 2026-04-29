# app/application/dto/strategy_dto.py
"""
Data Transfer Objects for Strategy API

Request and Response models for strategy CRUD operations.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ==============================
# Request DTOs
# ==============================

class StrategyCreateRequest(BaseModel):
    """Request to create a new strategy"""
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Strategy name"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Strategy description"
    )
    dsl_definition: Dict[str, Any] = Field(
        description="DSL definition as JSON object"
    )
    version: int = Field(
        default=1,
        ge=1,
        description="DSL version"
    )
    is_active: bool = Field(
        default=True,
        description="Whether the strategy is active"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "RSI Oversold Strategy",
                "description": "Buy when RSI < 30",
                "dsl_definition": {
                    "version": 1,
                    "root": {
                        "type": "condition",
                        "left": {
                            "type": "indicator",
                            "name": "RSI",
                            "params": {"period": 14}
                        },
                        "operator": "<",
                        "right": {
                            "type": "constant",
                            "value": 30
                        }
                    }
                },
                "version": 1,
                "is_active": True
            }
        }


class StrategyUpdateRequest(BaseModel):
    """Request to update an existing strategy"""
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Strategy name"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Strategy description"
    )
    dsl_definition: Optional[Dict[str, Any]] = Field(
        default=None,
        description="DSL definition as JSON object"
    )
    version: Optional[int] = Field(
        default=None,
        ge=1,
        description="DSL version"
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Whether the strategy is active"
    )


# ==============================
# Response DTOs
# ==============================

class StrategyResponse(BaseModel):
    """Response with strategy details"""
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]
    is_active: bool
    dsl_definition: Dict[str, Any]
    version: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "name": "RSI Oversold Strategy",
                "description": "Buy when RSI < 30",
                "is_active": True,
                "dsl_definition": {
                    "version": 1,
                    "root": {
                        "type": "condition",
                        "left": {
                            "type": "indicator",
                            "name": "RSI",
                            "params": {"period": 14}
                        },
                        "operator": "<",
                        "right": {
                            "type": "constant",
                            "value": 30
                        }
                    }
                },
                "version": 1,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class StrategyListResponse(BaseModel):
    """Response with list of strategies"""
    items: List[StrategyResponse]
    total: int
    page: int
    page_size: int


class StrategyDSLPreviewResponse(BaseModel):
    """
    Response for DSL preview/debugging.
    
    Useful for:
    - Showing DSL in UI
    - Debugging AI-generated DSL
    - Validating DSL before saving
    """
    is_valid: bool
    dsl_definition: Dict[str, Any]
    version: int
    depth: int
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    pretty_print: Optional[str] = Field(
        default=None,
        description="Formatted DSL for display"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "dsl_definition": {
                    "version": 1,
                    "root": {
                        "type": "condition",
                        "left": {"type": "indicator", "name": "RSI", "params": {"period": 14}},
                        "operator": "<",
                        "right": {"type": "constant", "value": 30}
                    }
                },
                "version": 1,
                "depth": 2,
                "errors": [],
                "warnings": [],
                "pretty_print": "{\n  \"version\": 1,\n  \"root\": {\n    \"type\": \"condition\",\n    ...\n  }\n}"
            }
        }


class StrategyValidationResponse(BaseModel):
    """Response for DSL validation"""
    is_valid: bool
    depth: int
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
