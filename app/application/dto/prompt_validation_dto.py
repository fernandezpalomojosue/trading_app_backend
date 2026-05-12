"""
Data Transfer Objects for Prompt Validation

Request/Response models for strategy prompt validation API.
"""

from typing import Optional
from pydantic import BaseModel, Field


class PromptValidationRequest(BaseModel):
    """Request to validate a strategy prompt."""
    
    prompt: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Natural language description of trading strategy to validate"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Create a strategy that buys when RSI is below 30 and price crosses above 20-day EMA"
            }
        }


class PromptValidationResponse(BaseModel):
    """Response from prompt validation."""
    
    status: str = Field(
        ...,
        pattern="^(VALID|INVALID)$",
        description="Validation status: VALID or INVALID"
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for invalid status (only present when status is INVALID)"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "status": "VALID"
                },
                {
                    "status": "INVALID",
                    "reason": "Unsupported indicator: news sentiment"
                }
            ]
        }
