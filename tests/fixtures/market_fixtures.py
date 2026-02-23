"""
Market-specific fixtures for testing
Provides reusable test data and mock implementations
"""
import pytest
from datetime import datetime, timezone
from typing import List, Dict, Any
from app.domain.entities.market import Asset, MarketType, MarketSummary, CandleStick
from app.domain.use_cases.market_use_cases import MarketRepository, MarketDataCache


class MockMarketRepository(MarketRepository):
    """Enhanced mock repository with configurable data"""
    
    def __init__(self):
        self.data = {}
        self.call_count = {}
        self.call_history = []
    
    async def get_asset_raw_data(self, symbol: str):
        self._record_call('get_asset_raw_data', symbol=symbol)
        return self.data.get(f'asset_{symbol}')
    
    async def search_assets_raw(self, query: str, market_type: MarketType = None):
        self._record_call('search_assets_raw', query=query, market_type=market_type)
        return self.data.get(f'search_{query}', [])
    
    async def fetch_raw_market_data(self, date: str):
        self._record_call('fetch_raw_market_data', date=date)
        return self.data.get(f'market_{date}', {"results": []})
    
    async def fetch_symbol_data(self, symbol: str, date: str):
        self._record_call('fetch_symbol_data', symbol=symbol, date=date)
        return self.data.get(f'symbol_{symbol}_{date}')
    
    async def fetch_candlestick_data(self, symbol: str, multiplier: int, timespan: str, from_date: str, to_date: str, limit: int = 100):
        self._record_call('fetch_candlestick_data', symbol=symbol, multiplier=multiplier, timespan=timespan, from_date=from_date, to_date=to_date, limit=limit)
        return self.data.get(f'candles_{symbol}_{timespan}_{from_date}_{to_date}')
    
    async def get_last_trading_date(self):
        self._record_call('get_last_trading_date')
        return self.data.get('last_trading_date', '2024-01-15')
    
    async def fetch_ticker_details(self, symbol: str):
        self._record_call('fetch_ticker_details', symbol=symbol)
        return self.data.get(f'ticker_{symbol}')
    
    def _record_call(self, method: str, **kwargs):
        """Record method calls for testing"""
        self.call_count[method] = self.call_count.get(method, 0) + 1
        self.call_history.append({
            'method': method,
            'kwargs': kwargs,
            'timestamp': datetime.now(timezone.utc)
        })
    
    def reset_call_tracking(self):
        """Reset call tracking for clean test state"""
        self.call_count.clear()
        self.call_history.clear()


class MockMarketDataCache(MarketDataCache):
    """Enhanced mock cache with configurable behavior"""
    
    def __init__(self, default_ttl: int = 300):
        self.default_ttl = default_ttl
        self.cache = {}
        self.call_count = {}
        self.ttl_settings = {}
    
    async def get(self, key: str):
        self.call_count['get'] = self.call_count.get('get', 0) + 1
        return self.cache.get(key)
    
    async def set(self, key: str, value, ttl: int = None):
        self.call_count['set'] = self.call_count.get('set', 0) + 1
        self.cache[key] = value
        self.ttl_settings[key] = ttl or self.default_ttl
    
    async def delete(self, key: str):
        self.call_count['delete'] = self.call_count.get('delete', 0) + 1
        if key in self.cache:
            del self.cache[key]
            if key in self.ttl_settings:
                del self.ttl_settings[key]
    
    async def clear_pattern(self, pattern: str):
        self.call_count['clear_pattern'] = self.call_count.get('clear_pattern', 0) + 1
        keys_to_delete = [k for k in self.cache.keys() if pattern in k]
        for key in keys_to_delete:
            await self.delete(key)
    
    def get_stats(self):
        return {
            "entries": len(self.cache),
            "ttl_settings": dict(self.ttl_settings)
        }
    
    def clear_all(self):
        """Clear all cache data"""
        self.cache.clear()
        self.ttl_settings.clear()
        self.call_count.clear()


@pytest.fixture
def mock_market_repository():
    """Mock market repository for testing"""
    return MockMarketRepository()


@pytest.fixture
def mock_market_cache():
    """Mock market cache for testing"""
    return MockMarketDataCache()


@pytest.fixture
def sample_asset():
    """Sample asset entity for testing"""
    return Asset(
        id="AAPL",
        symbol="AAPL",
        name="Apple Inc.",
        market=MarketType.STOCKS,
        currency="USD",
        active=True,
        price=150.25,
        change=2.25,
        change_percent=1.52,
        volume=1000000,
        details={
            "market_cap": 2500000000000,
            "primary_exchange": "NASDAQ",
            "description": "Technology company"
        }
    )


@pytest.fixture
def sample_crypto_asset():
    """Sample crypto asset entity for testing"""
    return Asset(
        id="BTC",
        symbol="BTC",
        name="Bitcoin",
        market=MarketType.CRYPTO,
        currency="USD",
        active=True,
        price=45000.50,
        change=500.25,
        change_percent=1.12,
        volume=2000000000,
        details={
            "market_cap": 850000000000,
            "circulating_supply": 19000000
        }
    )


@pytest.fixture
def sample_market_summary():
    """Sample market summary for testing"""
    return MarketSummary(
        symbol="AAPL",
        open=100.0,
        high=110.0,
        low=95.0,
        close=105.0,
        volume=1000000,
        vwap=102.5,
        change=5.0,
        change_percent=5.0,
        timestamp=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_candlestick():
    """Sample candlestick data for testing"""
    return CandleStick(
        timestamp=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
        open=100.0,
        high=105.0,
        low=98.0,
        close=103.0,
        volume=1000000
    )


@pytest.fixture
def sample_raw_market_data():
    """Sample raw market data from external API"""
    return {
        "results": [
            {
                "T": "AAPL",
                "c": 105.0,
                "o": 100.0,
                "h": 110.0,
                "l": 95.0,
                "v": 1000000,
                "vw": 102.5
            },
            {
                "T": "GOOGL",
                "c": 190.0,
                "o": 200.0,
                "h": 205.0,
                "l": 185.0,
                "v": 800000,
                "vw": 195.0
            },
            {
                "T": "MSFT",
                "c": 160.0,
                "o": 150.0,
                "h": 165.0,
                "l": 140.0,
                "v": 1200000,
                "vw": 155.0
            },
            {
                "T": "TSLA",
                "c": 285.0,
                "o": 300.0,
                "h": 310.0,
                "l": 280.0,
                "v": 2000000,
                "vw": 290.0
            }
        ]
    }


@pytest.fixture
def sample_raw_asset_data():
    """Sample raw asset data from external API"""
    return {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "market": "stocks",
        "currency_name": "USD",
        "active": True,
        "price": 150.25,
        "change": 2.25,
        "change_percent": 1.52,
        "volume": 1000000,
        "market_cap": 2500000000000,
        "primary_exchange": "NASDAQ",
        "description": "Technology company that designs, manufactures..."
    }


@pytest.fixture
def sample_raw_candlestick_data():
    """Sample raw candlestick data from external API"""
    return {
        "status": "OK",
        "results": [
            {
                "o": 100.0,
                "h": 105.0,
                "l": 98.0,
                "c": 103.0,
                "v": 1000000,
                "t": 1642291200000  # Millisecond timestamp
            },
            {
                "o": 103.0,
                "h": 108.0,
                "l": 101.0,
                "c": 107.0,
                "v": 1200000,
                "t": 1642377600000
            },
            {
                "o": 107.0,
                "h": 112.0,
                "l": 105.0,
                "c": 110.0,
                "v": 900000,
                "t": 1642464000000
            }
        ]
    }


@pytest.fixture
def multiple_market_summaries():
    """Multiple market summaries for comprehensive testing"""
    return [
        MarketSummary(
            symbol="GAINER1",
            open=100.0,
            high=110.0,
            low=90.0,
            close=108.0,
            volume=1000000,
            change=8.0,
            change_percent=8.0
        ),
        MarketSummary(
            symbol="GAINER2",
            open=50.0,
            high=55.0,
            low=45.0,
            close=54.0,
            volume=800000,
            change=4.0,
            change_percent=8.0
        ),
        MarketSummary(
            symbol="LOSER1",
            open=100.0,
            high=105.0,
            low=85.0,
            close=92.0,
            volume=1200000,
            change=-8.0,
            change_percent=-8.0
        ),
        MarketSummary(
            symbol="LOSER2",
            open=200.0,
            high=210.0,
            low=180.0,
            close=184.0,
            volume=600000,
            change=-16.0,
            change_percent=-8.0
        ),
        MarketSummary(
            symbol="NEUTRAL",
            open=75.0,
            high=75.0,
            low=75.0,
            close=75.0,
            volume=500000,
            change=0.0,
            change_percent=0.0
        )
    ]


@pytest.fixture
def invalid_raw_data_samples():
    """Various invalid raw data samples for validation testing"""
    return [
        # Missing required fields
        {"T": "AAPL", "c": 105.0},  # Missing o, v
        {"c": 105.0, "o": 100.0, "v": 1000000},  # Missing T
        {"T": "AAPL", "o": 100.0, "v": 1000000},  # Missing c
        
        # Invalid data types
        {"T": "AAPL", "c": "invalid", "o": 100.0, "v": 1000000},
        {"T": "AAPL", "c": 105.0, "o": "invalid", "v": 1000000},
        {"T": "AAPL", "c": 105.0, "o": 100.0, "v": "invalid"},
        
        # Zero division cases
        {"T": "AAPL", "c": 105.0, "o": 0.0, "v": 1000000},
        
        # Empty data
        {},
        None,
        
        # Negative values where inappropriate
        {"T": "AAPL", "c": 105.0, "o": 100.0, "v": -1000000}
    ]
