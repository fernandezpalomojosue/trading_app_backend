# app/application/services/indicators_service.py
from abc import ABC, abstractmethod
from typing import Optional

from app.application.dto.indicators_dto import (
    CombinedIndicatorsResponse
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
    ) -> CombinedIndicatorsResponse:
        """Get all technical indicators for a symbol"""
        pass
