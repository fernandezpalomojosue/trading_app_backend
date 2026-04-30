"""
Unit tests for StrategyEngine
Tests full DSL evaluation integration.
"""
import pytest
from uuid import UUID
from app.domain.services.strategy_engine import StrategyEngine
from app.domain.entities.strategy import Strategy
from app.domain.entities.strategy_dsl import StrategyDSL
from app.domain.entities.market_context import MarketContext


class TestStrategyEngineEvaluate:
    """Test StrategyEngine.evaluate method"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.engine = StrategyEngine()
    
    def test_evaluate_buy_strategy_conditions_met(self):
        """Should return True when buy strategy conditions are met"""
        # Create a buy strategy: RSI < 30
        strategy = Strategy(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            user_id=UUID("12345678-1234-5678-1234-567812345678"),
            name="RSI Oversold Buy",
            dsl_definition={
                "version": 1,
                "action": "buy",
                "root": {
                    "type": "condition",
                    "operator": "<",
                    "left": {"type": "indicator", "name": "RSI", "params": {"period": 14}},
                    "right": {"type": "constant", "value": 30.0}
                }
            },
            version=1
        )
        
        # Context with RSI = 25 (oversold)
        context = MarketContext(symbol="AAPL", timestamp=0, rsi=25.0)
        
        result = self.engine.evaluate(strategy, context)
        
        assert result is True
    
    def test_evaluate_buy_strategy_conditions_not_met(self):
        """Should return False when buy strategy conditions are not met"""
        strategy = Strategy(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            user_id=UUID("12345678-1234-5678-1234-567812345678"),
            name="RSI Oversold Buy",
            dsl_definition={
                "version": 1,
                "action": "buy",
                "root": {
                    "type": "condition",
                    "operator": "<",
                    "left": {"type": "indicator", "name": "RSI", "params": {"period": 14}},
                    "right": {"type": "constant", "value": 30.0}
                }
            },
            version=1
        )
        
        # Context with RSI = 50 (neutral)
        context = MarketContext(symbol="AAPL", timestamp=0, rsi=50.0)
        
        result = self.engine.evaluate(strategy, context)
        
        assert result is False
    
    def test_evaluate_complex_and_strategy(self):
        """Should evaluate AND strategy with multiple conditions"""
        strategy = Strategy(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            user_id=UUID("12345678-1234-5678-1234-567812345678"),
            name="Complex Buy Strategy",
            dsl_definition={
                "version": 1,
                "action": "buy",
                "root": {
                    "type": "AND",
                    "children": [
                        {
                            "type": "condition",
                            "operator": "<",
                            "left": {"type": "indicator", "name": "RSI", "params": {"period": 14}},
                            "right": {"type": "constant", "value": 30.0}
                        },
                        {
                            "type": "condition",
                            "operator": ">",
                            "left": {"type": "price", "field": "close"},
                            "right": {"type": "indicator", "name": "SMA", "params": {"period": 200}}
                        }
                    ]
                }
            },
            version=1
        )
        
        # Context meeting both conditions
        context = MarketContext(
            symbol="AAPL", 
            timestamp=0, 
            rsi=25.0,  # < 30
            close_price=150.0,
            sma=140.0  # Price > SMA
        )
        
        result = self.engine.evaluate(strategy, context)
        
        assert result is True
    
    def test_evaluate_dsl_directly(self):
        """Should evaluate DSL directly"""
        dsl = StrategyDSL(
            version=1,
            action="sell",
            root={
                "type": "condition",
                "operator": ">",
                "left": {"type": "indicator", "name": "RSI", "params": {"period": 14}},
                "right": {"type": "constant", "value": 70.0}
            }
        )
        
        context = MarketContext(symbol="AAPL", timestamp=0, rsi=75.0)
        
        result = self.engine.evaluate_dsl(dsl, context)
        
        assert result is True
    
    def test_invalid_dsl_raises_error(self):
        """Should raise ValueError for invalid DSL"""
        strategy = Strategy(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            user_id=UUID("12345678-1234-5678-1234-567812345678"),
            name="Invalid Strategy",
            dsl_definition={
                "version": 1,
                "action": "buy",
                "root": "invalid"  # Invalid root
            },
            version=1
        )
        
        context = MarketContext(symbol="AAPL", timestamp=0)
        
        with pytest.raises(ValueError, match="Invalid DSL definition"):
            self.engine.evaluate(strategy, context)
