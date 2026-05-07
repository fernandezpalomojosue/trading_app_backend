# app/application/services/snapshot_precomputation_service.py
"""
Snapshot Precomputation Service

Phase 4 optimization service responsible for:
- Grouping execution plans by (symbol, timeframe)
- Fetching market data once per unique combination
- Computing indicators once per unique combination
- Creating MarketSnapshots for reuse across all evaluations
"""

import asyncio
from typing import List, Dict, Tuple, Optional
from uuid import UUID
import logging

from app.domain.entities.execution_plan import ExecutionPlan
from app.domain.entities.market_snapshot import MarketSnapshot
from app.domain.entities.strategy import Strategy
from app.application.services.market_service import MarketService
from app.application.services.indicators_service import IndicatorsService
from app.infrastructure.external.market_client import PolygonMarketClient
from app.domain.use_cases.indicators_use_cases import IndicatorsUseCases
from app.infrastructure.cache.redis_cache import RedisCache


logger = logging.getLogger(__name__)


class SnapshotPrecomputationService:
    """
    Service for precomputing market snapshots from execution plans.
    
    This service implements Phase 4 optimization by computing market data
    and indicators once per (symbol, timeframe) combination, then creating
    reusable MarketSnapshot objects for all strategy evaluations.
    """
    
    def __init__(
        self,
        market_service: MarketService,
        indicator_service: IndicatorsService,
        max_concurrency: int = 5
    ):
        """
        Initialize snapshot precomputation service.
        
        Args:
            market_service: Service for fetching market data
            indicator_service: Service for computing technical indicators
            max_concurrency: Maximum concurrent snapshot computations
        """
        self.market_service = market_service
        self.indicator_service = indicator_service
        self.semaphore = asyncio.Semaphore(max_concurrency)
        
    async def build_snapshots(
        self,
        plans: List[ExecutionPlan]
    ) -> Dict[Tuple[str, str], MarketSnapshot]:
        """
        Build market snapshots from execution plans.
        
        Args:
            plans: List of active execution plans
            
        Returns:
            Dictionary mapping (symbol, timeframe) -> MarketSnapshot
        """
        # Step 1: Collect unique (symbol, timeframe) keys
        unique_keys = self._collect_unique_keys(plans)
        
        logger.info(
            "snapshot_precompute_started",
            extra={
                "total_plans": len(plans),
                "unique_pairs": len(unique_keys),
                "max_concurrency": self.semaphore._value
            }
        )
        
        # Step 2: Precompute snapshots with bounded concurrency
        snapshots = {}
        tasks = []
        
        for symbol, timeframe in unique_keys:
            task = self._build_single_snapshot(symbol, timeframe)
            tasks.append(task)
        
        # Wait for all snapshots with error isolation
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and log errors
        successful_count = 0
        for i, result in enumerate(results):
            symbol, timeframe = list(unique_keys)[i]
            
            if isinstance(result, Exception):
                logger.error(
                    "snapshot_build_failed",
                    extra={
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "error": str(result)
                    }
                )
                continue
            
            if result and isinstance(result, MarketSnapshot) and result.has_valid_data():
                snapshots[(symbol, timeframe)] = result
                successful_count += 1
                
                logger.info(
                    "snapshot_built",
                    extra={
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "current_timestamp": result.current_point.timestamp,
                        "previous_timestamp": result.previous_point.timestamp
                    }
                )
            else:
                logger.warning(
                    "snapshot_invalid",
                    extra={
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "reason": "insufficient_data"
                    }
                )
        
        logger.info(
            "snapshot_precompute_completed",
            extra={
                "requested": len(unique_keys),
                "successful": successful_count,
                "failed": len(unique_keys) - successful_count
            }
        )
        
        return snapshots
    
    def _collect_unique_keys(
        self, 
        plans: List[ExecutionPlan]
    ) -> List[Tuple[str, str]]:
        """
        Collect unique (symbol, timeframe) combinations from execution plans.
        
        Args:
            plans: List of execution plans
            
        Returns:
            List of unique (symbol, timeframe) tuples
        """
        unique_keys = set()
        
        for plan in plans:
            for stock in plan.stocks:
                unique_keys.add((stock, plan.timeframe))
        
        return list(unique_keys)
    
    async def _build_single_snapshot(
        self,
        symbol: str,
        timeframe: str
    ) -> Optional[MarketSnapshot]:
        """
        Build a single market snapshot for (symbol, timeframe).
        
        Args:
            symbol: Stock symbol
            timeframe: Timeframe (day, hour, minute, etc.)
            
        Returns:
            MarketSnapshot or None if insufficient data
        """
        async with self.semaphore:
            try:
                # Fetch market data
                data = await self._fetch_market_data(symbol, timeframe)
                
                if not data or len(data) < 2:
                    logger.warning(
                        "insufficient_market_data",
                        extra={
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "data_points": len(data) if data else 0
                        }
                    )
                    return None
                
                # Compute indicators
                indicators = await self._compute_indicators(symbol, timeframe, data)
                
                if not indicators or len(indicators) < 2:
                    logger.warning(
                        "insufficient_indicators",
                        extra={
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "indicator_points": len(indicators) if indicators else 0
                        }
                    )
                    return None
                
                # Create snapshot with full indicators list
                snapshot = MarketSnapshot(
                    symbol=symbol,
                    timeframe=timeframe,
                    indicators=indicators
                )
                
                return snapshot
                
            except Exception as e:
                logger.error(
                    "snapshot_build_error",
                    extra={
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                raise
    
    async def _fetch_market_data(
        self,
        symbol: str,
        timeframe: str
    ) -> List[Dict]:
        """
        Fetch market data for symbol and timeframe.
        
        Args:
            symbol: Stock symbol
            timeframe: Timeframe string
            
        Returns:
            List of OHLCV data points
        """
        # Convert timeframe to Polygon API parameters
        multiplier, timespan = self._convert_timeframe(timeframe)
        
        # Fetch sufficient data for indicator calculations
        limit = 100  # Default limit for indicator calculations
        
        data = await self.market_service.fetch_candlestick_data(
            symbol=symbol,
            timespan=timespan,
            multiplier=multiplier,
            limit=limit
        )
        
        return data
    
    async def _compute_indicators(
        self,
        symbol: str,
        timeframe: str,
        data: List[Dict]
    ) -> List:
        """
        Compute technical indicators for market data.
        
        Args:
            symbol: Stock symbol
            timeframe: Timeframe string
            data: OHLCV market data
            
        Returns:
            List of IndicatorDataPoint objects
        """
        # Standard indicator parameters (can be made configurable)
        window = 14
        fast = 12
        slow = 26
        signal = 9
        
        indicators = await self.indicator_service.get_indicators(
            symbol=symbol,
            data=data,
            window=window,
            fast=fast,
            slow=slow,
            signal=signal,
            timespan=timeframe,
            limit=100
        )
        
        return indicators
    
    def _convert_timeframe(self, timeframe: str) -> Tuple[int, str]:
        """
        Convert timeframe string to Polygon API parameters.
        
        Args:
            timeframe: Timeframe string (day, hour, minute, 4hour)
            
        Returns:
            Tuple of (multiplier, timespan) for Polygon API
        """
        timeframe_map = {
            "minute": (1, "minute"),
            "hour": (1, "hour"),
            "4hour": (4, "hour"),
            "day": (1, "day")
        }
        
        return timeframe_map.get(timeframe, (1, "day"))
