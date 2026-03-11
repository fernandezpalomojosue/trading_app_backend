# app/application/dto/portfolio_dto.py
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.domain.entities.portfolio import TransactionType


class HoldingResponse(BaseModel):
    """Response DTO for portfolio holding"""
    id: uuid.UUID
    symbol: str
    quantity: float
    average_price: float
    current_price: float
    total_value: float
    unrealized_pnl: float
    pnl_percentage: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    """Response DTO for transaction"""
    id: uuid.UUID
    symbol: str
    transaction_type: TransactionType
    quantity: float
    price: float
    total_amount: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class PortfolioSummaryResponse(BaseModel):
    """Response DTO for portfolio summary"""
    user_id: uuid.UUID
    cash_balance: float
    total_holdings_value: float
    total_portfolio_value: float
    total_unrealized_pnl: float
    unrealized_pnl_percentage: float
    holdings_count: int
    updated_at: datetime


class BuyStockRequest(BaseModel):
    """Request DTO for buying stocks"""
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol (e.g., AAPL)")
    quantity: float = Field(..., gt=0, description="Number of shares to buy")
    price: float = Field(..., gt=0, description="Price per share")


class SellStockRequest(BaseModel):
    """Request DTO for selling stocks"""
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol (e.g., AAPL)")
    quantity: float = Field(..., gt=0, description="Number of shares to sell")
    price: float = Field(..., gt=0, description="Price per share")
