# app/application/dto/market_dto.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

from app.domain.entities.market import MarketType


class AssetResponse(BaseModel):
    """DTO for asset responses"""
    id: str
    symbol: str
    name: str
    market: MarketType
    currency: str
    active: bool
    price: Optional[float]
    change: Optional[float]
    change_percent: Optional[float]
    volume: Optional[float]
    details: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class MarketSummaryResponse(BaseModel):
    """DTO for market summary responses"""
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: Optional[float]
    change: Optional[float]
    change_percent: Optional[float]
    
    class Config:
        from_attributes = True


class MarketOverviewResponse(BaseModel):
    """DTO for market overview responses"""
    market: MarketType
    total_assets: int
    status: str
    last_updated: str
    top_gainers: List[MarketSummaryResponse] = []
    top_losers: List[MarketSummaryResponse] = []
    most_active: List[MarketSummaryResponse] = []
    
    class Config:
        from_attributes = True


class CandleData(BaseModel):
    """Individual candle data in frontend format"""
    t: int  # Timestamp in milliseconds
    c: float  # Close price
    o: float  # Open price
    h: float  # High price
    l: float  # Low price
    v: int   # Volume


class CandleStickDataResponse(BaseModel):
    """DTO for candlestick data response in frontend format"""
    results: List[CandleData]


class FavoriteStockRequest(BaseModel):
    """DTO for adding a stock to favorites"""
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol (e.g., AAPL, GOOGL)")
    
    class Config:
        from_attributes = True


class FavoriteStockResponse(BaseModel):
    """DTO for favorite stock response"""
    id: str
    user_id: str
    symbol: str
    created_at: str
    
    class Config:
        from_attributes = True


class FavoriteStockListResponse(BaseModel):
    """DTO for list of favorite stocks"""
    favorites: List[FavoriteStockResponse] = []
    total: int = 0
    
    class Config:
        from_attributes = True
