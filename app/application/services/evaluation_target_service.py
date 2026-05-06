# app/application/services/evaluation_target_service.py
"""
EvaluationTargetService - Pure service for determining what to evaluate.

Responsible ONLY for deciding what should be evaluated.
No side effects: no market data fetching, no execution, no locking.
Phase 2: Returns targets from execution plans with fallback to favorites.
"""

from typing import List
from app.domain.entities.evaluation_target import EvaluationTarget
from app.application.repositories.favorite_repository import FavoriteRepository
from app.application.repositories.execution_plan_repository import ExecutionPlanRepository
from app.core.config import AppBaseSettings
from app.core.logging_config import get_logger


class EvaluationTargetService:
    """
    Pure service responsible ONLY for determining what should be evaluated.
    
    This service has NO side effects:
    - Does NOT fetch market data
    - Does NOT execute strategies  
    - Does NOT save signals
    - Does NOT acquire locks
    
    Phase 2 Implementation:
    - Returns targets from active execution plans
    - Falls back to favorites + default strategy for backward compatibility
    - No per-user logic yet (system-wide execution)
    """
    
    def __init__(
        self,
        execution_plan_repository: ExecutionPlanRepository,
        favorite_repository: FavoriteRepository,
        settings: AppBaseSettings
    ):
        self._execution_plan_repo = execution_plan_repository
        self._favorite_repo = favorite_repository
        self._settings = settings
        self._logger = get_logger(__name__)
    
    async def get_targets(self) -> List[EvaluationTarget]:
        """
        Generate evaluation targets for current execution cycle.
        
        Phase 2: Returns targets from active execution plans.
        Fallback: If no plans exist, use favorites logic for backward compatibility.
        
        Logic:
        1. Try to get active execution plans from database
        2. If plans exist, create one target per plan
        3. If no plans, fallback to favorites + default strategy
        
        Returns:
            List[EvaluationTarget] - One per active plan, or fallback target
            
        Raises:
            No exceptions swallowed - let caller handle DB errors
        """
        # Try execution plans first
        plans = await self._execution_plan_repo.get_active_plans()
        
        if plans:
            self._logger.info(
                "Using execution plans",
                component="evaluation_target_service",
                plan_count=len(plans)
            )
            return [
                EvaluationTarget(
                    strategy_id=plan.strategy_id,
                    stocks=plan.stocks,
                    timeframe=plan.timeframe
                )
                for plan in plans
            ]
        
        # Fallback to favorites for backward compatibility
        self._logger.info(
            "No execution plans found, falling back to favorites",
            component="evaluation_target_service"
        )
        return await self._fallback_to_favorites()

    async def _fallback_to_favorites(self) -> List[EvaluationTarget]:
        """Fallback method using existing favorites logic"""
        stocks = await self._get_stock_universe()
        
        if not stocks:
            return []
        
        # Use default strategy for fallback
        from app.infrastructure.database.default_strategy_seed import get_default_strategy_entity
        default_strategy = get_default_strategy_entity()
        
        return [EvaluationTarget(
            strategy_id=default_strategy.id,
            stocks=stocks,
            timeframe="day"
        )]
    
    async def _get_stock_universe(self) -> List[str]:
        """
        Determine which stocks to evaluate.
        
        Priority:
        1. User's favorite stocks from DB
        2. DEFAULT_SIGNAL_STOCKS from environment
        """
        # Try favorites first
        favorites = await self._favorite_repo.get_all_favorites()
    
        if favorites and favorites.symbols:
            return [s.strip().upper() for s in favorites.symbols]
            
        # Fallback to environment defaults
        default_stocks = getattr(
            self._settings, 
            'DEFAULT_SIGNAL_STOCKS', 
            'AAPL,GOOGL,MSFT,TSLA,NVDA'
        )
        
        if isinstance(default_stocks, str):
            return [s.strip().upper() for s in default_stocks.split(',')]
            
        if default_stocks is None:
            return []
        
        return [s.strip().upper() for s in default_stocks]
