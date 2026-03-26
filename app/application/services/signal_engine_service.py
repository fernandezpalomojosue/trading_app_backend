# app/application/services/signal_engine_service.py
"""
SignalEngineService: Generates trading signals (buy/sell/hold) from technical indicators.

Rules:
- BUY: RSI < 30 (oversold) + MACD crosses above signal + Price > EMA
- SELL: RSI > 70 (overbought) + MACD crosses below signal + Price < EMA  
- HOLD: Otherwise
"""
from typing import List, Dict
import math
from abc import ABC, abstractmethod


class SignalEngineServiceInterface(ABC):
    """Abstract interface for signal engine service"""
    
    @abstractmethod
    def calculate_signals(self, data_points: List[Dict]) -> List[str]:
        """Calculate signals for a list of indicator data points"""
        pass


class SignalEngineService(SignalEngineServiceInterface):
    """Generates trading signals from technical indicator data"""

    def calculate_signals(self, data_points: List[Dict]) -> List[str]:
        """
        Calculate signals for a list of indicator data points.
        
        Args:
            data_points: List of dicts with keys: rsi, macd, signal, ema, c/close
            
        Returns:
            List of signals: "buy", "sell", or "hold"
        """
        signals = []
        
        for i, point in enumerate(data_points):
            if i == 0:
                signals.append("hold")
                continue
                
            prev_point = data_points[i - 1]
            signal = self._calculate_single_signal(point, prev_point)
            signals.append(signal)
            
        return signals

    def _calculate_single_signal(self, point: Dict, prev_point: Dict) -> str:
        """Calculate signal for single point using previous point for crossover detection"""
        rsi = point.get("rsi")
        macd = point.get("macd")
        signal_line = point.get("signal")
        ema = point.get("ema")
        close_price = point.get("c") or point.get("close")
        
        if any(v is None or (isinstance(v, float) and math.isnan(v)) 
               for v in [rsi, macd, signal_line, ema, close_price]):
            return "hold"
        
        prev_macd = prev_point.get("macd")
        prev_signal = prev_point.get("signal")
        
        if prev_macd is None or prev_signal is None:
            return "hold"
        
        macd_cross_up = macd > signal_line and prev_macd <= prev_signal
        macd_cross_down = macd < signal_line and prev_macd >= prev_signal
        
        if rsi < 30 and macd_cross_up and close_price > ema:
            return "buy"
        
        if rsi > 70 and macd_cross_down and close_price < ema:
            return "sell"
        
        return "hold"
