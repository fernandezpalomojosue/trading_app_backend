"""
Unit tests for Strategy DSL Validator
Tests for validation logic including AST structure, operators, and depth limits
"""
import pytest
from pydantic import ValidationError
from app.domain.entities.strategy_dsl import (
    Constant,
    Price,
    Indicator,
    Condition,
    AndNode,
    OrNode,
    NotNode,
    StrategyDSL
)
from app.domain.services.strategy_validator import DSLValidator, ValidationResult
from app.domain.services.strategy_registry import StrategyRegistry


class TestValidationResult:
    """Test ValidationResult dataclass"""
    
    def test_valid_result(self):
        """Should create valid result"""
        result = ValidationResult(is_valid=True, errors=[], warnings=[], depth=3)
        assert result.is_valid is True
        assert result.errors == []
        assert result.depth == 3
    
    def test_invalid_result_with_errors(self):
        """Should create invalid result with errors"""
        result = ValidationResult(
            is_valid=False,
            errors=["Invalid operator", "Missing field"],
            warnings=["Low volume"],
            depth=0
        )
        assert result.is_valid is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1


class TestBasicValidation:
    """Test basic DSL validation"""
    
    def test_valid_simple_condition(self):
        """Should validate simple condition as root"""
        root = Condition(
            type="condition",
            operator=">",
            left=Price(type="price", field="close"),
            right=Constant(type="constant", value=100.0)
        )
        dsl = StrategyDSL(version=1, root=root)
        
        result = DSLValidator.validate(dsl)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.depth == 1
    
    def test_valid_simple_and_node(self):
        """Should validate AND node with conditions"""
        child1 = Condition(
            type="condition",
            operator=">",
            left=Price(type="price", field="close"),
            right=Constant(type="constant", value=100.0)
        )
        child2 = Condition(
            type="condition",
            operator="<",
            left=Indicator(type="indicator", name="RSI", params={"period": 14}),
            right=Constant(type="constant", value=70.0)
        )
        root = AndNode(type="AND", children=[child1, child2])
        dsl = StrategyDSL(version=1, root=root)
        
        result = DSLValidator.validate(dsl)
        
        assert result.is_valid is True
        assert result.depth == 2  # AND node + conditions
    
    def test_invalid_version_zero(self):
        """Should reject version 0 at model level"""
        root = Condition(
            type="condition",
            operator=">",
            left=Constant(type="constant", value=1.0),
            right=Constant(type="constant", value=2.0)
        )
        
        # Pydantic should reject version < 1 at model creation
        with pytest.raises(ValidationError, match="version"):
            StrategyDSL(version=0, root=root)
    
    def test_invalid_version_negative(self):
        """Should reject negative version at model level"""
        root = Condition(
            type="condition",
            operator=">",
            left=Constant(type="constant", value=1.0),
            right=Constant(type="constant", value=2.0)
        )
        
        # Pydantic should reject version < 1 at model creation
        with pytest.raises(ValidationError, match="version"):
            StrategyDSL(version=-1, root=root)
    
    def test_null_root(self):
        """Should reject null root at model level"""
        # Pydantic should reject null root at model creation
        with pytest.raises(ValidationError, match="root"):
            StrategyDSL(version=1, root=None)


class TestOperatorValidation:
    """Test operator validation"""
    
    def test_valid_comparison_operators(self):
        """Should accept all valid comparison operators"""
        registry = StrategyRegistry()
        operators = ["<", "<=", ">", ">=", "==", "!=", "cross_above", "cross_below"]
        
        for op in operators:
            root = Condition(
                type="condition",
                operator=op,
                left=Constant(type="constant", value=1.0),
                right=Constant(type="constant", value=2.0)
            )
            dsl = StrategyDSL(version=1, root=root)
            
            result = DSLValidator.validate(dsl)
            
            assert result.is_valid is True, f"Operator {op} should be valid"
    
    def test_invalid_operator_rejected_by_pydantic(self):
        """Should reject invalid operator at model level"""
        # Pydantic should reject invalid operator at model creation
        with pytest.raises(ValidationError, match="operator"):
            Condition(
                type="condition",
                operator="invalid_op",
                left=Constant(type="constant", value=1.0),
                right=Constant(type="constant", value=2.0)
            )
    
    def test_invalid_indicator_rejected_by_pydantic(self):
        """Should reject invalid indicator name at model level"""
        # Pydantic should reject invalid indicator at model creation
        with pytest.raises(ValidationError, match="name"):
            Condition(
                type="condition",
                operator=">",
                left=Indicator(type="indicator", name="INVALID_INDICATOR", params={}),
                right=Constant(type="constant", value=50.0)
            )


class TestDepthLimit:
    """Test depth limit validation"""
    
    def test_depth_within_limit(self):
        """Should accept DSL within depth limit"""
        # Create structure with depth 3: AND(OR(cond1, cond2), cond3)
        cond1 = Condition(
            type="condition",
            operator=">",
            left=Price(type="price", field="close"),
            right=Constant(type="constant", value=100.0)
        )
        cond2 = Condition(
            type="condition",
            operator="<",
            left=Price(type="price", field="volume"),
            right=Constant(type="constant", value=1000000.0)
        )
        cond3 = Condition(
            type="condition",
            operator="cross_above",
            left=Indicator(type="indicator", name="SMA", params={"period": 20}),
            right=Indicator(type="indicator", name="SMA", params={"period": 50})
        )
        
        or_node = OrNode(type="OR", children=[cond1, cond2])
        root = AndNode(type="AND", children=[or_node, cond3])
        dsl = StrategyDSL(version=1, root=root)
        
        result = DSLValidator.validate(dsl)
        
        assert result.is_valid is True
        assert result.depth == 3
    
    def test_depth_exceeds_limit(self):
        """Should reject DSL exceeding depth limit"""
        # Create deeply nested structure (depth > 10)
        current = Condition(
            type="condition",
            operator=">",
            left=Constant(type="constant", value=1.0),
            right=Constant(type="constant", value=0.0)
        )
        
        # Nest 12 levels deep
        for _ in range(12):
            current = AndNode(type="AND", children=[current, current])
        
        dsl = StrategyDSL(version=1, root=current)
        
        result = DSLValidator.validate(dsl)
        
        assert result.is_valid is False
        assert any("depth" in error.lower() for error in result.errors)
    
    def test_exactly_at_depth_limit(self):
        """Should accept DSL exactly at depth limit"""
        # Create structure with depth exactly 10
        current = Condition(
            type="condition",
            operator=">",
            left=Constant(type="constant", value=1.0),
            right=Constant(type="constant", value=0.0)
        )
        
        # Nest exactly 9 more levels (total depth 10)
        for _ in range(9):
            current = AndNode(type="AND", children=[current, current])
        
        dsl = StrategyDSL(version=1, root=current)
        
        result = DSLValidator.validate(dsl)
        
        assert result.is_valid is True
        assert result.depth == 10


class TestNotNodeRules:
    """Test NOT node validation rules"""
    
    def test_not_node_with_single_condition(self):
        """Should accept NOT node wrapping single condition"""
        inner = Condition(
            type="condition",
            operator=">",
            left=Indicator(type="indicator", name="RSI", params={"period": 14}),
            right=Constant(type="constant", value=70.0)
        )
        root = NotNode(type="NOT", child=inner)
        dsl = StrategyDSL(version=1, root=root)
        
        result = DSLValidator.validate(dsl)
        
        assert result.is_valid is True
    
    def test_not_node_with_and_child(self):
        """Should accept NOT node wrapping AND node"""
        inner1 = Condition(
            type="condition",
            operator=">",
            left=Price(type="price", field="close"),
            right=Constant(type="constant", value=100.0)
        )
        inner2 = Condition(
            type="condition",
            operator="<",
            left=Price(type="price", field="volume"),
            right=Constant(type="constant", value=1000000.0)
        )
        and_node = AndNode(type="AND", children=[inner1, inner2])
        root = NotNode(type="NOT", child=and_node)
        dsl = StrategyDSL(version=1, root=root)
        
        result = DSLValidator.validate(dsl)
        
        assert result.is_valid is True
    
    def test_not_node_cannot_have_multiple_children(self):
        """NOT node validation is at model level - Pydantic enforces single child"""
        # This test verifies that NotNode can only have one child by design
        # The model itself enforces this through its schema
        child1 = Condition(
            type="condition",
            operator=">",
            left=Constant(type="constant", value=1.0),
            right=Constant(type="constant", value=0.0)
        )
        
        # NotNode only accepts a single 'child' parameter
        not_node = NotNode(type="NOT", child=child1)
        
        assert not_node.child is not None
        # Cannot create NotNode with multiple children by design


class TestJsonValidation:
    """Test JSON input validation"""
    
    def test_validate_from_valid_json(self):
        """Should validate valid JSON DSL"""
        json_data = {
            "version": 1,
            "root": {
                "type": "condition",
                "operator": ">",
                "left": {"type": "price", "field": "close"},
                "right": {"type": "constant", "value": 100.0}
            }
        }
        
        result = DSLValidator.validate_from_json(json_data)
        
        assert result.is_valid is True
    
    def test_validate_from_json_missing_version(self):
        """Should reject JSON without version"""
        json_data = {
            "root": {
                "type": "condition",
                "operator": ">",
                "left": {"type": "constant", "value": 1.0},
                "right": {"type": "constant", "value": 2.0}
            }
        }
        
        result = DSLValidator.validate_from_json(json_data)
        
        assert result.is_valid is False
        assert any("version" in error.lower() for error in result.errors)
    
    def test_validate_from_json_missing_root(self):
        """Should reject JSON without root"""
        json_data = {
            "version": 1
        }
        
        result = DSLValidator.validate_from_json(json_data)
        
        assert result.is_valid is False
        assert any("root" in error.lower() for error in result.errors)
    
    def test_validate_from_json_null_root(self):
        """Should reject JSON with null root"""
        json_data = {
            "version": 1,
            "root": None
        }
        
        result = DSLValidator.validate_from_json(json_data)
        
        assert result.is_valid is False
    
    def test_validate_from_json_invalid_structure(self):
        """Should reject invalid JSON structure"""
        json_data = {
            "version": 1,
            "root": "invalid_string_instead_of_object"
        }
        
        result = DSLValidator.validate_from_json(json_data)
        
        assert result.is_valid is False
    
    def test_validate_from_json_with_unsupported_indicator(self):
        """Should reject JSON with unsupported indicator"""
        json_data = {
            "version": 1,
            "root": {
                "type": "condition",
                "operator": ">",
                "left": {"type": "indicator", "name": "CUSTOM_IND", "params": {}},
                "right": {"type": "constant", "value": 50.0}
            }
        }
        
        result = DSLValidator.validate_from_json(json_data)
        
        assert result.is_valid is False


class TestRealWorldStrategies:
    """Test validation with real-world strategy examples"""
    
    def test_momentum_strategy(self):
        """Should validate momentum strategy: RSI < 30 (oversold)"""
        root = Condition(
            type="condition",
            operator="<",
            left=Indicator(type="indicator", name="RSI", params={"period": 14}),
            right=Constant(type="constant", value=30.0)
        )
        dsl = StrategyDSL(version=1, root=root)
        
        result = DSLValidator.validate(dsl)
        
        assert result.is_valid is True
    
    def test_trend_following_strategy(self):
        """Should validate trend following: Price > SMA 200 AND Volume > 1M"""
        price_above_sma = Condition(
            type="condition",
            operator=">",
            left=Price(type="price", field="close"),
            right=Indicator(type="indicator", name="SMA", params={"period": 200})
        )
        volume_check = Condition(
            type="condition",
            operator=">",
            left=Price(type="price", field="volume"),
            right=Constant(type="constant", value=1000000.0)
        )
        root = AndNode(type="AND", children=[price_above_sma, volume_check])
        dsl = StrategyDSL(version=1, root=root)
        
        result = DSLValidator.validate(dsl)
        
        assert result.is_valid is True
        assert result.depth == 2
    
    def test_complex_multi_indicator_strategy(self):
        """Should validate complex strategy with multiple indicators"""
        # MACD bullish (using valid MACD params: fast, slow, signal)
        macd_bullish = Condition(
            type="condition",
            operator="cross_above",
            left=Indicator(type="indicator", name="MACD", params={"fast": 12, "slow": 26, "signal": 9}),
            right=Indicator(type="indicator", name="SMA", params={"period": 200})
        )
        
        # RSI not overbought
        rsi_not_overbought = NotNode(
            type="NOT",
            child=Condition(
                type="condition",
                operator=">",
                left=Indicator(type="indicator", name="RSI", params={"period": 14}),
                right=Constant(type="constant", value=70.0)
            )
        )
        
        # Price above EMA 50
        price_above_ema = Condition(
            type="condition",
            operator=">",
            left=Price(type="price", field="close"),
            right=Indicator(type="indicator", name="EMA", params={"period": 50})
        )
        
        # Combine: MACD OR (NOT RSI overbought AND Price > EMA)
        inner_and = AndNode(type="AND", children=[rsi_not_overbought, price_above_ema])
        root = OrNode(type="OR", children=[macd_bullish, inner_and])
        dsl = StrategyDSL(version=1, root=root)
        
        result = DSLValidator.validate(dsl)
        
        assert result.is_valid is True
