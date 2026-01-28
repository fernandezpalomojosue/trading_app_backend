"""
Unit tests for MarketUseCases - Domain orchestration logic
Tests focus on business rules, data transformation, and validation
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone
from app.domain.use_cases.market_use_cases import MarketUseCases, MarketRepository, MarketDataCache
from app.domain.entities.market import Asset, MarketType, MarketSummary, CandleStick


class MockMarketRepository(MarketRepository):
    """Mock implementation of MarketRepository for testing"""
    
    def __init__(self):
        self.data = {}
        self.call_count = {}
    
    async def get_asset_raw_data(self, symbol: str):
        self.call_count['get_asset_raw_data'] = self.call_count.get('get_asset_raw_data', 0) + 1
        return self.data.get(f'asset_{symbol}')
    
    async def search_assets_raw(self, query: str, market_type: MarketType = None):
        self.call_count['search_assets_raw'] = self.call_count.get('search_assets_raw', 0) + 1
        return self.data.get(f'search_{query}', [])
    
    async def fetch_raw_market_data(self, date: str):
        self.call_count['fetch_raw_market_data'] = self.call_count.get('fetch_raw_market_data', 0) + 1
        return self.data.get(f'market_{date}', {"results": []})
    
    async def fetch_symbol_data(self, symbol: str, date: str):
        self.call_count['fetch_symbol_data'] = self.call_count.get('fetch_symbol_data', 0) + 1
        return self.data.get(f'symbol_{symbol}_{date}')
    
    async def fetch_candlestick_data(self, symbol: str, multiplier: int, timespan: str, from_date: str, to_date: str, limit: int = 100):
        self.call_count['fetch_candlestick_data'] = self.call_count.get('fetch_candlestick_data', 0) + 1
        return self.data.get(f'candles_{symbol}_{timespan}_{from_date}_{to_date}')
    
    async def get_last_trading_date(self):
        self.call_count['get_last_trading_date'] = self.call_count.get('get_last_trading_date', 0) + 1
        return self.data.get('last_trading_date', '2024-01-15')
    
    async def fetch_ticker_details(self, symbol: str):
        self.call_count['fetch_ticker_details'] = self.call_count.get('fetch_ticker_details', 0) + 1
        return self.data.get(f'ticker_{symbol}')


class MockMarketDataCache(MarketDataCache):
    """Mock implementation of MarketDataCache for testing"""
    
    def __init__(self):
        self.cache = {}
        self.call_count = {}
    
    async def get(self, key: str):
        self.call_count['get'] = self.call_count.get('get', 0) + 1
        return self.cache.get(key)
    
    async def set(self, key: str, value, ttl: int = 300):
        self.call_count['set'] = self.call_count.get('set', 0) + 1
        self.cache[key] = value
    
    async def delete(self, key: str):
        self.call_count['delete'] = self.call_count.get('delete', 0) + 1
        if key in self.cache:
            del self.cache[key]
    
    async def clear_pattern(self, pattern: str):
        self.call_count['clear_pattern'] = self.call_count.get('clear_pattern', 0) + 1
        keys_to_delete = [k for k in self.cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self.cache[key]
    
    def get_stats(self):
        return {"entries": len(self.cache)}


class TestMarketUseCases:
    """Test MarketUseCases domain orchestration logic"""
    
    @pytest.fixture
    def mock_repository(self):
        return MockMarketRepository()
    
    @pytest.fixture
    def mock_cache(self):
        return MockMarketDataCache()
    
    @pytest.fixture
    def market_use_cases(self, mock_repository, mock_cache):
        return MarketUseCases(mock_repository, mock_cache)
    
    @pytest.fixture
    def sample_raw_market_data(self):
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
                }
            ]
        }
    
    @pytest.fixture
    def sample_raw_asset_data(self):
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
            "volume": 1000000
        }
    
    @pytest.fixture
    def sample_candlestick_data(self):
        """Sample candlestick data from external API"""
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
                }
            ]
        }
    
    async def test_convert_raw_to_entity_valid_data(self, market_use_cases):
        """Should convert valid raw data to MarketSummary entity"""
        raw_data = {
            "T": "AAPL",
            "c": 105.0,
            "o": 100.0,
            "h": 110.0,
            "l": 95.0,
            "v": 1000000,
            "vw": 102.5
        }
        
        entity = market_use_cases._convert_raw_to_entity(raw_data)
        
        assert entity is not None
        assert entity.symbol == "AAPL"
        assert entity.open == 100.0
        assert entity.close == 105.0
        assert entity.high == 110.0
        assert entity.low == 95.0
        assert entity.volume == 1000000
        assert entity.vwap == 102.5
        assert entity.change == 5.0
        assert entity.change_percent == 5.0
    
    async def test_convert_raw_to_entity_missing_required_fields(self, market_use_cases):
        """Should return None for missing required fields"""
        raw_data = {
            "T": "AAPL",
            "c": 105.0
            # Missing o, v
        }
        
        entity = market_use_cases._convert_raw_to_entity(raw_data)
        assert entity is None
    
    async def test_convert_raw_to_entity_zero_division_protection(self, market_use_cases):
        """Should handle zero open price gracefully"""
        raw_data = {
            "T": "AAPL",
            "c": 105.0,
            "o": 0.0,  # Zero open price
            "h": 110.0,
            "l": 95.0,
            "v": 1000000
        }
        
        entity = market_use_cases._convert_raw_to_entity(raw_data)
        
        assert entity is not None
        assert entity.change_percent == 0.0  # Should not crash
    
    async def test_convert_raw_to_asset_valid_data(self, market_use_cases, sample_raw_asset_data):
        """Should convert valid raw data to Asset entity"""
        asset = market_use_cases._convert_raw_to_asset(sample_raw_asset_data)
        
        assert asset is not None
        assert asset.id == "AAPL"
        assert asset.symbol == "AAPL"
        assert asset.name == "Apple Inc."
        assert asset.market == MarketType.STOCKS
        assert asset.currency == "USD"
        assert asset.active is True
        assert asset.price == 150.25
        assert asset.change == 2.25
        assert asset.change_percent == 1.52
        assert asset.volume == 1000000
    
    async def test_convert_raw_to_asset_empty_data(self, market_use_cases):
        """Should handle empty data gracefully"""
        asset = market_use_cases._convert_raw_to_asset({})
        assert asset is None
    
    async def test_convert_raw_to_asset_none_data(self, market_use_cases):
        """Should handle None data gracefully"""
        asset = market_use_cases._convert_raw_to_asset(None)
        assert asset is None
    
    def test_map_market_type_stocks(self, market_use_cases):
        """Should map stocks correctly"""
        market_type = market_use_cases._map_market_type("stocks")
        assert market_type == MarketType.STOCKS
    
    def test_map_market_type_crypto(self, market_use_cases):
        """Should map crypto correctly"""
        market_type = market_use_cases._map_market_type("crypto")
        assert market_type == MarketType.CRYPTO
    
    def test_map_market_type_fx(self, market_use_cases):
        """Should map fx correctly"""
        market_type = market_use_cases._map_market_type("fx")
        assert market_type == MarketType.FX
    
    def test_map_market_type_indices(self, market_use_cases):
        """Should map indices correctly"""
        market_type = market_use_cases._map_market_type("indices")
        assert market_type == MarketType.INDICES
    
    def test_map_market_type_unknown_defaults_to_stocks(self, market_use_cases):
        """Should default to stocks for unknown market types"""
        market_type = market_use_cases._map_market_type("unknown")
        assert market_type == MarketType.STOCKS
    
    def test_map_market_type_case_insensitive(self, market_use_cases):
        """Should handle case insensitive market types"""
        market_type = market_use_cases._map_market_type("STOCKS")
        assert market_type == MarketType.STOCKS
        
        market_type = market_use_cases._map_market_type("Crypto")
        assert market_type == MarketType.CRYPTO
    
    async def test_convert_raw_to_asset_basic_valid_data(self, market_use_cases):
        """Should convert basic raw market data to Asset entity"""
        raw_data = {
            "T": "AAPL",
            "c": 105.0,
            "o": 100.0,
            "v": 1000000,
            "h": 110.0,
            "l": 95.0,
            "vw": 102.5
        }
        
        asset = market_use_cases._convert_raw_to_asset_basic(raw_data, MarketType.STOCKS)
        
        assert asset is not None
        assert asset.id == "AAPL"
        assert asset.symbol == "AAPL"
        assert asset.name == "AAPL"  # Basic info uses symbol as name
        assert asset.market == MarketType.STOCKS
        assert asset.currency == "USD"
        assert asset.active is True
        assert asset.price == 105.0
        assert asset.change == 5.0
        assert asset.change_percent == 5.0
        assert asset.volume == 1000000
    
    async def test_convert_raw_to_asset_basic_missing_required_fields(self, market_use_cases):
        """Should return None for missing required fields"""
        raw_data = {
            "T": "AAPL",
            "c": 105.0
            # Missing v
        }
        
        asset = market_use_cases._convert_raw_to_asset_basic(raw_data, MarketType.STOCKS)
        assert asset is None
    
    async def test_convert_massive_to_candlestick_valid_data(self, market_use_cases):
        """Should convert Massive API data to CandleStick entity"""
        raw_data = {
            "o": 100.0,
            "h": 105.0,
            "l": 98.0,
            "c": 103.0,
            "v": 1000000,
            "t": 1642291200000  # Millisecond timestamp
        }
        
        candle = market_use_cases._convert_massive_to_candlestick(raw_data)
        
        assert candle is not None
        assert candle.open == 100.0
        assert candle.high == 105.0
        assert candle.low == 98.0
        assert candle.close == 103.0
        assert candle.volume == 1000000
        assert candle.timestamp.year == 2022
        assert candle.timestamp.month == 1
        assert candle.timestamp.day == 16
    
    async def test_convert_massive_to_candlestick_missing_fields(self, market_use_cases):
        """Should return None for missing required fields"""
        raw_data = {
            "o": 100.0,
            "h": 105.0
            # Missing l, c, v, t
        }
        
        candle = market_use_cases._convert_massive_to_candlestick(raw_data)
        assert candle is None
    
    def test_convert_to_massive_timespan_minute(self, market_use_cases):
        """Should convert minute timespan correctly"""
        timespan = market_use_cases._convert_to_massive_timespan("minute")
        assert timespan == "minute"
    
    def test_convert_to_massive_timespan_hour(self, market_use_cases):
        """Should convert hour timespan correctly"""
        timespan = market_use_cases._convert_to_massive_timespan("hour")
        assert timespan == "hour"
    
    def test_convert_to_massive_timespan_day(self, market_use_cases):
        """Should convert day timespan correctly"""
        timespan = market_use_cases._convert_to_massive_timespan("day")
        assert timespan == "day"
    
    def test_convert_to_massive_timespan_week(self, market_use_cases):
        """Should convert week timespan correctly"""
        timespan = market_use_cases._convert_to_massive_timespan("week")
        assert timespan == "week"
    
    def test_convert_to_massive_timespan_month(self, market_use_cases):
        """Should convert month timespan correctly"""
        timespan = market_use_cases._convert_to_massive_timespan("month")
        assert timespan == "month"
    
    def test_convert_to_massive_timespan_unknown_defaults_to_day(self, market_use_cases):
        """Should default to day for unknown timespans"""
        timespan = market_use_cases._convert_to_massive_timespan("unknown")
        assert timespan == "day"
    
    def test_convert_to_massive_timespan_case_insensitive(self, market_use_cases):
        """Should handle case insensitive timespans"""
        timespan = market_use_cases._convert_to_massive_timespan("DAY")
        assert timespan == "day"
    
    async def test_filter_top_assets_by_volume(self, market_use_cases):
        """Should filter assets to top N by volume"""
        assets = [
            Asset(id="A", symbol="A", name="A", market=MarketType.STOCKS, currency="USD", volume=1000),
            Asset(id="B", symbol="B", name="B", market=MarketType.STOCKS, currency="USD", volume=3000),
            Asset(id="C", symbol="C", name="C", market=MarketType.STOCKS, currency="USD", volume=2000),
            Asset(id="D", symbol="D", name="D", market=MarketType.STOCKS, currency="USD", volume=5000),
            Asset(id="E", symbol="E", name="E", market=MarketType.STOCKS, currency="USD", volume=None)
        ]
        
        filtered = market_use_cases._filter_top_assets_by_volume(assets, limit=3)
        
        assert len(filtered) == 3
        assert filtered[0].symbol == "D"  # 5000
        assert filtered[1].symbol == "B"  # 3000
        assert filtered[2].symbol == "C"  # 2000
    
    async def test_filter_top_assets_by_volume_empty_list(self, market_use_cases):
        """Should handle empty list gracefully"""
        filtered = market_use_cases._filter_top_assets_by_volume([], limit=5)
        assert len(filtered) == 0
    
    async def test_filter_top_assets_by_volume_none_volumes(self, market_use_cases):
        """Should handle None volumes correctly"""
        assets = [
            Asset(id="A", symbol="A", name="A", market=MarketType.STOCKS, currency="USD", volume=None),
            Asset(id="B", symbol="B", name="B", market=MarketType.STOCKS, currency="USD", volume=None)
        ]
        
        filtered = market_use_cases._filter_top_assets_by_volume(assets, limit=5)
        
        # Should return all assets when all have None volume
        assert len(filtered) == 2
