"""
SignalEngineServiceInterface: Abstract interface for signal generation.

Rules:
- BUY: RSI < 30 (oversold) + MACD crosses above signal + Price > EMA
- SELL: RSI > 70 (overbought) + MACD crosses below signal + Price < EMA  
- HOLD: Otherwise
"""
from typing import List
from abc import ABC, abstractmethod
from app.application.dto.indicators_dto import IndicatorDataPoint
from app.application.dto.signals_dto import SignalDataPoint


class SignalEngineService(ABC):
    """Abstract interface for signal engine service"""
    
    @abstractmethod
    async def calculate_signals(self, symbol: str, data_points: List[IndicatorDataPoint]) -> List[SignalDataPoint]:
        """Calculate signals for a list of indicator data points, returns (signal, reason)"""
        pass
    
    @abstractmethod
    async def calculate_single_signal(self, symbol: str, point: IndicatorDataPoint, prev_point: IndicatorDataPoint) -> SignalDataPoint:
        """Calculate signal for single point using previous point for crossover detection"""
        pass