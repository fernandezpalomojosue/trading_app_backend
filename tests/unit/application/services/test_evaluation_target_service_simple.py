# tests/unit/application/services/test_evaluation_target_service_simple.py
"""
Simple unit tests for EvaluationTargetService with Phase 2 execution plans support.
"""

import pytest
import uuid
from unittest.mock import AsyncMock, Mock
from app.application.services.evaluation_target_service import EvaluationTargetService
from app.domain.entities.evaluation_target import EvaluationTarget
from app.domain.entities.execution_plan import ExecutionPlan


class TestEvaluationTargetServiceSimple:
    """Test EvaluationTargetService behavior with minimal dependencies."""
    
    @pytest.mark.asyncio
    async def test_get_targets_with_execution_plans(self):
        """Should return targets from active execution plans."""
        # Arrange
        strategy_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        mock_plans = [
            ExecutionPlan(
                id=uuid.uuid4(),
                user_id=user_id,
                strategy_id=strategy_id,
                stocks=["AAPL", "MSFT", "GOOGL"],
                timeframe="day",
                is_active=True
            )
        ]
        
        mock_execution_plan_repo = AsyncMock()
        mock_execution_plan_repo.get_active_plans.return_value = mock_plans
        
        mock_favorite_repo = AsyncMock()
        mock_settings = Mock()
        
        service = EvaluationTargetService(
            execution_plan_repository=mock_execution_plan_repo,
            favorite_repository=mock_favorite_repo,
            settings=mock_settings
        )
        
        # Act
        targets = await service.get_targets()
        
        # Assert
        assert len(targets) == 1
        target = targets[0]
        assert isinstance(target, EvaluationTarget)
        assert target.strategy_id == strategy_id
        assert target.stocks == ["AAPL", "MSFT", "GOOGL"]
        assert target.timeframe == "day"
        assert target.stock_count == 3
        
        # Verify dependencies were called
        mock_execution_plan_repo.get_active_plans.assert_called_once()
        mock_favorite_repo.get_all_favorites.assert_not_called()  # Should not be called when plans exist
    
    @pytest.mark.asyncio
    async def test_get_targets_no_plans_fallback_to_favorites(self):
        """Should fallback to favorites when no execution plans exist."""
        # Arrange
        mock_execution_plan_repo = AsyncMock()
        mock_execution_plan_repo.get_active_plans.return_value = []
        
        mock_favorites = Mock()
        mock_favorites.symbols = ["AAPL", "MSFT", "GOOGL"]
        
        mock_favorite_repo = AsyncMock()
        mock_favorite_repo.get_all_favorites.return_value = mock_favorites
        
        mock_settings = Mock()
        
        service = EvaluationTargetService(
            execution_plan_repository=mock_execution_plan_repo,
            favorite_repository=mock_favorite_repo,
            settings=mock_settings
        )
        
        # Act
        targets = await service.get_targets()
        
        # Assert
        assert len(targets) == 1
        target = targets[0]
        assert isinstance(target, EvaluationTarget)
        assert target.stocks == ["AAPL", "MSFT", "GOOGL"]
        assert target.timeframe == "day"
        assert target.stock_count == 3
        assert target.strategy_id is not None  # Should have default strategy ID
        
        # Verify dependencies were called
        mock_execution_plan_repo.get_active_plans.assert_called_once()
        mock_favorite_repo.get_all_favorites.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_targets_no_plans_with_defaults(self):
        """Should fallback to defaults when no plans or favorites exist."""
        # Arrange
        mock_execution_plan_repo = AsyncMock()
        mock_execution_plan_repo.get_active_plans.return_value = []
        
        mock_favorites = Mock()
        mock_favorites.symbols = []  # Empty favorites
        
        mock_favorite_repo = AsyncMock()
        mock_favorite_repo.get_all_favorites.return_value = mock_favorites
        
        mock_settings = Mock()
        mock_settings.DEFAULT_SIGNAL_STOCKS = "AAPL,TSLA,NVDA"
        
        service = EvaluationTargetService(
            execution_plan_repository=mock_execution_plan_repo,
            favorite_repository=mock_favorite_repo,
            settings=mock_settings
        )
        
        # Act
        targets = await service.get_targets()
        
        # Assert
        assert len(targets) == 1
        target = targets[0]
        assert target.stocks == ["AAPL", "TSLA", "NVDA"]
        assert target.timeframe == "day"
        assert target.stock_count == 3
        assert target.strategy_id is not None  # Should have default strategy ID
    
    @pytest.mark.asyncio
    async def test_get_targets_no_plans_no_favorites_no_defaults(self):
        """Should return empty list when no plans, favorites, or defaults exist."""
        # Arrange
        mock_execution_plan_repo = AsyncMock()
        mock_execution_plan_repo.get_active_plans.return_value = []
        
        mock_favorites = Mock()
        mock_favorites.symbols = None  # No favorites
        
        mock_favorite_repo = AsyncMock()
        mock_favorite_repo.get_all_favorites.return_value = mock_favorites
        
        mock_settings = Mock()
        mock_settings.DEFAULT_SIGNAL_STOCKS = None
        
        service = EvaluationTargetService(
            execution_plan_repository=mock_execution_plan_repo,
            favorite_repository=mock_favorite_repo,
            settings=mock_settings
        )
        
        # Act
        targets = await service.get_targets()
        
        # Assert
        assert len(targets) == 0
    
    @pytest.mark.asyncio
    async def test_get_targets_normalizes_symbols_in_fallback(self):
        """Should normalize stock symbols to uppercase in fallback mode."""
        # Arrange
        mock_execution_plan_repo = AsyncMock()
        mock_execution_plan_repo.get_active_plans.return_value = []
        
        mock_favorites = Mock()
        mock_favorites.symbols = ["aapl", "msft", "googl"]  # lowercase
        
        mock_favorite_repo = AsyncMock()
        mock_favorite_repo.get_all_favorites.return_value = mock_favorites
        
        mock_settings = Mock()
        
        service = EvaluationTargetService(
            execution_plan_repository=mock_execution_plan_repo,
            favorite_repository=mock_favorite_repo,
            settings=mock_settings
        )
        
        # Act
        targets = await service.get_targets()
        
        # Assert
        assert len(targets) == 1
        target = targets[0]
        assert target.stocks == ["AAPL", "MSFT", "GOOGL"]  # Uppercase
