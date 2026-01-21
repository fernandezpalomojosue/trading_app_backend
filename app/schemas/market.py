# app/schemas/market.py
from enum import Enum
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class MarketType(str, Enum):
    STOCKS = "stocks"
    CRYPTO = "crypto"
    FX = "fx"
    INDICES = "indices"

class MarketSummary(BaseModel):
    """Modelo para el resumen de un activo en el mercado"""
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None

class MarketOverview(BaseModel):
    """Modelo para el resumen de mercado"""
    market: MarketType
    total_assets: int
    status: str
    last_updated: datetime
    top_gainers: List[MarketSummary] = []
    top_losers: List[MarketSummary] = []
    most_active: List[MarketSummary] = []

class Asset(BaseModel):
    """Modelo para representar un activo financiero"""
    id: str
    symbol: str
    name: str
    market: MarketType
    currency: str
    active: bool
    price: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detalles adicionales del activo"
    )

    class Config:
        schema_extra = {
            "example": {
                "id": "aapl",
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "market": "stocks",
                "currency": "USD",
                "active": True,
                "details": {}
            }
        }