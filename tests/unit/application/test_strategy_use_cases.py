"""
Unit tests for Strategy Use Cases
Tests for business logic with mocked repository
"""
import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.domain.entities.strategy import Strategy
from app.domain.entities.strategy_dsl import (
    StrategyDSL,
    Condition,
    Price,
    Constant,
    Indicator
)
from app.domain.use_cases.strategy_use_cases import StrategyUseCases
from app.application.dto.strategy_dto import (
    StrategyCreateRequest,
    StrategyUpdateRequest
)


@pytest.fixture
def mock_repository():
    """Create mock strategy repository"""
    return AsyncMock()


@pytest.fixture
def strategy_use_cases(mock_repository):
    """Create strategy use cases with mock repository"""
    return StrategyUseCases(repository=mock_repository)


@pytest.fixture
def sample_user_id():
    """Sample user ID"""
    return uuid.uuid4()


@pytest.fixture
def sample_strategy_id():
    """Sample strategy ID"""
    return uuid.uuid4()


@pytest.fixture
def valid_dsl_json():
    """Valid DSL JSON for testing"""
    return {
        "version": 1,
        "root": {
            "type": "condition",
            "operator": ">",
            "left": {"type": "price", "field": "close"},
            "right": {"type": "constant", "value": 100.0}
        }
    }


class TestCreateStrategy:
    """Test strategy creation use case"""
    
    async def test_create_strategy_with_valid_dsl(
        self, strategy_use_cases, mock_repository, sample_user_id, valid_dsl_json
    ):
        """Should create strategy with valid DSL"""
        request = StrategyCreateRequest(
            name="Test Strategy",
            description="A test strategy",
            dsl_definition=valid_dsl_json
        )
        
        # Mock repository to return the created strategy
        mock_repository.create.return_value = Strategy(
            user_id=sample_user_id,
            name=request.name,
            description=request.description,
            dsl_definition=request.dsl_definition,
            version=1
        )
        
        result = await strategy_use_cases.create_strategy(sample_user_id, request)
        
        assert result.name == "Test Strategy"
        assert result.description == "A test strategy"
        assert result.is_active is True
        mock_repository.create.assert_called_once()
    
    async def test_create_strategy_with_invalid_dsl(
        self, strategy_use_cases, mock_repository, sample_user_id
    ):
        """Should reject strategy with invalid DSL"""
        invalid_dsl = {
            "version": 1,
            "root": {
                "type": "condition",
                "operator": "invalid_operator",
                "left": {"type": "constant", "value": 1.0},
                "right": {"type": "constant", "value": 2.0}
            }
        }
        
        request = StrategyCreateRequest(
            name="Test Strategy",
            dsl_definition=invalid_dsl
        )
        
        with pytest.raises(ValueError, match="DSL validation failed"):
            await strategy_use_cases.create_strategy(sample_user_id, request)
        
        mock_repository.create.assert_not_called()
    
    async def test_create_strategy_without_description(
        self, strategy_use_cases, mock_repository, sample_user_id, valid_dsl_json
    ):
        """Should create strategy without optional description"""
        request = StrategyCreateRequest(
            name="Test Strategy",
            dsl_definition=valid_dsl_json
        )
        
        mock_repository.create.return_value = Strategy(
            user_id=sample_user_id,
            name=request.name,
            dsl_definition=request.dsl_definition,
            version=1
        )
        
        result = await strategy_use_cases.create_strategy(sample_user_id, request)
        
        assert result.name == "Test Strategy"
        assert result.description is None


class TestUpdateStrategy:
    """Test strategy update use case"""
    
    async def test_update_strategy_success(
        self, strategy_use_cases, mock_repository, 
        sample_user_id, sample_strategy_id, valid_dsl_json
    ):
        """Should update strategy with valid DSL"""
        # Mock existing strategy
        existing_strategy = Strategy(
            id=sample_strategy_id,
            user_id=sample_user_id,
            name="Old Name",
            dsl_definition=valid_dsl_json,
            version=1
        )
        mock_repository.get_by_id.return_value = existing_strategy
        mock_repository.update.return_value = existing_strategy
        
        new_dsl = {
            "version": 1,
            "root": {
                "type": "condition",
                "operator": "<",
                "left": {"type": "price", "field": "close"},
                "right": {"type": "constant", "value": 50.0}
            }
        }
        
        request = StrategyUpdateRequest(
            name="New Name",
            dsl_definition=new_dsl
        )
        
        result = await strategy_use_cases.update_strategy(
            sample_user_id, sample_strategy_id, request
        )
        
        mock_repository.update.assert_called_once()
    
    async def test_update_strategy_not_found(
        self, strategy_use_cases, mock_repository, sample_user_id, sample_strategy_id
    ):
        """Should raise error when strategy not found"""
        mock_repository.get_by_id.return_value = None
        
        request = StrategyUpdateRequest(name="New Name")
        
        with pytest.raises(ValueError, match="Strategy not found"):
            await strategy_use_cases.update_strategy(
                sample_user_id, sample_strategy_id, request
            )
    
    async def test_update_strategy_wrong_owner(
        self, strategy_use_cases, mock_repository, 
        sample_user_id, sample_strategy_id, valid_dsl_json
    ):
        """Should raise permission error for wrong owner"""
        wrong_user_id = uuid.uuid4()
        existing_strategy = Strategy(
            id=sample_strategy_id,
            user_id=wrong_user_id,  # Different user
            name="Test",
            dsl_definition=valid_dsl_json,
            version=1
        )
        mock_repository.get_by_id.return_value = existing_strategy
        
        request = StrategyUpdateRequest(name="New Name")
        
        with pytest.raises(PermissionError, match="Cannot update strategy owned by another user"):
            await strategy_use_cases.update_strategy(
                sample_user_id, sample_strategy_id, request
            )
    
    async def test_update_strategy_with_invalid_dsl(
        self, strategy_use_cases, mock_repository, 
        sample_user_id, sample_strategy_id, valid_dsl_json
    ):
        """Should reject update with invalid DSL"""
        existing_strategy = Strategy(
            id=sample_strategy_id,
            user_id=sample_user_id,
            name="Test",
            dsl_definition=valid_dsl_json,
            version=1
        )
        mock_repository.get_by_id.return_value = existing_strategy
        
        invalid_dsl = {
            "version": 1,
            "root": {
                "type": "condition",
                "operator": "invalid_op",
                "left": {"type": "constant", "value": 1.0},
                "right": {"type": "constant", "value": 2.0}
            }
        }
        
        request = StrategyUpdateRequest(dsl_definition=invalid_dsl)
        
        with pytest.raises(ValueError, match="DSL validation failed"):
            await strategy_use_cases.update_strategy(
                sample_user_id, sample_strategy_id, request
            )


class TestDeleteStrategy:
    """Test strategy deletion use case"""
    
    async def test_delete_strategy_success(
        self, strategy_use_cases, mock_repository, 
        sample_user_id, sample_strategy_id, valid_dsl_json
    ):
        """Should delete strategy with correct ownership"""
        existing_strategy = Strategy(
            id=sample_strategy_id,
            user_id=sample_user_id,
            name="Test",
            dsl_definition=valid_dsl_json,
            version=1
        )
        mock_repository.get_by_id.return_value = existing_strategy
        mock_repository.delete.return_value = True
        
        result = await strategy_use_cases.delete_strategy(
            sample_user_id, sample_strategy_id
        )
        
        assert result is True
        mock_repository.delete.assert_called_once_with(sample_strategy_id)
    
    async def test_delete_strategy_not_found(
        self, strategy_use_cases, mock_repository, sample_user_id, sample_strategy_id
    ):
        """Should raise error when strategy not found"""
        mock_repository.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Strategy not found"):
            await strategy_use_cases.delete_strategy(
                sample_user_id, sample_strategy_id
            )
    
    async def test_delete_strategy_wrong_owner(
        self, strategy_use_cases, mock_repository, 
        sample_user_id, sample_strategy_id, valid_dsl_json
    ):
        """Should raise permission error for wrong owner"""
        wrong_user_id = uuid.uuid4()
        existing_strategy = Strategy(
            id=sample_strategy_id,
            user_id=wrong_user_id,
            name="Test",
            dsl_definition=valid_dsl_json,
            version=1
        )
        mock_repository.get_by_id.return_value = existing_strategy
        
        with pytest.raises(PermissionError, match="Cannot delete strategy"):
            await strategy_use_cases.delete_strategy(
                sample_user_id, sample_strategy_id
            )


class TestGetStrategy:
    """Test strategy retrieval use case"""
    
    async def test_get_strategy_success(
        self, strategy_use_cases, mock_repository, 
        sample_user_id, sample_strategy_id, valid_dsl_json
    ):
        """Should return strategy by ID (Phase 2: no ownership check)"""
        existing_strategy = Strategy(
            id=sample_strategy_id,
            user_id=sample_user_id,
            name="Test",
            dsl_definition=valid_dsl_json,
            version=1
        )
        mock_repository.get_by_id.return_value = existing_strategy
        
        result = await strategy_use_cases.get_strategy(sample_strategy_id)
        
        assert result.name == "Test"
        assert result.id == sample_strategy_id
    
    async def test_get_strategy_not_found(
        self, strategy_use_cases, mock_repository, sample_strategy_id
    ):
        """Should raise error when strategy not found"""
        mock_repository.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Strategy not found"):
            await strategy_use_cases.get_strategy(sample_strategy_id)
    
    async def test_get_strategy_by_id_only(
        self, strategy_use_cases, mock_repository, 
        sample_strategy_id, valid_dsl_json
    ):
        """Should get strategy by ID without user ownership check (Phase 2 change)"""
        # Strategy owned by different user, but should still be accessible
        wrong_user_id = uuid.uuid4()
        existing_strategy = Strategy(
            id=sample_strategy_id,
            user_id=wrong_user_id,
            name="Test",
            dsl_definition=valid_dsl_json,
            version=1
        )
        mock_repository.get_by_id.return_value = existing_strategy
        
        # Phase 2: No user_id parameter, no ownership check
        result = await strategy_use_cases.get_strategy(sample_strategy_id)
        
        assert result.name == "Test"
        assert result.id == sample_strategy_id


class TestListStrategies:
    """Test strategy listing use case"""
    
    async def test_list_strategies(
        self, strategy_use_cases, mock_repository, 
        sample_user_id, valid_dsl_json
    ):
        """Should return list of user strategies"""
        strategies = [
            Strategy(
                id=uuid.uuid4(),
                user_id=sample_user_id,
                name=f"Strategy {i}",
                dsl_definition=valid_dsl_json,
                version=1,
                is_active=i % 2 == 0
            )
            for i in range(3)
        ]
        mock_repository.get_by_user.return_value = strategies
        
        result = await strategy_use_cases.list_strategies(sample_user_id)
        
        assert len(result.items) == 3
        assert result.total == 3
    
    async def test_list_strategies_active_only(
        self, strategy_use_cases, mock_repository, 
        sample_user_id, valid_dsl_json
    ):
        """Should filter to active strategies only"""
        strategies = [
            Strategy(
                id=uuid.uuid4(),
                user_id=sample_user_id,
                name="Active Strategy",
                dsl_definition=valid_dsl_json,
                version=1,
                is_active=True
            ),
            Strategy(
                id=uuid.uuid4(),
                user_id=sample_user_id,
                name="Inactive Strategy",
                dsl_definition=valid_dsl_json,
                version=1,
                is_active=False
            )
        ]
        mock_repository.get_by_user.return_value = strategies
        
        result = await strategy_use_cases.list_strategies(
            sample_user_id, active_only=True
        )
        
        assert len(result.items) == 1
        assert result.items[0].name == "Active Strategy"
    
    async def test_list_strategies_empty(
        self, strategy_use_cases, mock_repository, sample_user_id
    ):
        """Should return empty list when no strategies"""
        mock_repository.get_by_user.return_value = []
        
        result = await strategy_use_cases.list_strategies(sample_user_id)
        
        assert len(result.items) == 0
        assert result.total == 0


class TestActivateDeactivateStrategy:
    """Test strategy activation/deactivation use cases"""
    
    async def test_activate_strategy(
        self, strategy_use_cases, mock_repository, 
        sample_user_id, sample_strategy_id, valid_dsl_json
    ):
        """Should activate strategy"""
        existing_strategy = Strategy(
            id=sample_strategy_id,
            user_id=sample_user_id,
            name="Test",
            dsl_definition=valid_dsl_json,
            version=1,
            is_active=False
        )
        mock_repository.get_by_id.return_value = existing_strategy
        mock_repository.update.return_value = existing_strategy
        
        result = await strategy_use_cases.activate_strategy(
            sample_user_id, sample_strategy_id
        )
        
        assert result.is_active is True
        mock_repository.update.assert_called_once()
    
    async def test_deactivate_strategy(
        self, strategy_use_cases, mock_repository, 
        sample_user_id, sample_strategy_id, valid_dsl_json
    ):
        """Should deactivate strategy"""
        existing_strategy = Strategy(
            id=sample_strategy_id,
            user_id=sample_user_id,
            name="Test",
            dsl_definition=valid_dsl_json,
            version=1,
            is_active=True
        )
        mock_repository.get_by_id.return_value = existing_strategy
        mock_repository.update.return_value = existing_strategy
        
        result = await strategy_use_cases.deactivate_strategy(
            sample_user_id, sample_strategy_id
        )
        
        assert result.is_active is False
        mock_repository.update.assert_called_once()


class TestValidateDSL:
    """Test DSL validation use case"""
    
    async def test_validate_dsl_valid(
        self, strategy_use_cases, valid_dsl_json
    ):
        """Should return success for valid DSL"""
        result = await strategy_use_cases.validate_dsl(valid_dsl_json)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    async def test_validate_dsl_invalid(
        self, strategy_use_cases
    ):
        """Should return failure for invalid DSL"""
        invalid_dsl = {
            "version": 1,
            "root": {
                "type": "condition",
                "operator": "invalid_op",
                "left": {"type": "constant", "value": 1.0},
                "right": {"type": "constant", "value": 2.0}
            }
        }
        
        result = await strategy_use_cases.validate_dsl(invalid_dsl)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    async def test_validate_dsl_missing_version(
        self, strategy_use_cases, valid_dsl_json
    ):
        """Should fail validation for missing version"""
        dsl_without_version = valid_dsl_json.copy()
        del dsl_without_version["version"]
        
        result = await strategy_use_cases.validate_dsl(dsl_without_version)
        
        assert result.is_valid is False
