"""
SignalEngineUseCases: Signal construction layer (NO hardcoded rules).

Receives evaluation results from StrategyEngine and builds SignalDataPoint objects.
Uses explicit action from strategy DSL - system does NOT decide signal type.
"""
from typing import List, Dict, Tuple, Optional, Literal
import math
from uuid import UUID
from app.application.dto.indicators_dto import IndicatorDataPoint
from app.application.dto.signals_dto import SignalDataPoint
from datetime import datetime
from app.domain.services.fibonacci_service import FibonacciService
from app.application.services.signal_engine_service import SignalEngineService


class SignalEngineUseCases(SignalEngineService):
    """
    Signal construction layer - NO hardcoded trading rules.
    
    Receives:
    - condition_met: bool (from StrategyEngine)
    - action: str (from strategy DSL - buy/sell/hold)
    
    Returns:
    - SignalDataPoint with proper SL/TP and metadata
    
    The system does NOT decide signal type - it only executes what the strategy defines.
    """
    
    def __init__(self):
        self.fibonacci_service = FibonacciService()
    
    async def calculate_single_signal(
        self, 
        symbol: str,
        point: IndicatorDataPoint,
        prev_point: Optional[IndicatorDataPoint],
        strategy_id: UUID,
        condition_met: bool,
        action: Literal["buy", "sell", "hold"],
        strategy_name: str = "Unknown"
    ) -> SignalDataPoint:
        """
        Build signal based on StrategyEngine evaluation and explicit DSL action.
        
        Args:
            symbol: Stock symbol
            point: Current indicator data point
            prev_point: Previous indicator data point (for crossover context)
            strategy_id: ID of the strategy that generated this signal
            condition_met: Whether strategy conditions were met (from StrategyEngine)
            action: Explicit action from strategy DSL (buy/sell/hold)
            strategy_name: Name of the strategy for logging
            
        Returns:
            SignalDataPoint with signal details
            
        Logic:
        - If condition_met is True → use action from DSL
        - If condition_met is False → always "hold"
        """
        close_price = point.close_price or 0.0
        fibonacci_levels = point.fibonacci_levels or {}
        confidence = self._calculate_confidence(point)
        timestamp = point.timestamp or int(datetime.now().timestamp() * 1000)
        
        # Check for missing/invalid indicator values
        if self._has_invalid_data(point):
            return SignalDataPoint(
                symbol=symbol,
                timestamp=timestamp,
                signal="hold",
                reason="HOLD: Insufficient or invalid indicator data",
                take_profit=close_price * 1.05,
                stop_loss=close_price * 0.95,
                confidence=confidence,
                strategy_id=strategy_id
            )
        
        # System does NOT decide - it uses explicit action from DSL
        if condition_met:
            signal_type = action  # Use explicit action from strategy DSL
            stop_loss, take_profit = self._calculate_dynamic_sl_tp(signal_type, close_price, fibonacci_levels)
            reason = f"{signal_type.upper()}: Strategy '{strategy_name}' conditions met"
        else:
            signal_type = "hold"
            stop_loss, take_profit = self._calculate_dynamic_sl_tp("hold", close_price, fibonacci_levels)
            reason = f"HOLD: Strategy '{strategy_name}' conditions not met"
        
        return SignalDataPoint(
            timestamp=timestamp,
            symbol=symbol,
            signal=signal_type,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=confidence,
            reason=reason,
            strategy_id=strategy_id
        )
    
    def _has_invalid_data(self, point: IndicatorDataPoint) -> bool:
        """Check if indicator data has missing or NaN values."""
        required_fields = [point.rsi, point.macd, point.macd_signal, point.ema, point.close_price]
        return any(v is None or (isinstance(v, float) and math.isnan(v)) for v in required_fields)
    
    def _calculate_confidence(self, point: IndicatorDataPoint) -> float:
        """Calculate confidence level based on indicator strength."""
        # Simple confidence calculation - can be enhanced
        confidence = 0.9
        
        # Adjust based on indicator clarity
        if point.rsi is not None:
            # Higher confidence when RSI is extreme (far from 50)
            rsi_distance = abs(point.rsi - 50)
            if rsi_distance > 30:
                confidence = min(0.95, confidence + 0.05)
        
        return confidence
    
    def _calculate_dynamic_sl_tp(
        self, 
        signal: str, 
        current_price: float, 
        fibonacci_levels: Dict[str, float]
    ) -> Tuple[float, float]:
        """
        Calculate dynamic stop-loss and take-profit using Fibonacci levels.
        
        Args:
            signal: 'buy', 'sell', or 'hold'
            current_price: Current price
            fibonacci_levels: Dictionary of Fibonacci retracement levels
            
        Returns:
            Tuple of (stop_loss, take_profit)
        """
        if not fibonacci_levels:
            # Fallback to static 5% calculation
            if signal == "sell":
                return current_price * 1.05, current_price * 0.95
            else:  # buy or hold
                return current_price * 0.95, current_price * 1.05
        
        if signal == "buy":
            # For buy: use nearest support below for SL, nearest resistance above for TP
            support = self.fibonacci_service.get_nearest_support_level(current_price, fibonacci_levels)
            resistance = self.fibonacci_service.get_nearest_resistance_level(current_price, fibonacci_levels)
            stop_loss = support if support else current_price * 0.95
            take_profit = resistance if resistance else current_price * 1.05
            
        elif signal == "sell":
            # For sell: use nearest resistance above for SL, nearest support below for TP
            resistance = self.fibonacci_service.get_nearest_resistance_level(current_price, fibonacci_levels)
            support = self.fibonacci_service.get_nearest_support_level(current_price, fibonacci_levels)
            stop_loss = resistance if resistance else current_price * 1.05
            take_profit = support if support else current_price * 0.95
            
        else:  # hold
            stop_loss = current_price * 0.95
            take_profit = current_price * 1.05
        
        return stop_loss, take_profit
