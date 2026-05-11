# tests/unit/domain/test_execution_plan_use_cases.py
"""
Tests for ExecutionPlanUseCases duplicate prevention functionality.
"""

import pytest
import uuid
from unittest.mock import AsyncMock, Mock
from app.domain.use_cases.execution_plan_use_cases import ExecutionPlanUseCases
from app.application.dto.execution_plan_dto import CreateExecutionPlanDTO, TimeFrameDTO
from app.domain.entities.execution_plan import ExecutionPlan
from app.domain.entities.strategy import Strategy


@pytest.fixture
def mock_execution_plan_repo():
    """Create mock execution plan repository"""
    return AsyncMock()


@pytest.fixture
def mock_strategy_repo():
    """Create mock strategy repository"""
    return AsyncMock()


@pytest.fixture
def mock_strategy():
    """Create mock strategy"""
    return Strategy(
        id=uuid.uuid4(),
        name="Test Strategy",
        dsl={"version": 1, "conditions": [], "actions": []},
        is_active=True,
        created_at=None,
        updated_at=None
    )


class TestExecutionPlanUseCasesDuplicatePrevention:
    """Test duplicate prevention in execution plan creation"""

    @pytest.mark.asyncio
    async def test_create_plan_duplicate_prevention(self, mock_execution_plan_repo, mock_strategy_repo, mock_strategy):
        """Should prevent creation of identical execution plans"""
        # Arrange
        user_id = uuid.uuid4()
        plan_dto = CreateExecutionPlanDTO(
            strategy_id=mock_strategy.id,
            stocks=["AAPL", "MSFT", "GOOGL"],
            timeframe=TimeFrameDTO.DAY
        )
        
        # Mock existing identical plan
        existing_plan = ExecutionPlan(
            id=uuid.uuid4(),
            user_id=user_id,
            strategy_id=mock_strategy.id,
            stocks=["AAPL", "MSFT", "GOOGL"],
            timeframe="day",
            is_active=True,
            created_at=None,
            updated_at=None
        )
        
        mock_strategy_repo.get_by_id.return_value = mock_strategy
        mock_execution_plan_repo.get_by_user_id.return_value = [existing_plan]
        
        use_cases = ExecutionPlanUseCases(mock_execution_plan_repo, mock_strategy_repo)
        
        # Act & Assert
        with pytest.raises(ValueError, match="An identical execution plan already exists for this user"):
            await use_cases.create_plan(plan_dto, user_id)
        
        # Verify dependencies were called
        mock_strategy_repo.get_by_id.assert_called_once_with(mock_strategy.id)
        mock_execution_plan_repo.get_by_user_id.assert_called_once_with(user_id)
        mock_execution_plan_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_plan_different_stocks_allowed(self, mock_execution_plan_repo, mock_strategy_repo, mock_strategy):
        """Should allow creation with different stocks"""
        # Arrange
        user_id = uuid.uuid4()
        plan_dto = CreateExecutionPlanDTO(
            strategy_id=mock_strategy.id,
            stocks=["TSLA", "NVDA"],  # Different stocks
            timeframe=TimeFrameDTO.DAY
        )
        
        # Mock existing plan with different stocks
        existing_plan = ExecutionPlan(
            id=uuid.uuid4(),
            user_id=user_id,
            strategy_id=mock_strategy.id,
            stocks=["AAPL", "MSFT", "GOOGL"],  # Different stocks
            timeframe="day",
            is_active=True,
            created_at=None,
            updated_at=None
        )
        
        new_plan = ExecutionPlan(
            id=uuid.uuid4(),
            user_id=user_id,
            strategy_id=mock_strategy.id,
            stocks=["TSLA", "NVDA"],
            timeframe="day",
            is_active=True,
            created_at=None,
            updated_at=None
        )
        
        mock_strategy_repo.get_by_id.return_value = mock_strategy
        mock_execution_plan_repo.get_by_user_id.return_value = [existing_plan]
        mock_execution_plan_repo.create.return_value = new_plan
        
        use_cases = ExecutionPlanUseCases(mock_execution_plan_repo, mock_strategy_repo)
        
        # Act
        result = await use_cases.create_plan(plan_dto, user_id)
        
        # Assert
        assert result == new_plan
        mock_execution_plan_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_plan_different_timeframe_allowed(self, mock_execution_plan_repo, mock_strategy_repo, mock_strategy):
        """Should allow creation with different timeframe"""
        # Arrange
        user_id = uuid.uuid4()
        plan_dto = CreateExecutionPlanDTO(
            strategy_id=mock_strategy.id,
            stocks=["AAPL", "MSFT", "GOOGL"],
            timeframe=TimeFrameDTO.HOUR  # Different timeframe
        )
        
        # Mock existing plan with different timeframe
        existing_plan = ExecutionPlan(
            id=uuid.uuid4(),
            user_id=user_id,
            strategy_id=mock_strategy.id,
            stocks=["AAPL", "MSFT", "GOOGL"],
            timeframe="day",  # Different timeframe
            is_active=True,
            created_at=None,
            updated_at=None
        )
        
        new_plan = ExecutionPlan(
            id=uuid.uuid4(),
            user_id=user_id,
            strategy_id=mock_strategy.id,
            stocks=["AAPL", "MSFT", "GOOGL"],
            timeframe="hour",
            is_active=True,
            created_at=None,
            updated_at=None
        )
        
        mock_strategy_repo.get_by_id.return_value = mock_strategy
        mock_execution_plan_repo.get_by_user_id.return_value = [existing_plan]
        mock_execution_plan_repo.create.return_value = new_plan
        
        use_cases = ExecutionPlanUseCases(mock_execution_plan_repo, mock_strategy_repo)
        
        # Act
        result = await use_cases.create_plan(plan_dto, user_id)
        
        # Assert
        assert result == new_plan
        mock_execution_plan_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_plan_different_user_allowed(self, mock_execution_plan_repo, mock_strategy_repo, mock_strategy):
        """Should allow same plan for different users"""
        # Arrange
        user_id_1 = uuid.uuid4()
        user_id_2 = uuid.uuid4()
        plan_dto = CreateExecutionPlanDTO(
            strategy_id=mock_strategy.id,
            stocks=["AAPL", "MSFT", "GOOGL"],
            timeframe=TimeFrameDTO.DAY
        )
        
        # Mock existing plan for different user
        existing_plan = ExecutionPlan(
            id=uuid.uuid4(),
            user_id=user_id_1,  # Different user
            strategy_id=mock_strategy.id,
            stocks=["AAPL", "MSFT", "GOOGL"],
            timeframe="day",
            is_active=True,
            created_at=None,
            updated_at=None
        )
        
        new_plan = ExecutionPlan(
            id=uuid.uuid4(),
            user_id=user_id_2,  # Different user
            strategy_id=mock_strategy.id,
            stocks=["AAPL", "MSFT", "GOOGL"],
            timeframe="day",
            is_active=True,
            created_at=None,
            updated_at=None
        )
        
        mock_strategy_repo.get_by_id.return_value = mock_strategy
        mock_execution_plan_repo.get_by_user_id.return_value = [existing_plan]
        mock_execution_plan_repo.create.return_value = new_plan
        
        use_cases = ExecutionPlanUseCases(mock_execution_plan_repo, mock_strategy_repo)
        
        # Act
        result = await use_cases.create_plan(plan_dto, user_id_2)
        
        # Assert
        assert result == new_plan
        mock_execution_plan_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_plan_inactive_existing_allowed(self, mock_execution_plan_repo, mock_strategy_repo, mock_strategy):
        """Should allow creation when existing plan is inactive"""
        # Arrange
        user_id = uuid.uuid4()
        plan_dto = CreateExecutionPlanDTO(
            strategy_id=mock_strategy.id,
            stocks=["AAPL", "MSFT", "GOOGL"],
            timeframe=TimeFrameDTO.DAY
        )
        
        # Mock existing inactive plan
        existing_plan = ExecutionPlan(
            id=uuid.uuid4(),
            user_id=user_id,
            strategy_id=mock_strategy.id,
            stocks=["AAPL", "MSFT", "GOOGL"],
            timeframe="day",
            is_active=False,  # Inactive plan
            created_at=None,
            updated_at=None
        )
        
        new_plan = ExecutionPlan(
            id=uuid.uuid4(),
            user_id=user_id,
            strategy_id=mock_strategy.id,
            stocks=["AAPL", "MSFT", "GOOGL"],
            timeframe="day",
            is_active=True,
            created_at=None,
            updated_at=None
        )
        
        mock_strategy_repo.get_by_id.return_value = mock_strategy
        mock_execution_plan_repo.get_by_user_id.return_value = [existing_plan]
        mock_execution_plan_repo.create.return_value = new_plan
        
        use_cases = ExecutionPlanUseCases(mock_execution_plan_repo, mock_strategy_repo)
        
        # Act
        result = await use_cases.create_plan(plan_dto, user_id)
        
        # Assert
        assert result == new_plan
        mock_execution_plan_repo.create.assert_called_once()
