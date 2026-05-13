# app/application/dto/indicators_dto.py
from typing import Optional, Dict
from pydantic import BaseModel, Field


class IndicatorDataPoint(BaseModel):
    """Combined data point with all technical indicators and OHLCV data"""
    timestamp: int
    symbol: str
    
    # OHLCV data
    open_price: Optional[float] = Field(default=None, description="Open price")
    high_price: Optional[float] = Field(default=None, description="High price")
    low_price: Optional[float] = Field(default=None, description="Low price")
    close_price: Optional[float] = Field(default=None, description="Close price")
    volume: Optional[float] = Field(default=None, description="Volume")
    
    # Technical indicators
    ema: Optional[float] = Field(default=None, description="Exponential Moving Average")
    sma: Optional[float] = Field(default=None, description="Simple Moving Average")
    rsi: Optional[float] = Field(default=None, description="Relative Strength Index")
    macd: Optional[float] = Field(default=None, description="MACD line")
    macd_signal: Optional[float] = Field(default=None, description="MACD signal line")
    histogram: Optional[float] = Field(default=None, description="MACD histogram")
    
    # Fibonacci levels
    fibonacci_levels: Dict[str, float] = Field(default_factory=dict, description="Fibonacci retracement levels")

