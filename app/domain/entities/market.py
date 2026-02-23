# app/domain/entities/market.py
from enum import Enum
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class MarketType(str, Enum):
    STOCKS = "stocks"
    CRYPTO = "crypto"
    FX = "fx"
    INDICES = "indices"


class Asset(BaseModel):
    """Core asset entity - pure business logic"""
    id: str
    symbol: str
    name: str
    market: MarketType
    currency: str
    active: bool = True
    price: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    
    def is_tradable(self) -> bool:
        """Check if asset is available for trading"""
        return self.active and self.price is not None


class MarketSummary(BaseModel):
    """Market summary entity"""
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    timestamp: Optional[datetime] = None
    
    @property
    def is_positive(self) -> bool:
        return (self.change or 0) > 0
    
    @property
    def price_range(self) -> float:
        return self.high - self.low


class CandleStick(BaseModel):
    """Candlestick data for charting - OHLCV format"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    
    @property
    def is_green(self) -> bool:
        """Check if candle is bullish (close > open)"""
        return self.close > self.open
    
    @property
    def is_red(self) -> bool:
        """Check if candle is bearish (close < open)"""
        return self.close < self.open
    
    @property
    def body_size(self) -> float:
        """Size of the candle body"""
        return abs(self.close - self.open)
    
    @property
    def upper_wick(self) -> float:
        """Upper shadow/wick size"""
        return self.high - max(self.open, self.close)
    
    @property
    def lower_wick(self) -> float:
        """Lower shadow/wick size"""
        return min(self.open, self.close) - self.low
    
    @property
    def price_range(self) -> float:
        """Total price range (high - low)"""
        return self.high - self.low
