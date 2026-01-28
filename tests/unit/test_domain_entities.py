"""
Unit tests for domain entities - Pure business logic validation
Tests focus on business rules, calculations, and invariants
"""
import pytest
from datetime import datetime, timezone
from app.domain.entities.market import Asset, MarketType, MarketSummary, CandleStick, MarketOverview


class TestAsset:
    """Test Asset entity business logic"""
    
    def test_asset_is_tradable_with_price_and_active(self):
        """Asset should be tradable when active and has price"""
        asset = Asset(
            id="AAPL",
            symbol="AAPL", 
            name="Apple Inc.",
            market=MarketType.STOCKS,
            currency="USD",
            active=True,
            price=150.25
        )
        
        assert asset.is_tradable() is True
    
    def test_asset_not_tradable_when_inactive(self):
        """Asset should not be tradable when inactive"""
        asset = Asset(
            id="AAPL",
            symbol="AAPL",
            name="Apple Inc.", 
            market=MarketType.STOCKS,
            currency="USD",
            active=False,
            price=150.25
        )
        
        assert asset.is_tradable() is False
    
    def test_asset_not_tradable_without_price(self):
        """Asset should not be tradable without price"""
        asset = Asset(
            id="AAPL",
            symbol="AAPL",
            name="Apple Inc.",
            market=MarketType.STOCKS, 
            currency="USD",
            active=True,
            price=None
        )
        
        assert asset.is_tradable() is False
    
    def test_asset_not_tradable_when_inactive_and_no_price(self):
        """Asset should not be tradable when inactive and no price"""
        asset = Asset(
            id="AAPL",
            symbol="AAPL",
            name="Apple Inc.",
            market=MarketType.STOCKS,
            currency="USD", 
            active=False,
            price=None
        )
        
        assert asset.is_tradable() is False


class TestMarketSummary:
    """Test MarketSummary entity business logic"""
    
    def test_is_positive_with_gain(self):
        """Market summary should be positive with gain"""
        summary = MarketSummary(
            symbol="AAPL",
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000,
            change=2.0
        )
        
        assert summary.is_positive is True
    
    def test_is_positive_with_loss(self):
        """Market summary should not be positive with loss"""
        summary = MarketSummary(
            symbol="AAPL",
            open=100.0,
            high=101.0,
            low=98.0,
            close=99.0,
            volume=1000000,
            change=-1.0
        )
        
        assert summary.is_positive is False
    
    def test_is_positive_with_no_change(self):
        """Market summary should not be positive with no change"""
        summary = MarketSummary(
            symbol="AAPL",
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=1000000,
            change=0.0
        )
        
        assert summary.is_positive is False
    
    def test_is_positive_with_none_change(self):
        """Market summary should not be positive with None change"""
        summary = MarketSummary(
            symbol="AAPL",
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=1000000,
            change=None
        )
        
        assert summary.is_positive is False
    
    def test_price_range_calculation(self):
        """Price range should be high - low"""
        summary = MarketSummary(
            symbol="AAPL",
            open=100.0,
            high=105.5,
            low=98.5,
            close=102.0,
            volume=1000000
        )
        
        assert summary.price_range == 7.0  # 105.5 - 98.5
    
    def test_price_range_with_same_high_low(self):
        """Price range should be zero when high equals low"""
        summary = MarketSummary(
            symbol="AAPL",
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=1000000
        )
        
        assert summary.price_range == 0.0


class TestCandleStick:
    """Test CandleStick entity business logic"""
    
    def test_is_green_bullish_candle(self):
        """Candle should be green when close > open"""
        timestamp = datetime.now(timezone.utc)
        candle = CandleStick(
            timestamp=timestamp,
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000000
        )
        
        assert candle.is_green is True
        assert candle.is_red is False
    
    def test_is_red_bearish_candle(self):
        """Candle should be red when close < open"""
        timestamp = datetime.now(timezone.utc)
        candle = CandleStick(
            timestamp=timestamp,
            open=100.0,
            high=101.0,
            low=97.0,
            close=98.0,
            volume=1000000
        )
        
        assert candle.is_red is True
        assert candle.is_green is False
    
    def test_neither_green_nor_red_when_equal(self):
        """Candle should be neither green nor red when close == open"""
        timestamp = datetime.now(timezone.utc)
        candle = CandleStick(
            timestamp=timestamp,
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=1000000
        )
        
        assert candle.is_green is False
        assert candle.is_red is False
    
    def test_body_size_calculation(self):
        """Body size should be absolute difference between close and open"""
        timestamp = datetime.now(timezone.utc)
        candle = CandleStick(
            timestamp=timestamp,
            open=100.0,
            high=105.0,
            low=97.0,
            close=103.0,
            volume=1000000
        )
        
        assert candle.body_size == 3.0  # |103.0 - 100.0|
    
    def test_upper_wick_calculation(self):
        """Upper wick should be high - max(open, close)"""
        timestamp = datetime.now(timezone.utc)
        candle = CandleStick(
            timestamp=timestamp,
            open=100.0,
            high=105.0,
            low=97.0,
            close=103.0,
            volume=1000000
        )
        
        assert candle.upper_wick == 2.0  # 105.0 - max(100.0, 103.0)
    
    def test_lower_wick_calculation(self):
        """Lower wick should be min(open, close) - low"""
        timestamp = datetime.now(timezone.utc)
        candle = CandleStick(
            timestamp=timestamp,
            open=100.0,
            high=105.0,
            low=97.0,
            close=103.0,
            volume=1000000
        )
        
        assert candle.lower_wick == 3.0  # min(100.0, 103.0) - 97.0
    
    def test_price_range_calculation(self):
        """Price range should be high - low"""
        timestamp = datetime.now(timezone.utc)
        candle = CandleStick(
            timestamp=timestamp,
            open=100.0,
            high=105.0,
            low=97.0,
            close=103.0,
            volume=1000000
        )
        
        assert candle.price_range == 8.0  # 105.0 - 97.0


class TestMarketOverview:
    """Test MarketOverview entity business logic"""
    
    def test_get_market_health_bullish(self):
        """Market should be bullish when gainers outperform losers"""
        timestamp = datetime.now(timezone.utc)
        
        gainers = [
            MarketSummary(symbol="A", open=100, high=110, low=90, close=105, volume=1000, change_percent=5.0),
            MarketSummary(symbol="B", open=100, high=115, low=90, close=110, volume=1000, change_percent=10.0)
        ]
        
        losers = [
            MarketSummary(symbol="C", open=100, high=105, low=90, close=95, volume=1000, change_percent=-5.0),
            MarketSummary(symbol="D", open=100, high=102, low=90, close=98, volume=1000, change_percent=-2.0)
        ]
        
        overview = MarketOverview(
            market=MarketType.STOCKS,
            total_assets=100,
            status="active",
            last_updated=timestamp,
            top_gainers=gainers,
            top_losers=losers
        )
        
        # Avg gainer: 7.5%, Avg loser: -3.5% -> Bullish
        assert overview.get_market_health() == "bullish"
    
    def test_get_market_health_bearish(self):
        """Market should be bearish when losers outperform gainers"""
        timestamp = datetime.now(timezone.utc)
        
        gainers = [
            MarketSummary(symbol="A", open=100, high=102, low=90, close=101, volume=1000, change_percent=1.0)
        ]
        
        losers = [
            MarketSummary(symbol="C", open=100, high=105, low=80, close=85, volume=1000, change_percent=-15.0),
            MarketSummary(symbol="D", open=100, high=102, low=85, close=90, volume=1000, change_percent=-10.0)
        ]
        
        overview = MarketOverview(
            market=MarketType.STOCKS,
            total_assets=100,
            status="active",
            last_updated=timestamp,
            top_gainers=gainers,
            top_losers=losers
        )
        
        # Avg gainer: 1.0%, Avg loser: -12.5% -> Bearish
        assert overview.get_market_health() == "bearish"
    
    def test_get_market_health_neutral(self):
        """Market should be neutral when gainers and losers are balanced"""
        timestamp = datetime.now(timezone.utc)
        
        gainers = [
            MarketSummary(symbol="A", open=100, high=110, low=90, close=105, volume=1000, change_percent=5.0)
        ]
        
        losers = [
            MarketSummary(symbol="C", open=100, high=105, low=90, close=95, volume=1000, change_percent=-5.0)
        ]
        
        overview = MarketOverview(
            market=MarketType.STOCKS,
            total_assets=100,
            status="active",
            last_updated=timestamp,
            top_gainers=gainers,
            top_losers=losers
        )
        
        # Avg gainer: 5.0%, Avg loser: -5.0% -> Neutral
        assert overview.get_market_health() == "neutral"
    
    def test_get_market_health_unknown_with_empty_data(self):
        """Market health should be unknown with no data"""
        timestamp = datetime.now(timezone.utc)
        
        overview = MarketOverview(
            market=MarketType.STOCKS,
            total_assets=100,
            status="active",
            last_updated=timestamp,
            top_gainers=[],
            top_losers=[]
        )
        
        assert overview.get_market_health() == "unknown"
