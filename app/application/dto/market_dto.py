# app/application/dto/market_dto.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

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
    volume: Optional[int]
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


class MarketMoversResponse(BaseModel):
    """DTO for market movers response"""
    gainers: List[MarketSummaryResponse]
    losers: List[MarketSummaryResponse]
    most_active: List[MarketSummaryResponse]


class SearchAssetsRequest(BaseModel):
    """DTO for asset search requests"""
    query: str = Field(..., min_length=2, description="Término de búsqueda")
    market_type: Optional[MarketType] = Field(None, description="Tipo de mercado")


class CacheStatsResponse(BaseModel):
    """DTO for cache statistics response"""
    entries: int
    memory_usage: Optional[str] = None
    hit_rate: Optional[float] = None
    additional_info: Dict[str, Any] = Field(default_factory=dict)
