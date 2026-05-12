# app/domain/entities/market_context.py
"""
Market Context for Strategy Evaluation

Contains OHLCV data and calculated indicators for a specific point in time.
Used by StrategyEngine as evaluation context for DSL conditions.
"""
from typing import Optional, Dict, Any, List
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
    
    # Historical data for offset support
    historical_indicators: List = Field(
        default_factory=list,
        description="List of historical indicator data points for offset calculations"
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
    
    def get_price(self, field: str) -> Optional[float]:
        """
        Get price field value.
        
        Args:
            field: Field name ('open', 'high', 'low', 'close', 'volume')
            
        Returns:
            Field value or None if not available
        """
        if field == "open":
            return self.open_price
        elif field == "high":
            return self.high_price
        elif field == "low":
            return self.low_price
        elif field == "close":
            return self.close_price
        elif field == "volume":
            return self.volume
        else:
            logger.warning(f"Unknown price field: {field}")
            return None
    
    @classmethod
    def from_snapshot(cls, market_snapshot: 'MarketSnapshot', index: int = -1) -> "MarketContext":
        """
        Create MarketContext from MarketSnapshot at specific index.
        
        Args:
            market_snapshot: MarketSnapshot with historical indicators
            index: Index in indicators list (-1 for latest, 0 for first)
            
        Returns:
            MarketContext populated with indicator data at specified index
        """
        if not market_snapshot.indicators:
            raise ValueError("MarketSnapshot has no indicators")
        
        if index == -1:
            # Latest indicator
            indicator_point = market_snapshot.indicators[-1]
        else:
            # Specific index
            if index < 0 or index >= len(market_snapshot.indicators):
                raise ValueError(f"Index {index} out of range for indicators")
            indicator_point = market_snapshot.indicators[index]
        
        return cls.from_indicator_point(indicator_point)
    
    def with_snapshot(self, market_snapshot: 'MarketSnapshot') -> "MarketContext":
        """
        Create a new MarketContext with MarketSnapshot attached for offset support.
        
        Args:
            market_snapshot: MarketSnapshot with historical indicators
            
        Returns:
            MarketContext with _market_snapshot attribute for historical access
        """
        # Create context from latest indicator point
        context = self.from_indicator_point(market_snapshot.indicators[-1])
        
        # Attach snapshot for historical access
        context._market_snapshot = market_snapshot
        
        return context
        return field_map.get(field)
