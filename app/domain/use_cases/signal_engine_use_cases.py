"""
SignalEngineUseCases: Generates trading signals (buy/sell/hold) from technical indicators.

Rules:
- BUY: RSI < 30 (oversold) + MACD crosses above signal + Price > EMA
- SELL: RSI > 70 (overbought) + MACD crosses below signal + Price < EMA  
- HOLD: Otherwise
"""
from typing import List, Dict, Tuple
import math
from app.application.dto.indicators_dto import IndicatorDataPoint
from app.application.dto.signals_dto import SignalDataPoint


class SignalEngineUseCases:
    """Generates trading signals from technical indicator data"""

    def calculate_signals(self, data_points: List[IndicatorDataPoint]) -> List[SignalDataPoint]:
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
                results.append(SignalDataPoint(signal="hold", reason="HOLD: No previous data for MACD crossover detection"))
                continue
                
            prev_point = data_points[i - 1]
            signal, reason = self.calculate_single_signal(point, prev_point)
            results.append(SignalDataPoint(signal=signal, reason=reason))
            
        return results

    def calculate_single_signal(self, point: Dict, prev_point: Dict) -> SignalDataPoint:
        """Calculate signal for single point using previous point for crossover detection"""
        rsi = point.get("rsi")
        macd = point.get("macd")
        signal_line = point.get("signal")
        ema = point.get("ema")
        close_price = point.get("close")
        
        # Check for missing/NaN values
        if any(v is None or (isinstance(v, float) and math.isnan(v)) 
               for v in [rsi, macd, signal_line, ema, close_price]):
            return SignalDataPoint(signal="hold", reason="HOLD: Insufficient data (missing or invalid indicator values)")
        
        prev_macd = prev_point.get("macd")
        prev_signal = prev_point.get("signal")
        
        if prev_macd is None or prev_signal is None:
            return SignalDataPoint(signal="hold", reason="HOLD: No previous MACD data for crossover detection")
        
        macd_cross_up = macd > signal_line and prev_macd <= prev_signal
        macd_cross_down = macd < signal_line and prev_macd >= prev_signal
        
        # BUY conditions
        if rsi < 30 and macd_cross_up and close_price > ema:
            reason = (f"BUY: RSI oversold ({rsi:.1f} < 30) + "
                     f"MACD crossed above signal ({macd:.3f} > {signal_line:.3f}) + "
                     f"Price above EMA ({close_price:.2f} > {ema:.2f})")
            return SignalDataPoint(signal="buy", reason=reason)
        
        # SELL conditions  
        if rsi > 70 and macd_cross_down and close_price < ema:
            reason = (f"SELL: RSI overbought ({rsi:.1f} > 70) + "
                     f"MACD crossed below signal ({macd:.3f} < {signal_line:.3f}) + "
                     f"Price below EMA ({close_price:.2f} < {ema:.2f})")
            return SignalDataPoint(signal="sell", reason=reason)
        
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
        
        return SignalDataPoint(signal="hold", reason="HOLD: " + " | ".join(reasons))
