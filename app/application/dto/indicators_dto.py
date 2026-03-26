# app/application/dto/indicators_dto.py
from typing import List, Optional
from pydantic import BaseModel


class CombinedIndicatorDataPoint(BaseModel):
    """Combined data point with all technical indicators"""
    t: int  # Timestamp in milliseconds
    ema: float  # EMA value
    sma: float  # SMA value
    rsi: float  # RSI value (0-100)
    macd: float  # MACD line value
    signal: float  # Signal line value
    histogram: float  # Histogram value (macd - signal)
    order_signal: Optional[str] = None  # Future field for trading signals (buy/sell/hold)


class CombinedIndicatorsResponse(BaseModel):
    """DTO for combined indicators response"""
    symbol: str
    results: List[CombinedIndicatorDataPoint]
