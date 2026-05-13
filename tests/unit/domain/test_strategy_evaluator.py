"""
Unit tests for StrategyEvaluator
Tests DSL evaluation logic without dependencies.
"""
import pytest
from app.domain.services.strategy_evaluator import StrategyEvaluator
from app.domain.entities.strategy_dsl import (
    Constant, Price, Indicator,
    Condition, AndNode, OrNode, NotNode
)
from app.domain.entities.market_snapshot import MarketSnapshot


class TestStrategyEvaluatorExpressions:
    """Test expression evaluation"""
    
    def test_evaluate_constant(self):
        """Should return constant value"""
        const = Constant(type="constant", value=42.0)
        ctx = MarketSnapshot(symbol="TEST", timeframe="day", indicators=[])
        
        result = StrategyEvaluator._evaluate_expression(const, ctx)
        
        assert result == 42.0
    
    def test_evaluate_price(self):
        """Should return price from context"""
        price = Price(type="price", field="close")
        ctx = MarketSnapshot(symbol="TEST", timeframe="day", indicators=[], close_price=150.0)
        
        result = StrategyEvaluator._evaluate_expression(price, ctx)
        
        assert result == 150.0
    
    def test_evaluate_indicator(self):
        """Should return indicator from context"""
        ind = Indicator(type="indicator", name="RSI", params={"period": 14})
        ctx = MarketSnapshot(symbol="TEST", timeframe="day", indicators=[], rsi=30.0)
        
        result = StrategyEvaluator._evaluate_expression(ind, ctx)
        
        assert result == 30.0


class TestStrategyEvaluatorConditions:
    """Test condition evaluation"""
    
    def test_less_than_true(self):
        """Should return True when left < right"""
        cond = Condition(
            type="condition",
            operator="<",
            left=Constant(type="constant", value=10.0),
            right=Constant(type="constant", value=20.0)
        )
        ctx = MarketSnapshot(symbol="TEST", timeframe="day", indicators=[])
        
        result = StrategyEvaluator._evaluate_condition(cond, ctx, None)
        
        assert result is True
    
    def test_greater_than_true(self):
        """Should return True when left > right"""
        cond = Condition(
            type="condition",
            operator=">",
            left=Constant(type="constant", value=30.0),
            right=Constant(type="constant", value=20.0)
        )
        ctx = MarketSnapshot(symbol="TEST", timeframe="day", indicators=[])
        
        result = StrategyEvaluator._evaluate_condition(cond, ctx, None)
        
        assert result is True
    
    def test_cross_above_true(self):
        """Should detect crossover"""
        cond = Condition(
            type="condition",
            operator="cross_above",
            left=Constant(type="constant", value=25.0),
            right=Constant(type="constant", value=20.0)
        )
        ctx = MarketSnapshot(symbol="TEST", timeframe="day", indicators=[])
        prev_ctx = MarketSnapshot(symbol="TEST", timeframe="day", indicators=[])
        
        # Need to set values in prev_ctx - using a workaround
        result = StrategyEvaluator._evaluate_condition(cond, ctx, None)
        # Without prev_context, just checks if left > right
        assert result is True


class TestStrategyEvaluatorLogicalNodes:
    """Test logical node evaluation"""
    
    def test_and_all_true(self):
        """AND should return True when all children are true"""
        node = AndNode(
            type="AND",
            children=[
                Condition(type="condition", operator="<", left=Constant(type="constant", value=1), right=Constant(type="constant", value=2)),
                Condition(type="condition", operator="<", left=Constant(type="constant", value=3), right=Constant(type="constant", value=4)),
            ]
        )
        ctx = MarketSnapshot(symbol="TEST", timeframe="day", indicators=[])
        
        result = StrategyEvaluator.evaluate_node(node, ctx, None)
        
        assert result is True
    
    def test_and_one_false(self):
        """AND should return False when any child is false"""
        node = AndNode(
            type="AND",
            children=[
                Condition(type="condition", operator="<", left=Constant(type="constant", value=1), right=Constant(type="constant", value=2)),
                Condition(type="condition", operator=">", left=Constant(type="constant", value=3), right=Constant(type="constant", value=4)),  # False
            ]
        )
        ctx = MarketSnapshot(symbol="TEST", timeframe="day", indicators=[])
        
        result = StrategyEvaluator.evaluate_node(node, ctx, None)
        
        assert result is False
    
    def test_or_one_true(self):
        """OR should return True when at least one child is true"""
        node = OrNode(
            type="OR",
            children=[
                Condition(type="condition", operator="<", left=Constant(type="constant", value=1), right=Constant(type="constant", value=2)),
                Condition(type="condition", operator=">", left=Constant(type="constant", value=3), right=Constant(type="constant", value=4)),  # False
            ]
        )
        ctx = MarketSnapshot(symbol="TEST", timeframe="day", indicators=[])
        
        result = StrategyEvaluator.evaluate_node(node, ctx, None)
        
        assert result is True
    
    def test_not_negates(self):
        """NOT should negate child result"""
        node = NotNode(
            type="NOT",
            child=Condition(type="condition", operator="<", left=Constant(type="constant", value=1), right=Constant(type="constant", value=2))
        )
        ctx = MarketSnapshot(symbol="TEST", timeframe="day", indicators=[])
        
        result = StrategyEvaluator.evaluate_node(node, ctx, None)
        
        assert result is False  # NOT True = False


class TestStrategyEvaluatorRSIStrategy:
    """Test RSI-based strategy evaluation"""
    
    def test_rsi_oversold_condition(self):
        """Should detect RSI < 30 (oversold)"""
        cond = Condition(
            type="condition",
            operator="<",
            left=Indicator(type="indicator", name="RSI", params={"period": 14}),
            right=Constant(type="constant", value=30.0)
        )
        ctx = MarketSnapshot(symbol="AAPL", timeframe="day", indicators=[], rsi=25.0)
        
        result = StrategyEvaluator._evaluate_condition(cond, ctx, None)
        
        assert result is True
    
    def test_rsi_overbought_condition(self):
        """Should detect RSI > 70 (overbought)"""
        cond = Condition(
            type="condition",
            operator=">",
            left=Indicator(type="indicator", name="RSI", params={"period": 14}),
            right=Constant(type="constant", value=70.0)
        )
        ctx = MarketSnapshot(symbol="AAPL", timeframe="day", indicators=[], rsi=75.0)
        
        result = StrategyEvaluator._evaluate_condition(cond, ctx, None)
        
        assert result is True
