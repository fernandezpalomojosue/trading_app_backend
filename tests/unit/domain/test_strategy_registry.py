"""
Unit tests for Strategy Registry
Tests for operator and indicator registry functionality
"""
import pytest
from app.domain.services.strategy_registry import StrategyRegistry, IndicatorSpec


class TestOperators:
    """Test operator registry"""
    
    def test_all_operators_valid(self):
        """Should validate all supported operators"""
        operators = ["<", "<=", ">", ">=", "==", "!=", "cross_above", "cross_below"]
        
        for op in operators:
            assert StrategyRegistry.is_valid_operator(op), f"Operator {op} should be valid"
    
    def test_invalid_operator_rejected(self):
        """Should reject invalid operators"""
        assert StrategyRegistry.is_valid_operator("invalid") is False
        assert StrategyRegistry.is_valid_operator("") is False
        assert StrategyRegistry.is_valid_operator("AND") is False  # Logical operators are separate
        assert StrategyRegistry.is_valid_operator("OR") is False
    
    def test_get_all_operators(self):
        """Should return list of all operators"""
        operators = StrategyRegistry.get_all_operators()
        
        assert isinstance(operators, list)
        assert "<" in operators
        assert ">" in operators
        assert "cross_above" in operators
        assert len(operators) == 8


class TestIndicators:
    """Test indicator registry"""
    
    def test_sma_indicator_exists(self):
        """Should have SMA indicator"""
        assert StrategyRegistry.is_valid_indicator("SMA")
        spec = StrategyRegistry.get_indicator_spec("SMA")
        assert isinstance(spec, IndicatorSpec)
        assert "period" in spec.required_params
    
    def test_ema_indicator_exists(self):
        """Should have EMA indicator"""
        assert StrategyRegistry.is_valid_indicator("EMA")
        spec = StrategyRegistry.get_indicator_spec("EMA")
        assert isinstance(spec, IndicatorSpec)
        assert "period" in spec.required_params
    
    def test_rsi_indicator_exists(self):
        """Should have RSI indicator"""
        assert StrategyRegistry.is_valid_indicator("RSI")
        spec = StrategyRegistry.get_indicator_spec("RSI")
        assert isinstance(spec, IndicatorSpec)
        assert "period" in spec.required_params
    
    def test_macd_indicator_exists(self):
        """Should have MACD indicator"""
        assert StrategyRegistry.is_valid_indicator("MACD")
        spec = StrategyRegistry.get_indicator_spec("MACD")
        assert isinstance(spec, IndicatorSpec)
        assert "fast" in spec.required_params
        assert "slow" in spec.required_params
        assert "signal" in spec.required_params
    
    def test_invalid_indicator_rejected(self):
        """Should reject invalid indicators"""
        assert StrategyRegistry.is_valid_indicator("INVALID") is False
        assert StrategyRegistry.is_valid_indicator("") is False
        assert StrategyRegistry.is_valid_indicator("sma") is False  # Case sensitive
    
    def test_get_all_indicators(self):
        """Should return list of all indicators"""
        indicators = StrategyRegistry.get_all_indicators()
        
        assert isinstance(indicators, list)
        assert "SMA" in indicators
        assert "EMA" in indicators
        assert "RSI" in indicators
        assert "MACD" in indicators
        assert len(indicators) == 4
    
    def test_get_nonexistent_indicator_spec_raises(self):
        """Should raise ValueError for nonexistent indicator"""
        with pytest.raises(ValueError, match="Unknown indicator"):
            StrategyRegistry.get_indicator_spec("NONEXISTENT")


class TestIndicatorValidation:
    """Test indicator parameter validation"""
    
    def test_validate_sma_valid_params(self):
        """Should accept valid SMA params"""
        errors = StrategyRegistry.validate_indicator_params("SMA", {"period": 20})
        assert len(errors) == 0
    
    def test_validate_sma_missing_period(self):
        """Should reject SMA without period"""
        errors = StrategyRegistry.validate_indicator_params("SMA", {})
        assert len(errors) == 1
        assert "period" in errors[0]
    
    def test_validate_macd_valid_params(self):
        """Should accept valid MACD params"""
        errors = StrategyRegistry.validate_indicator_params(
            "MACD", {"fast": 12, "slow": 26, "signal": 9}
        )
        assert len(errors) == 0
    
    def test_validate_macd_missing_params(self):
        """Should reject MACD with missing params"""
        errors = StrategyRegistry.validate_indicator_params("MACD", {"fast": 12})
        assert len(errors) == 2  # slow and signal missing
    
    def test_validate_unknown_indicator(self):
        """Should return error for unknown indicator"""
        errors = StrategyRegistry.validate_indicator_params("UNKNOWN", {})
        assert len(errors) == 1
        assert "Unknown" in errors[0]


class TestPriceFields:
    """Test price field validation"""
    
    def test_valid_price_fields(self):
        """Should validate valid price fields"""
        valid_fields = ["open", "high", "low", "close", "volume"]
        for field in valid_fields:
            assert StrategyRegistry.is_valid_price_field(field), f"Field {field} should be valid"
    
    def test_invalid_price_field(self):
        """Should reject invalid price fields"""
        assert StrategyRegistry.is_valid_price_field("invalid") is False
        assert StrategyRegistry.is_valid_price_field("price") is False
        assert StrategyRegistry.is_valid_price_field("") is False


class TestNodeTypes:
    """Test node type validation"""
    
    def test_logical_node_types(self):
        """Should validate logical node types"""
        assert StrategyRegistry.is_logical_node("AND") is True
        assert StrategyRegistry.is_logical_node("OR") is True
        assert StrategyRegistry.is_logical_node("NOT") is True
        assert StrategyRegistry.is_logical_node("condition") is False
    
    def test_expression_types(self):
        """Should validate expression types"""
        assert StrategyRegistry.is_expression_type("constant") is True
        assert StrategyRegistry.is_expression_type("price") is True
        assert StrategyRegistry.is_expression_type("indicator") is True
        assert StrategyRegistry.is_expression_type("AND") is False
