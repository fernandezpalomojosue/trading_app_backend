# app/application/dto/indicators_dto.py
from typing import List, Optional
from pydantic import BaseModel


class IndicatorDataPoint(BaseModel):
    """Combined data point with all technical indicators"""
    timestamp: int
    symbol: str
    ema: Optional[float]
    sma: Optional[float]
    rsi: Optional[float]
    macd: Optional[float]
    signal: Optional[float]
    histogram: Optional[float]
    close_price: Optional[float]
    fibonacci_levels: dict

