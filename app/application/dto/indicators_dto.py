# app/application/dto/indicators_dto.py
from typing import List, Optional
from pydantic import BaseModel


class IndicatorDataPoint(BaseModel):
    """Combined data point with all technical indicators"""
    timestamp: int
    symbol: str
    ema: float
    sma: float
    rsi: float
    macd: float
    signal: float
    histogram: float
    fibonacci_levels: dict

