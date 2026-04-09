# app/domain/services/fibonacci_service.py
from typing import Dict, Tuple, Optional, List, Any
import logging

logger = logging.getLogger(__name__)


class FibonacciService:
    """Service for calculating Fibonacci retracement levels from OHLC data"""
    
    # Standard Fibonacci retracement levels
    LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786]
    
    def __init__(self, min_bars: int = 10):
        self.min_bars = min_bars
    
    def calculate_fibonacci_levels(self, data: List[Dict[str, Any]]) -> Tuple[Dict[str, float], Optional[int], Optional[int]]:
        """
        Calculate Fibonacci retracement levels from OHLC data
        
        Args:
            data: List of dictionaries with keys 'h', 'l', 't' (high, low, timestamp)
            
        Returns:
            Tuple of (fibonacci_levels_dict, high_timestamp, low_timestamp)
            Returns empty dict and None timestamps if insufficient data
        """
        if len(data) < self.min_bars:
            logger.warning(f"Insufficient data for Fibonacci calculation: {len(data)} < {self.min_bars}")
            return {}, None, None
        
        # Find highest high and lowest low
        high_values = [item['h'] for item in data]
        low_values = [item['l'] for item in data]
        high = max(high_values)
        low = min(low_values)
        
        # Handle edge case where high == low (no price movement)
        if high == low:
            logger.warning("No price movement detected (high == low), cannot calculate Fibonacci levels")
            return {}, None, None
        
        # Get timestamps for high and low
        high_item = max(data, key=lambda x: x['h'])
        low_item = min(data, key=lambda x: x['l'])
        high_ts = high_item['t']
        low_ts = low_item['t']
        
        # Calculate retracement levels
        levels = {}
        for level in self.LEVELS:
            retracement = high - (high - low) * level
            levels[str(level)] = round(retracement, 4)  # Round to 4 decimal places
        
        logger.debug(f"Calculated Fibonacci levels: high={high}, low={low}, levels={levels}")
        
        return levels, int(high_ts), int(low_ts)
    
    def should_recalculate(self, current_high_ts: int, current_low_ts: int, 
                          cached_high_ts: int, cached_low_ts: int) -> bool:
        """
        Determine if Fibonacci levels should be recalculated based on timestamp comparison
        
        Args:
            current_high_ts: Current highest high timestamp
            current_low_ts: Current lowest low timestamp  
            cached_high_ts: Cached highest high timestamp
            cached_low_ts: Cached lowest low timestamp
            
        Returns:
            True if recalculation is needed, False otherwise
        """
        # Recalculate if either high or low timestamp has changed
        should_recalc = (current_high_ts != cached_high_ts) or (current_low_ts != cached_low_ts)
        
        if should_recalc:
            logger.debug(f"Fibonacci recalculation needed: "
                        f"high_ts {current_high_ts} vs {cached_high_ts}, "
                        f"low_ts {current_low_ts} vs {cached_low_ts}")
        
        return should_recalc
    
    def get_nearest_support_level(self, current_price: float, fibonacci_levels: Dict[str, float]) -> Optional[float]:
        """
        Find the nearest Fibonacci support level below current price
        
        Args:
            current_price: Current price
            fibonacci_levels: Dictionary of Fibonacci levels
            
        Returns:
            Nearest support level or None if no support found
        """
        support_levels = [level for level in fibonacci_levels.values() if level < current_price]
        
        if not support_levels:
            return None
        
        return max(support_levels)  # Highest level below price
    
    def get_nearest_resistance_level(self, current_price: float, fibonacci_levels: Dict[str, float]) -> Optional[float]:
        """
        Find the nearest Fibonacci resistance level above current price
        
        Args:
            current_price: Current price
            fibonacci_levels: Dictionary of Fibonacci levels
            
        Returns:
            Nearest resistance level or None if no resistance found
        """
        resistance_levels = [level for level in fibonacci_levels.values() if level > current_price]
        
        if not resistance_levels:
            return None
        
        return min(resistance_levels)  # Lowest level above price
