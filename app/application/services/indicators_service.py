# app/application/services/indicators_service.py
from abc import ABC, abstractmethod
from typing import List, Optional

from app.application.dto.indicators_dto import (
    IndicatorDataPoint
)


class IndicatorsService(ABC):
    """Application interface for technical indicators operations"""
    
    @abstractmethod
    async def get_indicators(
        self,
        symbol: str,
        window: int,
        fast: int,
        slow: int,
        signal: int,
        timespan: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[IndicatorDataPoint]:
        """Get all technical indicators for a symbol"""
        pass
