# app/domain/entities/market_snapshot.py
"""
Market Snapshot Entity

Represents a reusable indicator snapshot for a specific (symbol, timeframe) combination.
Used as shared input for all strategy evaluations in Phase 4 optimization.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from app.application.dto.indicators_dto import IndicatorDataPoint
import logging

logger = logging.getLogger(__name__)


class MarketSnapshot(BaseModel):
    """
    Market snapshot for strategy evaluation.
    
    Represents a precomputed indicator snapshot for a specific symbol and timeframe.
    This becomes the shared input for all strategy evaluations, eliminating redundant
    market data fetching and indicator calculations.
    
    Attributes:
        symbol: Stock symbol (e.g., AAPL, GOOGL)
        timeframe: Timeframe for this snapshot (day, hour, minute, etc.)
        indicators: List of indicator data points (chronological order, newest last)
        open_price: Open price from latest indicator
        high_price: High price from latest indicator
        low_price: Low price from latest indicator
        close_price: Close price from latest indicator
        volume: Volume from latest indicator
        ema: Exponential Moving Average from latest indicator
        sma: Simple Moving Average from latest indicator
        rsi: Relative Strength Index from latest indicator
        macd: MACD line from latest indicator
        macd_signal: MACD signal line from latest indicator
        macd_histogram: MACD histogram from latest indicator
        fibonacci_levels: Fibonacci retracement levels from latest indicator
    """
    
    symbol: str = Field(description="Stock symbol (e.g., AAPL, GOOGL)")
    timeframe: str = Field(description="Timeframe for this snapshot (day, hour, minute, etc.)")
    indicators: List[IndicatorDataPoint] = Field(description="List of indicator data points in chronological order")
    timestamp: Optional[int] = Field(default=None, description="Timestamp from latest indicator (milliseconds)")
    
    # OHLCV data from latest indicator
    open_price: Optional[float] = Field(default=None, description="Open price from latest indicator")
    high_price: Optional[float] = Field(default=None, description="High price from latest indicator")
    low_price: Optional[float] = Field(default=None, description="Low price from latest indicator")
    close_price: Optional[float] = Field(default=None, description="Close price from latest indicator")
    volume: Optional[float] = Field(default=None, description="Volume from latest indicator")
    
    # Technical indicators from latest indicator
    ema: Optional[float] = Field(default=None, description="Exponential Moving Average")
    sma: Optional[float] = Field(default=None, description="Simple Moving Average")
    rsi: Optional[float] = Field(default=None, description="Relative Strength Index")
    macd: Optional[float] = Field(default=None, description="MACD line")
    macd_signal: Optional[float] = Field(default=None, description="MACD signal line")
    macd_histogram: Optional[float] = Field(default=None, description="MACD histogram")
    
    # Fibonacci levels from latest indicator
    fibonacci_levels: Dict[str, float] = Field(
        default_factory=dict,
        description="Fibonacci retracement levels from latest indicator"
    )
    
    @property
    def unique_key(self) -> tuple:
        """
        Get the unique key for this snapshot.
        
        Returns:
            Tuple of (symbol, timeframe) used as dictionary key
        """
        return (self.symbol, self.timeframe)
    
    def has_valid_data(self) -> bool:
        """
        Check if snapshot has valid indicator data.
        
        Returns:
            True if snapshot has at least 2 indicator points with valid data
        """
        return (
            len(self.indicators) >= 2
            and self.indicators[-1] is not None 
            and self.indicators[-2] is not None
            and self.indicators[-1].timestamp > self.indicators[-2].timestamp
            and self.close_price is not None
        )
    
    def get_evaluation_context(self) -> tuple:
        """
        Get MarketSnapshot objects for current and previous points for strategy evaluation.
        
        Returns:
            Tuple of (current_snapshot, previous_snapshot) for strategy evaluation
        """
        if len(self.indicators) < 2:
            raise ValueError("Insufficient indicator data for evaluation")
        
        current_snapshot = self.get_point(0)
        previous_snapshot = self.get_point(1)
        
        return current_snapshot, previous_snapshot
    
    @property
    def current_point(self) -> IndicatorDataPoint:
        """
        Get the current (most recent) indicator point.
        
        Returns:
            The most recent indicator data point
        """
        if not self.indicators:
            raise ValueError("No indicator data available")
        return self.indicators[-1]
    
    @property
    def previous_point(self) -> IndicatorDataPoint:
        """
        Get the previous indicator point.
        
        Returns:
            The previous indicator data point
        """
        if len(self.indicators) < 2:
            raise ValueError("Insufficient indicator data for previous point")
        return self.indicators[-2]
    
    def get_last_n_points(self, count: int) -> List[IndicatorDataPoint]:
        """
        Get the last N indicator points for historical analysis.
        
        Args:
            count: Number of historical points to return
            
        Returns:
            List of the last N indicator points (newest first)
        """
        if count <= 0:
            return []
        
        return self.indicators[-count:] if len(self.indicators) >= count else self.indicators.copy()

    
    def get_value(self, field: str) -> Optional[float]:
        """
        Get price field value from latest indicator.
        
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
    
    def get_point(self, offset: int) -> "MarketSnapshot":
        """
        Get a MarketSnapshot for a specific historical offset.
        
        Args:
            offset: Offset from current (0 = current, 1 = previous, etc.)
            
        Returns:
            MarketSnapshot with data from the specified offset
        """
        if offset < 0 or offset >= len(self.indicators):
            raise ValueError(f"Offset {offset} out of range for indicators")
        
        historical_index = -(offset + 1)
        indicator_point = self.indicators[historical_index]
        
        # Create a new snapshot with only the historical point
        return MarketSnapshot(
            symbol=self.symbol,
            timeframe=self.timeframe,
            indicators=[indicator_point],
            timestamp=indicator_point.timestamp,
            open_price=indicator_point.open_price,
            high_price=indicator_point.high_price,
            low_price=indicator_point.low_price,
            close_price=indicator_point.close_price,
            volume=indicator_point.volume,
            ema=indicator_point.ema,
            sma=indicator_point.sma,
            rsi=indicator_point.rsi,
            macd=indicator_point.macd,
            macd_signal=indicator_point.macd_signal,
            macd_histogram=indicator_point.histogram,
            fibonacci_levels=indicator_point.fibonacci_levels or {}
        )
    
    def _populate_from_latest_indicator(self) -> None:
        """
        Populate individual fields from the latest indicator point.
        This is called internally after initialization.
        """
        if not self.indicators:
            return
        
        latest = self.indicators[-1]
        self.timestamp = latest.timestamp
        self.open_price = latest.open_price
        self.high_price = latest.high_price
        self.low_price = latest.low_price
        self.close_price = latest.close_price
        self.volume = latest.volume
        self.ema = latest.ema
        self.sma = latest.sma
        self.rsi = latest.rsi
        self.macd = latest.macd
        self.macd_signal = latest.macd_signal
        self.macd_histogram = latest.histogram
        self.fibonacci_levels = latest.fibonacci_levels or {}
    
    def model_post_init(self, __context: any) -> None:
        """
        Pydantic post-init hook to populate fields from latest indicator.
        """
        self._populate_from_latest_indicator()
