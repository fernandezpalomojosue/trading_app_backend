# app/application/dto/indicators_dto.py
from typing import List
from pydantic import BaseModel


class EMADataPoint(BaseModel):
    """Individual EMA data point"""
    t: int  # Timestamp in milliseconds
    v: float  # EMA value


class EMAResponse(BaseModel):
    """DTO for EMA indicator response"""
    symbol: str
    window: int
    timespan: str
    results: List[EMADataPoint]


class SMADataPoint(BaseModel):
    """Individual SMA data point"""
    t: int  # Timestamp in milliseconds
    v: float  # SMA value


class SMAResponse(BaseModel):
    """DTO for SMA indicator response"""
    symbol: str
    window: int
    timespan: str
    results: List[SMADataPoint]


class RSIDataPoint(BaseModel):
    """Individual RSI data point"""
    t: int  # Timestamp in milliseconds
    v: float  # RSI value (0-100)


class RSIResponse(BaseModel):
    """DTO for RSI indicator response"""
    symbol: str
    window: int
    timespan: str
    results: List[RSIDataPoint]


class MACDDataPoint(BaseModel):
    """Individual MACD data point"""
    t: int  # Timestamp in milliseconds
    macd: float  # MACD line value
    signal: float  # Signal line value
    histogram: float  # Histogram value (macd - signal)


class MACDResponse(BaseModel):
    """DTO for MACD indicator response"""
    symbol: str
    fast: int  # Fast EMA window
    slow: int  # Slow EMA window
    signal_period: int  # Signal EMA window
    timespan: str
    results: List[MACDDataPoint]
