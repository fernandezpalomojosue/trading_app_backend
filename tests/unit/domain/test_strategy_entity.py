"""
Unit tests for Strategy Entity
Tests for business logic and state management
"""
import uuid
import pytest
from datetime import datetime, timezone
from app.domain.entities.strategy import Strategy


class TestStrategyCreation:
    """Test strategy entity creation"""
    
    def test_create_strategy_with_defaults(self):
        """Should create strategy with default values"""
        user_id = uuid.uuid4()
        strategy = Strategy(
            user_id=user_id,
            name="Test Strategy",
            description="A test strategy"
        )
        
        assert strategy.id is not None
        assert isinstance(strategy.id, uuid.UUID)
        assert strategy.user_id == user_id
        assert strategy.name == "Test Strategy"
        assert strategy.description == "A test strategy"
        assert strategy.is_active is True
        assert strategy.dsl_definition == {}
        assert strategy.dsl_hash is None
        assert strategy.version == 1
    
    def test_create_strategy_with_dsl(self):
        """Should create strategy with DSL definition"""
        user_id = uuid.uuid4()
        dsl = {
            "version": 1,
            "root": {
                "type": "condition",
                "operator": ">",
                "left": {"type": "price", "field": "close"},
                "right": {"type": "constant", "value": 100.0}
            }
        }
        
        strategy = Strategy(
            user_id=user_id,
            name="DSL Strategy",
            dsl_definition=dsl,
            dsl_hash="abc123",
            version=1
        )
        
        assert strategy.dsl_definition == dsl
        assert strategy.dsl_hash == "abc123"
        assert strategy.version == 1
    
    def test_strategy_timestamps_set_on_creation(self):
        """Should set created_at and updated_at on creation"""
        before = datetime.now(timezone.utc)
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Test"
        )
        after = datetime.now(timezone.utc)
        
        assert before <= strategy.created_at <= after
        assert before <= strategy.updated_at <= after


class TestStrategyActivation:
    """Test strategy activation/deactivation"""
    
    def test_activate_sets_is_active_true(self):
        """Should set is_active to True"""
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Test",
            is_active=False
        )
        
        strategy.activate()
        
        assert strategy.is_active is True
    
    def test_activate_updates_timestamp(self):
        """Should update updated_at when activating"""
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Test",
            is_active=False
        )
        before_update = strategy.updated_at
        
        strategy.activate()
        
        assert strategy.updated_at > before_update
    
    def test_deactivate_sets_is_active_false(self):
        """Should set is_active to False"""
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Test",
            is_active=True
        )
        
        strategy.deactivate()
        
        assert strategy.is_active is False
    
    def test_deactivate_updates_timestamp(self):
        """Should update updated_at when deactivating"""
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Test",
            is_active=True
        )
        before_update = strategy.updated_at
        
        strategy.deactivate()
        
        assert strategy.updated_at > before_update
    
    def test_activate_returns_self(self):
        """Should return self for method chaining"""
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Test"
        )
        
        result = strategy.activate()
        
        assert result is strategy
    
    def test_deactivate_returns_self(self):
        """Should return self for method chaining"""
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Test"
        )
        
        result = strategy.deactivate()
        
        assert result is strategy


class TestStrategyUpdates:
    """Test strategy update methods"""
    
    def test_update_name(self):
        """Should update name and timestamp"""
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Old Name"
        )
        before_update = strategy.updated_at
        
        strategy.update_name("New Name")
        
        assert strategy.name == "New Name"
        assert strategy.updated_at > before_update
    
    def test_update_name_returns_self(self):
        """Should return self for method chaining"""
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Test"
        )
        
        result = strategy.update_name("New Name")
        
        assert result is strategy
    
    def test_update_description(self):
        """Should update description and timestamp"""
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Test",
            description="Old description"
        )
        before_update = strategy.updated_at
        
        strategy.update_description("New description")
        
        assert strategy.description == "New description"
        assert strategy.updated_at > before_update
    
    def test_update_description_to_none(self):
        """Should allow setting description to None"""
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Test",
            description="Has description"
        )
        
        strategy.update_description(None)
        
        assert strategy.description is None
    
    def test_update_dsl(self):
        """Should update DSL definition, version, and timestamp"""
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Test",
            dsl_definition={"old": "dsl"},
            version=1
        )
        before_update = strategy.updated_at
        
        new_dsl = {"new": "dsl"}
        strategy.update_dsl(new_dsl, version=2)
        
        assert strategy.dsl_definition == new_dsl
        assert strategy.version == 2
        assert strategy.updated_at > before_update
    
    def test_update_dsl_returns_self(self):
        """Should return self for method chaining"""
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Test"
        )
        
        result = strategy.update_dsl({"test": "dsl"}, version=1)
        
        assert result is strategy
    
    def test_generic_update_single_field(self):
        """Should update single allowed field"""
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Test",
            is_active=True
        )
        
        strategy.update(is_active=False)
        
        assert strategy.is_active is False
    
    def test_generic_update_multiple_fields(self):
        """Should update multiple allowed fields"""
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Test",
            description="Old",
            version=1
        )
        
        strategy.update(
            name="New Name",
            description="New",
            version=2
        )
        
        assert strategy.name == "New Name"
        assert strategy.description == "New"
        assert strategy.version == 2
    
    def test_generic_update_rejects_invalid_field(self):
        """Should reject update to non-allowed field"""
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Test"
        )
        original_id = strategy.id
        
        with pytest.raises(ValueError, match="Cannot update field: id"):
            strategy.update(id=uuid.uuid4())
        
        assert strategy.id == original_id
    
    def test_generic_update_rejects_user_id(self):
        """Should not allow updating user_id"""
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Test"
        )
        original_user_id = strategy.user_id
        
        with pytest.raises(ValueError, match="Cannot update field: user_id"):
            strategy.update(user_id=uuid.uuid4())
        
        assert strategy.user_id == original_user_id
    
    def test_generic_update_updates_timestamp(self):
        """Should update timestamp on generic update"""
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Test"
        )
        before_update = strategy.updated_at
        
        strategy.update(name="New Name")
        
        assert strategy.updated_at > before_update
    
    def test_generic_update_returns_self(self):
        """Should return self for method chaining"""
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Test"
        )
        
        result = strategy.update(name="New Name")
        
        assert result is strategy
    
    def test_generic_update_with_dsl_hash(self):
        """Should allow updating dsl_hash field"""
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Test",
            dsl_hash=None
        )
        
        strategy.update(dsl_hash="new_hash_123")
        
        assert strategy.dsl_hash == "new_hash_123"


class TestStrategyValidation:
    """Test strategy validation rules"""
    
    def test_name_cannot_be_empty(self):
        """Should reject empty name"""
        with pytest.raises(ValueError):
            Strategy(
                user_id=uuid.uuid4(),
                name=""
            )
    
    def test_name_max_length(self):
        """Should enforce name max length"""
        with pytest.raises(ValueError):
            Strategy(
                user_id=uuid.uuid4(),
                name="a" * 101  # Exceeds 100 char limit
            )
    
    def test_description_max_length(self):
        """Should enforce description max length"""
        with pytest.raises(ValueError):
            Strategy(
                user_id=uuid.uuid4(),
                name="Test",
                description="a" * 501  # Exceeds 500 char limit
            )
    
    def test_version_must_be_positive(self):
        """Should reject version < 1"""
        with pytest.raises(ValueError):
            Strategy(
                user_id=uuid.uuid4(),
                name="Test",
                version=0
            )
    
    def test_version_can_be_greater_than_one(self):
        """Should accept version > 1"""
        strategy = Strategy(
            user_id=uuid.uuid4(),
            name="Test",
            version=5
        )
        
        assert strategy.version == 5


class TestStrategyOwnership:
    """Test strategy ownership concepts"""
    
    def test_strategy_has_user_id(self):
        """Should have user_id field"""
        user_id = uuid.uuid4()
        strategy = Strategy(
            user_id=user_id,
            name="Test"
        )
        
        assert strategy.user_id == user_id
    
    def test_user_id_cannot_be_changed(self):
        """Should not allow changing user_id"""
        original_user_id = uuid.uuid4()
        strategy = Strategy(
            user_id=original_user_id,
            name="Test"
        )
        
        with pytest.raises(ValueError):
            strategy.update(user_id=uuid.uuid4())


class TestStrategySerialization:
    """Test strategy serialization"""
    
    def test_strategy_to_dict(self):
        """Should serialize to dictionary"""
        user_id = uuid.uuid4()
        strategy = Strategy(
            user_id=user_id,
            name="Test",
            description="Test description",
            dsl_definition={"version": 1}
        )
        
        data = strategy.model_dump()
        
        assert data["name"] == "Test"
        assert data["description"] == "Test description"
        assert data["is_active"] is True
        assert data["dsl_definition"] == {"version": 1}
    
    def test_strategy_json_serialization(self):
        """Should serialize to JSON"""
        user_id = uuid.uuid4()
        strategy = Strategy(
            user_id=user_id,
            name="Test",
            dsl_definition={"key": "value"},
            dsl_hash="hash123"
        )
        
        json_str = strategy.model_dump_json()
        
        assert "Test" in json_str
        assert "hash123" in json_str
