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


@pytest.fixture
def mock_execution_plan_repo():
    """Create mock execution plan repository"""
    return AsyncMock()


@pytest.fixture
def mock_settings():
    """Create mock settings"""
    return Mock()


class TestEvaluationTargetService:
    """Test EvaluationTargetService functionality"""

    @pytest.mark.asyncio
    async def test_get_targets_with_plans(self, mock_execution_plan_repo, mock_settings):
        """Should return targets from active execution plans."""
        # Arrange
        plan1 = ExecutionPlan(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Plan 1",
            strategy_id=uuid.uuid4(),
            stocks=["AAPL", "MSFT"],
            timeframe="day",
            is_active=True
        )
        
        plan2 = ExecutionPlan(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Plan 2", 
            strategy_id=uuid.uuid4(),
            stocks=["GOOGL", "TSLA"],
            timeframe="day",
            is_active=True
        )
        
        mock_execution_plan_repo.get_active_plans.return_value = [plan1, plan2]
        
        service = EvaluationTargetService(
            execution_plan_repository=mock_execution_plan_repo,
            favorite_repository=Mock(),  # Not used when plans exist
            settings=mock_settings
        )
        
        # Act
        targets = await service.get_targets()
        
        # Assert
        assert len(targets) == 2
        
        # Check first target
        target1 = next(t for t in targets if t.strategy_id == plan1.strategy_id)
        assert target1.stocks == ["AAPL", "MSFT"]
        assert target1.timeframe == "day"
        assert target1.stock_count == 2
        
        # Check second target
        target2 = next(t for t in targets if t.strategy_id == plan2.strategy_id)
        assert target2.stocks == ["GOOGL", "TSLA"]
        assert target2.timeframe == "day"
        assert target2.stock_count == 2
        
        # Verify dependencies were called
        mock_execution_plan_repo.get_active_plans.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_targets_no_plans_returns_empty(self, mock_execution_plan_repo, mock_settings):
        """Should return empty list when no execution plans exist."""
        # Arrange
        mock_execution_plan_repo.get_active_plans.return_value = []
        
        service = EvaluationTargetService(
            execution_plan_repository=mock_execution_plan_repo,
            favorite_repository=Mock(),  # Not used when no plans exist
            settings=mock_settings
        )
        
        # Act
        targets = await service.get_targets()
        
        # Assert
        assert len(targets) == 0
        
        # Verify dependencies were called
        mock_execution_plan_repo.get_active_plans.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_targets_inactive_plans_filtered(self, mock_execution_plan_repo, mock_settings):
        """Should filter out inactive execution plans."""
        # Arrange
        active_plan = ExecutionPlan(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Active Plan",
            strategy_id=uuid.uuid4(),
            stocks=["AAPL"],
            timeframe="day",
            is_active=True
        )
        
        inactive_plan = ExecutionPlan(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Inactive Plan",
            strategy_id=uuid.uuid4(),
            stocks=["MSFT"],
            timeframe="day",
            is_active=False
        )
        
        mock_execution_plan_repo.get_active_plans.return_value = [active_plan, inactive_plan]
        
        service = EvaluationTargetService(
            execution_plan_repository=mock_execution_plan_repo,
            favorite_repository=Mock(),
            settings=mock_settings
        )
        
        # Act
        targets = await service.get_targets()
        
        # Assert
        assert len(targets) == 1
        target = targets[0]
        assert target.strategy_id == active_plan.strategy_id
        assert target.stocks == ["AAPL"]
        
        # Verify dependencies were called
        mock_execution_plan_repo.get_active_plans.assert_called_once()
