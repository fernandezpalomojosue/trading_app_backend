# app/application/services/evaluation_target_service.py
"""
EvaluationTargetService - Pure service for determining what to evaluate.

Responsible ONLY for deciding what should be evaluated.
No side effects: no market data fetching, no execution, no locking.
Phase 1: Returns single target with all stocks from favorites or defaults.
"""

from typing import List
from app.domain.entities.evaluation_target import EvaluationTarget
from app.application.repositories.favorite_repository import FavoriteRepository
from app.core.config import AppBaseSettings


class EvaluationTargetService:
    """
    Pure service responsible ONLY for determining what should be evaluated.
    
    This service has NO side effects:
    - Does NOT fetch market data
    - Does NOT execute strategies  
    - Does NOT save signals
    - Does NOT acquire locks
    
    Phase 1 Implementation:
    - Returns SINGLE target with all stocks
    - Uses favorites + fallback to env defaults
    - No per-user logic yet
    """
    
    def __init__(
        self,
        favorite_repository: FavoriteRepository,
        settings: AppBaseSettings
    ):
        self._favorite_repo = favorite_repository
        self._settings = settings
    
    async def get_targets(self) -> List[EvaluationTarget]:
        """
        Generate evaluation targets for current execution cycle.
        
        Phase 1: Returns exactly ONE target containing all stocks.
        Future: Will return multiple targets per user, per strategy, etc.
        
        Logic:
        1. Try to get favorites from database
        2. If no favorites, use DEFAULT_SIGNAL_STOCKS from env
        3. Return single EvaluationTarget
        
        Returns:
            List[EvaluationTarget] - Always length 1 in Phase 1
            
        Raises:
            No exceptions swallowed - let caller handle DB errors
        """
        # Get favorites or fallback
        stocks = await self._get_stock_universe()
        
        if not stocks:
            # Return empty list - caller decides what to do
            return []
        
        # Phase 1: Single target with all stocks
        return [EvaluationTarget(stocks=stocks)]
    
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
            return favorites.symbols
        
        # Fallback to environment defaults
        default_stocks = getattr(
            self._settings, 
            'DEFAULT_SIGNAL_STOCKS', 
            'AAPL,GOOGL,MSFT,TSLA,NVDA'
        )
        
        if isinstance(default_stocks, str):
            return [s.strip().upper() for s in default_stocks.split(',')]
        
        return [s.upper() for s in default_stocks]
