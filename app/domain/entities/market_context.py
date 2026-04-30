# app/domain/entities/market_context.py
"""
Market Context for Strategy Evaluation

Contains OHLCV data and calculated indicators for a specific point in time.
Used by StrategyEngine as evaluation context for DSL conditions.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class MarketContext(BaseModel):
    """
    Market context for strategy evaluation at a specific timestamp.
    
    Contains:
    - OHLCV data (open, high, low, close, volume)
    - Calculated technical indicators (EMA, SMA, RSI, MACD)
    - Current timestamp and symbol
    - Fibonacci levels
    """
    
    # Symbol and timestamp
    symbol: str = Field(description="Stock symbol (e.g., AAPL, GOOGL)")
    timestamp: int = Field(description="Timestamp in milliseconds")
    
    # OHLCV data
    open_price: Optional[float] = Field(default=None, description="Open price")
    high_price: Optional[float] = Field(default=None, description="High price")
    low_price: Optional[float] = Field(default=None, description="Low price")
    close_price: Optional[float] = Field(default=None, description="Close price")
    volume: Optional[float] = Field(default=None, description="Volume")
    
    # Technical indicators
    ema: Optional[float] = Field(default=None, description="Exponential Moving Average")
    sma: Optional[float] = Field(default=None, description="Simple Moving Average")
    rsi: Optional[float] = Field(default=None, description="Relative Strength Index")
    macd: Optional[float] = Field(default=None, description="MACD line")
    macd_signal: Optional[float] = Field(default=None, description="MACD signal line")
    macd_histogram: Optional[float] = Field(default=None, description="MACD histogram")
    
    # Fibonacci levels
    fibonacci_levels: Dict[str, float] = Field(
        default_factory=dict,
        description="Fibonacci retracement levels"
    )
    
    @classmethod
    def from_indicator_point(cls, indicator_point) -> "MarketContext":
        """
        Create MarketContext from an IndicatorDataPoint.
        
        Args:
            indicator_point: IndicatorDataPoint with calculated indicators
            
        Returns:
            MarketContext populated with indicator data
        """
        return cls(
            symbol=indicator_point.symbol,
            timestamp=indicator_point.timestamp,
            close_price=indicator_point.close_price,
            ema=indicator_point.ema,
            sma=indicator_point.sma,
            rsi=indicator_point.rsi,
            macd=indicator_point.macd,
            macd_signal=indicator_point.macd_signal,
            macd_histogram=indicator_point.histogram,
            fibonacci_levels=indicator_point.fibonacci_levels or {}
        )
    
    def get_value(self, field: str) -> Optional[float]:
        """
        Get a value by field name.
        
        Supports:
        - price fields: open, high, low, close, volume
        - indicator fields: ema, sma, rsi, macd, macd_signal, macd_histogram
        
        Args:
            field: Field name to retrieve
            
        Returns:
            Float value or None if field not found
        """
        field_map = {
            # Price fields
            "open": self.open_price,
            "high": self.high_price,
            "low": self.low_price,
            "close": self.close_price,
            "volume": self.volume,
            # Indicator fields
            "ema": self.ema,
            "sma": self.sma,
            "rsi": self.rsi,
            "macd": self.macd,
            "signal": self.macd_signal,
            "histogram": self.macd_histogram,
        }
        return field_map.get(field)
