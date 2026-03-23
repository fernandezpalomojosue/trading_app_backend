# app/application/services/indicators_service.py
from abc import ABC, abstractmethod
from typing import Optional

from app.application.dto.indicators_dto import (
    EMAResponse,
    SMAResponse,
    RSIResponse,
    MACDResponse
)


class IndicatorsService(ABC):
    """Application interface for technical indicators operations"""
    
    @abstractmethod
    async def get_ema(
        self,
        symbol: str,
        window: int,
        timespan: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> EMAResponse:
        """Get EMA (Exponential Moving Average) indicator data"""
        pass
    
    @abstractmethod
    async def get_sma(
        self,
        symbol: str,
        window: int,
        timespan: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> SMAResponse:
        """Get SMA (Simple Moving Average) indicator data"""
        pass
    
    @abstractmethod
    async def get_rsi(
        self,
        symbol: str,
        window: int,
        timespan: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> RSIResponse:
        """Get RSI (Relative Strength Index) indicator data"""
        pass
    
    @abstractmethod
    async def get_macd(
        self,
        symbol: str,
        fast: int,
        slow: int,
        signal: int,
        timespan: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> MACDResponse:
        """Get MACD (Moving Average Convergence Divergence) indicator data"""
        pass
