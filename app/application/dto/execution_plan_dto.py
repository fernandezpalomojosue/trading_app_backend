# app/application/dto/execution_plan_dto.py
"""
Execution Plan DTOs

Data Transfer Objects for Execution Plan API endpoints.
Includes validation, normalization, and response formatting.
"""

from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum
import re


class Timeframe(str, Enum):
    """Valid timeframes for execution plans."""
    DAY = "day"
    HOUR = "hour"
    MINUTE = "minute"
    FOUR_HOUR = "4hour"


class CreateExecutionPlanDTO(BaseModel):
    """DTO for creating a new execution plan."""
    strategy_id: UUID = Field(..., description="Strategy to execute")
    stocks: List[str] = Field(..., min_length=1, max_length=100, description="Stock symbols to evaluate")
    timeframe: Timeframe = Field(Timeframe.DAY, description="Timeframe for execution")
    
    @validator('stocks')
    def normalize_stocks(cls, v):
        """Normalize stock symbols: trim, uppercase, deduplicate, validate format."""
        if not v:
            raise ValueError('Stocks list cannot be empty')
        
        # Remove whitespace and normalize
        normalized = []
        for stock in v:
            if stock and stock.strip():
                clean_stock = stock.strip().upper()
                # Validate format: 1-10 uppercase letters
                if not re.match(r'^[A-Z]{1,10}$', clean_stock):
                    raise ValueError(f'Invalid stock symbol format: {stock}')
                normalized.append(clean_stock)
        
        # Deduplicate
        unique_stocks = list(set(normalized))
        
        if not unique_stocks:
            raise ValueError('Stocks list cannot be empty after normalization')
            
        return unique_stocks


class UpdateExecutionPlanDTO(BaseModel):
    """DTO for updating an existing execution plan."""
    stocks: Optional[List[str]] = Field(None, min_length=1, max_length=100, description="Stock symbols to evaluate")
    timeframe: Optional[Timeframe] = None
    is_active: Optional[bool] = None
    
    @validator('stocks')
    def normalize_stocks(cls, v):
        """Normalize stock symbols if provided."""
        if v is None:
            return v
        
        if not v:
            raise ValueError('Stocks list cannot be empty')
        
        # Remove whitespace and normalize
        normalized = []
        for stock in v:
            if stock and stock.strip():
                clean_stock = stock.strip().upper()
                # Validate format: 1-10 uppercase letters
                if not re.match(r'^[A-Z]{1,10}$', clean_stock):
                    raise ValueError(f'Invalid stock symbol format: {stock}')
                normalized.append(clean_stock)
        
        # Deduplicate
        unique_stocks = list(set(normalized))
        
        if not unique_stocks:
            raise ValueError('Stocks list cannot be empty after normalization')
            
        return unique_stocks


class ExecutionPlanResponseDTO(BaseModel):
    """DTO for execution plan responses."""
    id: UUID
    strategy_id: UUID
    strategy_name: str
    stocks: List[str]
    timeframe: str
    is_active: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True
