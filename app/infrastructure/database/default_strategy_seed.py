# app/infrastructure/database/default_strategy_seed.py
"""
Default Strategy Seed

System default strategy defined as DSL (not hardcoded).
Used when a user has no custom strategies.

This replaces the hardcoded SignalEngineUseCases rules with an equivalent DSL-based strategy.
"""
from typing import Dict, Any
import uuid

# System default strategy ID
DEFAULT_STRATEGY_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

# Default strategy definition (equivalent to old hardcoded rules)
# Buy when: RSI < 30 AND MACD crosses above signal AND Price > EMA
DEFAULT_STRATEGY_DSL: Dict[str, Any] = {
    "version": 1,
    "action": "buy",
    "root": {
        "type": "AND",
        "children": [
            {
                "type": "condition",
                "left": {"type": "indicator", "name": "RSI", "params": {"period": 14}},
                "operator": "<",
                "right": {"type": "constant", "value": 30}
            },
            {
                "type": "condition",
                "left": {"type": "indicator", "name": "MACD", "params": {"fast": 12, "slow": 26, "signal": 9}},
                "operator": "cross_above",
                "right": {"type": "indicator", "name": "MACD", "params": {"fast": 12, "slow": 26, "signal": 9}}
            },
            {
                "type": "condition",
                "left": {"type": "price", "field": "close"},
                "operator": ">",
                "right": {"type": "indicator", "name": "EMA", "params": {"period": 20}}
            }
        ]
    }
}

# Sell strategy example (for future use)
SELL_STRATEGY_DSL: Dict[str, Any] = {
    "version": 1,
    "action": "sell",
    "root": {
        "type": "AND",
        "children": [
            {
                "type": "condition",
                "left": {"type": "indicator", "name": "RSI", "params": {"period": 14}},
                "operator": ">",
                "right": {"type": "constant", "value": 70}
            },
            {
                "type": "condition",
                "left": {"type": "indicator", "name": "MACD", "params": {"fast": 12, "slow": 26, "signal": 9}},
                "operator": "cross_below",
                "right": {"type": "indicator", "name": "MACD", "params": {"fast": 12, "slow": 26, "signal": 9}}
            },
            {
                "type": "condition",
                "left": {"type": "price", "field": "close"},
                "operator": "<",
                "right": {"type": "indicator", "name": "EMA", "params": {"period": 20}}
            }
        ]
    }
}


def get_default_strategy_dsl() -> Dict[str, Any]:
    """
    Get the default strategy DSL definition.
    
    Returns:
        Default strategy DSL as JSON dict with action="buy"
    """
    return DEFAULT_STRATEGY_DSL.copy()


def get_default_strategy_entity():
    """
    Get the default strategy as a Strategy entity.
    
    Returns:
        Strategy entity with default DSL definition
    """
    from app.domain.entities.strategy import Strategy
    
    return Strategy(
        id=DEFAULT_STRATEGY_ID,
        user_id=DEFAULT_STRATEGY_ID,  # System user ID
        name="System Default Strategy",
        description="Default buy strategy activated when user has no custom strategies",
        is_active=True,
        dsl_definition=DEFAULT_STRATEGY_DSL.copy(),
        version=1
    )


def get_sell_strategy_dsl() -> Dict[str, Any]:
    """
    Get the default SELL strategy DSL definition.
    
    Returns:
        Sell strategy DSL as JSON dict with action="sell"
    """
    return SELL_STRATEGY_DSL.copy()
