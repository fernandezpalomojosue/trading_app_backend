"""
SignalEngineServiceInterface: Abstract interface for signal generation.

Rules:
- BUY: RSI < 30 (oversold) + MACD crosses above signal + Price > EMA
- SELL: RSI > 70 (overbought) + MACD crosses below signal + Price < EMA  
- HOLD: Otherwise
"""
from typing import List, Dict, Tuple
from abc import ABC, abstractmethod


class SignalEngineServiceInterface(ABC):
    """Abstract interface for signal engine service"""
    
    @abstractmethod
    def calculate_signals(self, data_points: List[Dict]) -> List[Tuple[str, str]]:
        """Calculate signals for a list of indicator data points, returns (signal, reason)"""
        pass
