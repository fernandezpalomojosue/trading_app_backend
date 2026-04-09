"""
SignalEngineUseCases: Generates trading signals (buy/sell/hold) from technical indicators.

Rules:
- BUY: RSI < 30 (oversold) + MACD crosses above signal + Price > EMA
- SELL: RSI > 70 (overbought) + MACD crosses below signal + Price < EMA  
- HOLD: Otherwise
"""
from typing import List, Dict, Tuple, Optional
import math
from app.application.dto.indicators_dto import IndicatorDataPoint
from app.application.dto.signals_dto import SignalDataPoint
from datetime import datetime
from app.domain.services.fibonacci_service import FibonacciService

class SignalEngineUseCases:
    """Generates trading signals from technical indicator data"""
    
    def __init__(self):
        self.fibonacci_service = FibonacciService()

    def calculate_signals(self, symbol: str, data_points: List[IndicatorDataPoint]) -> List[SignalDataPoint]:
        """
        Calculate signals for a list of indicator data points.
        
        Args:
            data_points: List of dicts with keys: rsi, macd, signal, ema, close
            
        Returns:
            List of tuples: (signal, reason) where signal is "buy", "sell", or "hold"
        """
        results = []
        
        for i, point in enumerate(data_points):
            if i == 0:
                results.append(SignalDataPoint(symbol=symbol, timestamp=int(datetime.now().timestamp() * 1000), signal="hold", reason="HOLD: No previous data for MACD crossover detection", take_profit=1, stop_loss=1, confidence=1))
                continue
                
            prev_point = data_points[i - 1]
            signalpoint = self.calculate_single_signal(symbol, point, prev_point)
            results.append(signalpoint)
            
        return results

    def _calculate_dynamic_sl_tp(self, signal: str, current_price: float, 
                             fibonacci_levels: Dict[str, float]) -> Tuple[float, float]:
        """
        Calculate dynamic stop-loss and take-profit using Fibonacci levels
        
        Args:
            signal: 'buy' or 'sell' signal
            current_price: Current price
            fibonacci_levels: Dictionary of Fibonacci retracement levels
            
        Returns:
            Tuple of (stop_loss, take_profit)
        """
        if not fibonacci_levels:
            # Fallback to static 5% calculation
            stop_loss = current_price * 0.95
            take_profit = current_price * 1.05
            return stop_loss, take_profit
        
        if signal == "buy":
            # For buy signals: use nearest support below for SL, nearest resistance above for TP
            support_level = self.fibonacci_service.get_nearest_support_level(current_price, fibonacci_levels)
            resistance_level = self.fibonacci_service.get_nearest_resistance_level(current_price, fibonacci_levels)
            
            stop_loss = support_level if support_level else current_price * 0.95
            take_profit = resistance_level if resistance_level else current_price * 1.05
            
        elif signal == "sell":
            # For sell signals: use nearest resistance above for SL, nearest support below for TP
            resistance_level = self.fibonacci_service.get_nearest_resistance_level(current_price, fibonacci_levels)
            support_level = self.fibonacci_service.get_nearest_support_level(current_price, fibonacci_levels)
            
            stop_loss = resistance_level if resistance_level else current_price * 1.05
            take_profit = support_level if support_level else current_price * 0.95
            
        else:  # hold
            # Use static calculation for hold signals
            stop_loss = current_price * 0.95
            take_profit = current_price * 1.05
        
        return stop_loss, take_profit

    def calculate_single_signal(self, symbol: str, point: IndicatorDataPoint, prev_point: IndicatorDataPoint) -> SignalDataPoint:
        """Calculate signal for single point using previous point for crossover detection"""
        rsi = point.rsi
        macd = point.macd
        signal_line = point.macd_signal
        ema = point.ema
        close_price = point.close_price
        fibonacci_levels = point.fibonacci_levels
        confidence = 0.9
        # Check for missing/NaN values
        if any(v is None or (isinstance(v, float) and math.isnan(v)) 
               for v in [rsi, macd, signal_line, ema, close_price]):
            return SignalDataPoint(symbol=symbol, timestamp=int(datetime.now().timestamp() * 1000), signal="hold", reason="HOLD: Insufficient data (missing or invalid indicator values)", take_profit=close_price * 1.05, stop_loss=close_price * 0.95, confidence=confidence)
        
        prev_macd = prev_point.macd
        prev_signal = prev_point.macd_signal
        
        if prev_macd is None or prev_signal is None:
            return SignalDataPoint(symbol=symbol, timestamp=int(datetime.now().timestamp() * 1000), signal="hold", reason="HOLD: No previous MACD data for crossover detection", take_profit=close_price * 1.05, stop_loss=close_price * 0.95, confidence=confidence)
        
        macd_cross_up = macd > signal_line and prev_macd <= prev_signal
        macd_cross_down = macd < signal_line and prev_macd >= prev_signal
        
        # BUY conditions
        if rsi < 30 and macd_cross_up and close_price > ema:
            # Calculate dynamic SL/TP using Fibonacci
            stop_loss, take_profit = self._calculate_dynamic_sl_tp("buy", close_price, fibonacci_levels)
            
            reason = (f"BUY: RSI oversold ({rsi:.1f} < 30) + "
                     f"MACD crossed above signal ({macd:.3f} > {signal_line:.3f}) + "
                     f"Price above EMA ({close_price:.2f} > {ema:.2f})")
            return SignalDataPoint(symbol=symbol, timestamp=int(datetime.now().timestamp() * 1000), signal="buy", reason=reason, take_profit=take_profit, stop_loss=stop_loss, confidence=confidence)
        
        # SELL conditions  
        if rsi > 70 and macd_cross_down and close_price < ema:
            # Calculate dynamic SL/TP using Fibonacci
            stop_loss, take_profit = self._calculate_dynamic_sl_tp("sell", close_price, fibonacci_levels)
            
            reason = (f"SELL: RSI overbought ({rsi:.1f} > 70) + "
                     f"MACD crossed below signal ({macd:.3f} < {signal_line:.3f}) + "
                     f"Price below EMA ({close_price:.2f} < {ema:.2f})")
            return SignalDataPoint(symbol=symbol, timestamp=int(datetime.now().timestamp() * 1000), signal="sell", reason=reason, take_profit=take_profit, stop_loss=stop_loss, confidence=confidence)
        
        # HOLD - build detailed reason
        reasons = []
        if rsi >= 30 and rsi <= 70:
            reasons.append(f"RSI neutral ({rsi:.1f})")
        elif rsi < 30:
            reasons.append(f"RSI oversold ({rsi:.1f}) but other conditions not met")
        else:
            reasons.append(f"RSI overbought ({rsi:.1f}) but other conditions not met")
            
        if not macd_cross_up and not macd_cross_down:
            if macd > signal_line:
                reasons.append(f"MACD above signal but no crossover ({macd:.3f} > {signal_line:.3f})")
            else:
                reasons.append(f"MACD below signal but no crossover ({macd:.3f} < {signal_line:.3f})")
        
        if close_price > ema:
            reasons.append(f"Price above EMA ({close_price:.2f} > {ema:.2f})")
        else:
            reasons.append(f"Price below EMA ({close_price:.2f} < {ema:.2f})")
        
        # Calculate dynamic SL/TP for hold signals
        stop_loss, take_profit = self._calculate_dynamic_sl_tp("hold", close_price, fibonacci_levels)
        
        return SignalDataPoint(timestamp=int(datetime.now().timestamp() * 1000), symbol=symbol, signal="hold", reason="HOLD: " + " | ".join(reasons), take_profit=take_profit, stop_loss=stop_loss, confidence=confidence)
