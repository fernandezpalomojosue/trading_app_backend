# tests/fixtures/indicators_fixtures.py
"""Test fixtures for indicators module"""
import pytest
from typing import List, Dict, Any, Optional


class MockIndicatorsClient:
    """Mock indicators client for testing"""
    
    def __init__(self):
        self.ema_data = []
        self.sma_data = []
        self.rsi_data = []
        self.macd_data = []
    
    async def fetch_ema(
        self,
        symbol: str,
        window: int,
        timespan: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Mock EMA data fetch"""
        return self.ema_data or [
            {"t": 1773028800000, "v": 150.5},
            {"t": 1773115200000, "v": 152.3},
            {"t": 1773201600000, "v": 151.8}
        ]
    
    async def fetch_sma(
        self,
        symbol: str,
        window: int,
        timespan: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Mock SMA data fetch"""
        return self.sma_data or [
            {"t": 1773028800000, "v": 148.0},
            {"t": 1773115200000, "v": 149.5},
            {"t": 1773201600000, "v": 150.2}
        ]
    
    async def fetch_rsi(
        self,
        symbol: str,
        window: int,
        timespan: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Mock RSI data fetch"""
        return self.rsi_data or [
            {"t": 1773028800000, "v": 65.5},
            {"t": 1773115200000, "v": 72.3},
            {"t": 1773201600000, "v": 58.8}
        ]
    
    async def fetch_macd(
        self,
        symbol: str,
        fast: int,
        slow: int,
        signal: int,
        timespan: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Mock MACD data fetch"""
        return self.macd_data or [
            {"t": 1773028800000, "macd": 2.5, "signal": 1.8, "histogram": 0.7},
            {"t": 1773115200000, "macd": 3.2, "signal": 2.1, "histogram": 1.1},
            {"t": 1773201600000, "macd": 1.8, "signal": 1.9, "histogram": -0.1}
        ]


@pytest.fixture
def mock_indicators_client():
    """Provide mock indicators client"""
    return MockIndicatorsClient()
