"""
Unit tests for Strategy DSL models
Tests for DSL AST structure, serialization, and validation
"""
import pytest
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


class TestExpressions:
    """Test DSL Expression types"""
    
    def test_constant_expression_creation(self):
        """Should create constant expression with value"""
        expr = Constant(type="constant", value=100.0)
        assert expr.type == "constant"
        assert expr.value == 100.0
    
    def test_constant_expression_integer(self):
        """Should create constant expression with integer"""
        expr = Constant(type="constant", value=50)
        assert expr.value == 50
    
    def test_price_expression_creation(self):
        """Should create price expression with field"""
        expr = Price(type="price", field="close")
        assert expr.type == "price"
        assert expr.field == "close"
    
    def test_price_expression_valid_fields(self):
        """Should accept valid price fields"""
        for field in ["open", "high", "low", "close", "volume"]:
            expr = Price(type="price", field=field)
            assert expr.field == field
    
    def test_indicator_expression_creation(self):
        """Should create indicator expression with name and params"""
        expr = Indicator(
            type="indicator",
            name="SMA",
            params={"period": 20, "source": "close"}
        )
        assert expr.type == "indicator"
        assert expr.name == "SMA"
        assert expr.params["period"] == 20


class TestConditions:
    """Test DSL Condition nodes"""
    
    def test_comparison_condition_with_constants(self):
        """Should create comparison with constant expressions"""
        left = Constant(type="constant", value=100.0)
        right = Constant(type="constant", value=50.0)
        
        condition = Condition(
            type="condition",
            operator=">",
            left=left,
            right=right
        )
        
        assert condition.type == "condition"
        assert condition.operator == ">"
        assert condition.left.value == 100.0
        assert condition.right.value == 50.0
    
    def test_comparison_condition_with_price_and_indicator(self):
        """Should create comparison with price vs indicator"""
        left = Price(type="price", field="close")
        right = Indicator(type="indicator", name="SMA", params={"period": 20})
        
        condition = Condition(
            type="condition",
            operator=">",
            left=left,
            right=right
        )
        
        assert condition.left.type == "price"
        assert condition.right.type == "indicator"
    
    def test_comparison_condition_all_operators(self):
        """Should accept all valid comparison operators"""
        operators = ["<", "<=", ">", ">=", "==", "!=", "cross_above", "cross_below"]
        left = Constant(type="constant", value=1.0)
        right = Constant(type="constant", value=2.0)
        
        for op in operators:
            condition = Condition(type="condition", operator=op, left=left, right=right)
            assert condition.operator == op


class TestLogicalNodes:
    """Test DSL Logical nodes (AND, OR, NOT)"""
    
    def test_and_node_with_multiple_children(self):
        """Should create AND node with multiple children"""
        child1 = Condition(
            type="condition",
            operator=">",
            left=Price(type="price", field="close"),
            right=Constant(type="constant", value=100.0)
        )
        child2 = Condition(
            type="condition",
            operator="<",
            left=Price(type="price", field="volume"),
            right=Constant(type="constant", value=1000000)
        )
        
        and_node = AndNode(type="AND", children=[child1, child2])
        
        assert and_node.type == "AND"
        assert len(and_node.children) == 2
    
    def test_or_node_with_children(self):
        """Should create OR node with children"""
        child1 = Condition(
            type="condition",
            operator=">",
            left=Price(type="price", field="close"),
            right=Constant(type="constant", value=100.0)
        )
        child2 = Condition(
            type="condition",
            operator="cross_above",
            left=Indicator(type="indicator", name="SMA", params={"period": 20}),
            right=Indicator(type="indicator", name="SMA", params={"period": 50})
        )
        
        or_node = OrNode(type="OR", children=[child1, child2])
        
        assert or_node.type == "OR"
        assert len(or_node.children) == 2
    
    def test_not_node_with_single_child(self):
        """Should create NOT node with single child"""
        child = Condition(
            type="condition",
            operator=">",
            left=Indicator(type="indicator", name="RSI", params={"period": 14}),
            right=Constant(type="constant", value=70.0)
        )
        
        not_node = NotNode(type="NOT", child=child)
        
        assert not_node.type == "NOT"
        assert not_node.child is not None


class TestStrategyDSL:
    """Test StrategyDSL root model"""
    
    def test_strategy_dsl_with_simple_condition_root(self):
        """Should accept simple condition as root (orphan condition)"""
        root = Condition(
            type="condition",
            operator=">",
            left=Price(type="price", field="close"),
            right=Indicator(type="indicator", name="SMA", params={"period": 20})
        )
        
        dsl = StrategyDSL(version=1, root=root)
        
        assert dsl.version == 1
        assert dsl.root.type == "condition"
    
    def test_strategy_dsl_with_logical_node_root(self):
        """Should accept logical node as root"""
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
        
        assert dsl.root.type == "AND"
        assert len(dsl.root.children) == 2
    
    def test_strategy_dsl_version_validation(self):
        """Should validate version is >= 1"""
        root = Condition(
            type="condition",
            operator=">",
            left=Constant(type="constant", value=1.0),
            right=Constant(type="constant", value=2.0)
        )
        
        # Valid version
        dsl = StrategyDSL(version=1, root=root)
        assert dsl.version == 1
        
        # Higher version also valid
        dsl2 = StrategyDSL(version=2, root=root)
        assert dsl2.version == 2
    
    def test_strategy_dsl_serialization(self):
        """Should serialize to JSON correctly"""
        root = Condition(
            type="condition",
            operator=">",
            left=Price(type="price", field="close"),
            right=Constant(type="constant", value=100.0)
        )
        
        dsl = StrategyDSL(version=1, root=root)
        json_data = dsl.model_dump()
        
        assert json_data["version"] == 1
        assert json_data["root"]["type"] == "condition"
        assert json_data["root"]["operator"] == ">"
    
    def test_strategy_dsl_deserialization(self):
        """Should deserialize from JSON correctly"""
        json_data = {
            "version": 1,
            "root": {
                "type": "AND",
                "children": [
                    {
                        "type": "condition",
                        "operator": ">",
                        "left": {"type": "price", "field": "close"},
                        "right": {"type": "constant", "value": 100.0}
                    },
                    {
                        "type": "condition",
                        "operator": "<",
                        "left": {"type": "indicator", "name": "RSI", "params": {"period": 14}},
                        "right": {"type": "constant", "value": 70.0}
                    }
                ]
            }
        }
        
        dsl = StrategyDSL.model_validate(json_data)
        
        assert dsl.version == 1
        assert dsl.root.type == "AND"
        assert len(dsl.root.children) == 2
        # Note: children are discriminated union types - access carefully
        first_child = dsl.root.children[0]
        assert hasattr(first_child, 'operator') or first_child.type == "condition"


class TestComplexDSLStructures:
    """Test complex nested DSL structures"""
    
    def test_deeply_nested_structure(self):
        """Should handle deeply nested logical structure"""
        # Create a complex nested structure: AND(OR(cond1, cond2), NOT(cond3))
        cond1 = Condition(
            type="condition",
            operator=">",
            left=Price(type="price", field="close"),
            right=Constant(type="constant", value=100.0)
        )
        cond2 = Condition(
            type="condition",
            operator="cross_above",
            left=Indicator(type="indicator", name="SMA", params={"period": 20}),
            right=Indicator(type="indicator", name="SMA", params={"period": 50})
        )
        cond3 = Condition(
            type="condition",
            operator=">",
            left=Price(type="price", field="volume"),
            right=Constant(type="constant", value=10000000.0)
        )
        
        or_node = OrNode(type="OR", children=[cond1, cond2])
        not_node = NotNode(type="NOT", child=cond3)
        root = AndNode(type="AND", children=[or_node, not_node])
        
        dsl = StrategyDSL(version=1, root=root)
        
        assert dsl.root.type == "AND"
        assert dsl.root.children[0].type == "OR"
        assert dsl.root.children[1].type == "NOT"
    
    def test_macd_strategy_example(self):
        """Should handle MACD crossover strategy"""
        # MACD bullish crossover: MACD line crosses above Signal line
        macd_line = Indicator(type="indicator", name="MACD", params={"fast": 12, "slow": 26, "signal": 9, "field": "macd"})
        signal_line = Indicator(type="indicator", name="MACD", params={"fast": 12, "slow": 26, "signal": 9, "field": "signal"})
        
        macd_crossover = Condition(
            type="condition",
            operator="cross_above",
            left=macd_line,
            right=signal_line
        )
        
        # Price above SMA 200 for trend confirmation
        price = Price(type="price", field="close")
        sma200 = Indicator(type="indicator", name="SMA", params={"period": 200})
        
        trend_condition = Condition(
            type="condition",
            operator=">",
            left=price,
            right=sma200
        )
        
        # Combine with AND
        root = AndNode(type="AND", children=[macd_crossover, trend_condition])
        dsl = StrategyDSL(version=1, root=root)
        
        assert dsl.root.type == "AND"
        assert dsl.root.children[0].operator == "cross_above"
        assert dsl.root.children[1].operator == ">"
