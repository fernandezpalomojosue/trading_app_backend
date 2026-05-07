# app/domain/entities/market_snapshot.py
"""
Market Snapshot Entity

Represents a reusable indicator snapshot for a specific (symbol, timeframe) combination.
Used as shared input for all strategy evaluations in Phase 4 optimization.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from app.application.dto.indicators_dto import IndicatorDataPoint


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
    """
    
    symbol: str = Field(description="Stock symbol (e.g., AAPL, GOOGL)")
    timeframe: str = Field(description="Timeframe for this snapshot (day, hour, minute, etc.)")
    indicators: List[IndicatorDataPoint] = Field(description="List of indicator data points in chronological order")
    
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
        )
    
    def get_evaluation_context(self):
        """
        Get MarketContext objects for strategy evaluation.
        
        Returns:
            Tuple of (current_context, previous_context) for strategy evaluation
        """
        from app.domain.entities.market_context import MarketContext
        
        if len(self.indicators) < 2:
            raise ValueError("Insufficient indicator data for evaluation")
        
        current_context = MarketContext.from_indicator_point(self.indicators[-1])
        previous_context = MarketContext.from_indicator_point(self.indicators[-2])
        
        return current_context, previous_context
    
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
    
    def get_point_by_timestamp(self, timestamp: int) -> Optional[IndicatorDataPoint]:
        """
        Get an indicator point by timestamp.
        
        Args:
            timestamp: Timestamp to search for
            
        Returns:
            Indicator data point with matching timestamp or None
        """
        for point in self.indicators:
            if point.timestamp == timestamp:
                return point
        return None
