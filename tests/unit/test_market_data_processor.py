"""
Unit tests for MarketDataProcessor - Pure business logic
Tests focus on data processing algorithms and business rules
"""
import pytest
from datetime import datetime
from app.utils.market_utils import MarketDataProcessor
from app.domain.entities.market import MarketSummary


class TestMarketDataProcessor:
    """Test MarketDataProcessor pure business logic"""
    
    @pytest.fixture
    def sample_market_data(self):
        """Create sample market data for testing"""
        return [
            MarketSummary(
                symbol="AAPL",
                open=100.0,
                high=110.0,
                low=90.0,
                close=105.0,
                volume=1000000,
                change=5.0,
                change_percent=5.0
            ),
            MarketSummary(
                symbol="GOOGL",
                open=200.0,
                high=220.0,
                low=180.0,
                close=190.0,
                volume=800000,
                change=-10.0,
                change_percent=-5.0
            ),
            MarketSummary(
                symbol="MSFT",
                open=150.0,
                high=165.0,
                low=140.0,
                close=160.0,
                volume=1200000,
                change=10.0,
                change_percent=6.67
            ),
            MarketSummary(
                symbol="TSLA",
                open=300.0,
                high=310.0,
                low=280.0,
                close=285.0,
                volume=2000000,
                change=-15.0,
                change_percent=-5.0
            ),
            MarketSummary(
                symbol="AMZN",
                open=100.0,
                high=100.0,
                low=100.0,
                close=100.0,
                volume=500000,
                change=0.0,
                change_percent=0.0
            )
        ]
    
    def test_get_top_gainers_default_limit(self, sample_market_data):
        """Should return top 10 gainers sorted by change_percent descending"""
        gainers = MarketDataProcessor.get_top_gainers(sample_market_data)
        
        # Should only include positive change_percent
        assert len(gainers) == 2  # AAPL (5.0%), MSFT (6.67%)
        
        # Should be sorted by change_percent descending
        assert gainers[0].symbol == "MSFT"  # 6.67%
        assert gainers[1].symbol == "AAPL"  # 5.0%
        
        # All should have positive change_percent
        assert all(g.change_percent > 0 for g in gainers)
    
    def test_get_top_gainers_custom_limit(self, sample_market_data):
        """Should respect custom limit"""
        gainers = MarketDataProcessor.get_top_gainers(sample_market_data, limit=1)
        
        assert len(gainers) == 1
        assert gainers[0].symbol == "MSFT"  # Top gainer
    
    def test_get_top_gainers_no_gainers(self):
        """Should return empty list when no gainers"""
        data = [
            MarketSummary(
                symbol="LOSS1",
                open=100.0,
                high=100.0,
                low=90.0,
                close=95.0,
                volume=1000000,
                change=-5.0,
                change_percent=-5.0
            ),
            MarketSummary(
                symbol="LOSS2", 
                open=100.0,
                high=100.0,
                low=95.0,
                close=98.0,
                volume=1000000,
                change=-2.0,
                change_percent=-2.0
            )
        ]
        
        gainers = MarketDataProcessor.get_top_gainers(data)
        assert len(gainers) == 0
    
    def test_get_top_gainers_empty_data(self):
        """Should handle empty data gracefully"""
        gainers = MarketDataProcessor.get_top_gainers([])
        assert len(gainers) == 0
    
    def test_get_top_losers_default_limit(self, sample_market_data):
        """Should return top 10 losers sorted by change_percent ascending"""
        losers = MarketDataProcessor.get_top_losers(sample_market_data)
        
        # Should only include negative change_percent
        assert len(losers) == 2  # GOOGL (-5.0%), TSLA (-5.0%)
        
        # Should be sorted by change_percent ascending (most negative first)
        # Both have -5.0%, order doesn't matter between them
        assert all(l.change_percent < 0 for l in losers)
        assert all(l.symbol in ["GOOGL", "TSLA"] for l in losers)
    
    def test_get_top_losers_custom_limit(self, sample_market_data):
        """Should respect custom limit"""
        losers = MarketDataProcessor.get_top_losers(sample_market_data, limit=1)
        
        assert len(losers) == 1
        assert losers[0].change_percent < 0
    
    def test_top_losers_no_losers(self):
        """Should return empty list when no losers"""
        data = [
            MarketSummary(
                symbol="GAIN1",
                open=100.0,
                high=110.0,
                low=95.0,
                close=105.0,
                volume=1000000,
                change=5.0,
                change_percent=5.0
            ),
            MarketSummary(
                symbol="GAIN2",
                open=100.0,
                high=108.0,
                low=98.0,
                close=103.0,
                volume=1000000,
                change=3.0,
                change_percent=3.0
            )
        ]
        
        losers = MarketDataProcessor.get_top_losers(data)
        assert len(losers) == 0
    
    def test_get_most_active_default_limit(self, sample_market_data):
        """Should return top 10 most active sorted by volume descending"""
        active = MarketDataProcessor.get_most_active(sample_market_data)
        
        # Should return all (less than 10) sorted by volume
        assert len(active) == 5
        
        # Should be sorted by volume descending
        assert active[0].symbol == "TSLA"  # 2,000,000
        assert active[1].symbol == "MSFT"  # 1,200,000
        assert active[2].symbol == "AAPL"  # 1,000,000
        assert active[3].symbol == "GOOGL"  # 800,000
        assert active[4].symbol == "AMZN"  # 500,000
    
    def test_get_most_active_custom_limit(self, sample_market_data):
        """Should respect custom limit"""
        active = MarketDataProcessor.get_most_active(sample_market_data, limit=3)
        
        assert len(active) == 3
        assert active[0].symbol == "TSLA"  # Top by volume
        assert active[1].symbol == "MSFT"
        assert active[2].symbol == "AAPL"
    
    def test_get_most_active_empty_data(self):
        """Should handle empty data gracefully"""
        active = MarketDataProcessor.get_most_active([])
        assert len(active) == 0
    
    def test_calculate_total_assets(self, sample_market_data):
        """Should count unique symbols"""
        total = MarketDataProcessor.calculate_total_assets(sample_market_data)
        assert total == 5
    
    def test_calculate_total_assets_with_duplicates(self):
        """Should handle duplicate symbols correctly"""
        data = [
            MarketSummary(
                symbol="AAPL",
                open=100.0,
                high=110.0,
                low=90.0,
                close=105.0,
                volume=1000000,
                change=5.0,
                change_percent=5.0
            ),
            MarketSummary(
                symbol="AAPL",  # Duplicate
                open=100.0,
                high=110.0,
                low=90.0,
                close=105.0,
                volume=1000000,
                change=5.0,
                change_percent=5.0
            ),
            MarketSummary(
                symbol="GOOGL",
                open=200.0,
                high=220.0,
                low=180.0,
                close=190.0,
                volume=800000,
                change=-10.0,
                change_percent=-5.0
            )
        ]
        
        total = MarketDataProcessor.calculate_total_assets(data)
        assert total == 2  # AAPL and GOOGL only
    
    def test_calculate_total_assets_empty_data(self):
        """Should handle empty data gracefully"""
        total = MarketDataProcessor.calculate_total_assets([])
        assert total == 0
    
    def test_get_top_gainers_ignores_zero_change(self, sample_market_data):
        """Should ignore zero change_percent in gainers"""
        gainers = MarketDataProcessor.get_top_gainers(sample_market_data)
        
        # AMZN has 0.0% change and should not be included
        assert not any(g.symbol == "AMZN" for g in gainers)
    
    def test_get_top_losers_ignores_zero_change(self, sample_market_data):
        """Should ignore zero change_percent in losers"""
        losers = MarketDataProcessor.get_top_losers(sample_market_data)
        
        # AMZN has 0.0% change and should not be included
        assert not any(l.symbol == "AMZN" for l in losers)
    
    def test_get_most_active_includes_zero_change(self, sample_market_data):
        """Should include zero change in most active"""
        active = MarketDataProcessor.get_most_active(sample_market_data)
        
        # AMZN has 0.0% change but should be included in most active
        assert any(a.symbol == "AMZN" for a in active)
    
    def test_edge_case_same_change_percent(self):
        """Test handling of same change_percent values"""
        data = [
            MarketSummary(
                symbol="SAME1",
                open=100.0,
                high=110.0,
                low=90.0,
                close=105.0,
                volume=1000000,
                change=5.0,
                change_percent=5.0
            ),
            MarketSummary(
                symbol="SAME2",
                open=200.0,
                high=220.0,
                low=180.0,
                close=210.0,
                volume=800000,
                change=10.0,
                change_percent=5.0
            ),
            MarketSummary(
                symbol="SAME3",
                open=50.0,
                high=55.0,
                low=45.0,
                close=52.5,
                volume=600000,
                change=2.5,
                change_percent=5.0
            )
        ]
        
        gainers = MarketDataProcessor.get_top_gainers(data, limit=2)
        
        # All have same change_percent, should return any 2
        assert len(gainers) == 2
        assert all(g.change_percent == 5.0 for g in gainers)
        assert len(set(g.symbol for g in gainers)) == 2  # All different symbols
