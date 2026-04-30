"""
SignalEngineService Interface: Abstract interface for signal generation.

Signal construction layer - receives evaluation results from StrategyEngine
and builds SignalDataPoint objects with proper SL/TP and metadata.
"""
from typing import List, Literal, Optional
from abc import ABC, abstractmethod
from uuid import UUID
from app.application.dto.indicators_dto import IndicatorDataPoint
from app.application.dto.signals_dto import SignalDataPoint


class SignalEngineService(ABC):
    """Abstract interface for signal engine service"""
    
    @abstractmethod
    async def calculate_signals(
        self, 
        symbol: str, 
        data_points: List[IndicatorDataPoint]
    ) -> List[SignalDataPoint]:
        """Calculate signals for a list of indicator data points"""
        pass
    
    @abstractmethod
    async def calculate_single_signal(
        self, 
        symbol: str, 
        point: IndicatorDataPoint, 
        prev_point: Optional[IndicatorDataPoint],
        strategy_id: UUID,
        condition_met: bool,
        action: Literal["buy", "sell", "hold"]
    ) -> SignalDataPoint:
        """
        Calculate signal for single point.
        
        Args:
            symbol: Stock symbol
            point: Current indicator data point
            prev_point: Previous indicator data point (for crossover context)
            strategy_id: ID of the strategy that generated this signal
            condition_met: Whether strategy conditions were met
            action: Action from strategy DSL (buy/sell/hold)
            
        Returns:
            SignalDataPoint with signal details
        """
        pass