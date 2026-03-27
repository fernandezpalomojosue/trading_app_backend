"""
Data validation and normalization tests for market endpoints
Tests business rules for data validation, normalization, and error handling
"""
import pytest
from app.domain.entities.market import MarketType
from tests.fixtures.market_fixtures import MockMarketRepository, MockMarketDataCache
from tests.fixtures.portfolio_fixtures import MockPortfolioRepository


@pytest.fixture
def mock_favorite_repository():
    """Mock favorite stock repository"""
    class MockFavoriteStockRepository:
        async def add_favorite(self, user_id, symbol):
            from app.domain.entities.favorite_stock import FavoriteStockEntity
            return FavoriteStockEntity(user_id=user_id, symbol=symbol.upper())
        
        async def remove_favorite(self, user_id, symbol):
            return None
        
        async def get_user_favorites(self, user_id):
            return []
        
        async def is_favorite(self, user_id, symbol):
            return False
        
        async def get_favorite_by_user_and_symbol(self, user_id, symbol):
            return None
    
    return MockFavoriteStockRepository()


@pytest.mark.asyncio
class TestDataValidationAndNormalization:
    """Test data validation and normalization business rules"""
    
    @pytest.fixture
    def mock_cache(self):
        return MockMarketDataCache()
    
    @pytest.fixture
    def mock_repository(self):
        return MockMarketRepository()

    @pytest.fixture
    def mock_portfolio_repository(self):
        return MockPortfolioRepository()
    
    @pytest.fixture
    def market_use_cases(self, mock_repository, mock_cache, mock_portfolio_repository, mock_favorite_repository):
        from app.domain.use_cases.market_use_cases import MarketUseCases
        return MarketUseCases(mock_repository, mock_cache, mock_portfolio_repository, mock_favorite_repository)
    
    async def test_validation_query_minimum_length(self, market_use_cases):
        """Search query should have minimum length of 2 characters"""
        # Test empty query
        results = await market_use_cases.search_assets("")
        assert len(results) == 0
        
        # Test single character
        results = await market_use_cases.search_assets("A")
        assert len(results) == 0
        
        # Test valid query
        mock_data = [
            {"symbol": "AAPL", "name": "Apple Inc.", "market": "stocks", "currency": "USD", "active": True, "id": "asset_AAPL"}
        ]
        market_use_cases.market_repository.data['search_AAPL'] = mock_data
        
        results = await market_use_cases.search_assets("AAPL")
        assert len(results) == 1
    
    async def test_validation_symbol_case_normalization(self, market_use_cases):
        """Symbols should be normalized to uppercase"""
        mock_data = [
            {"symbol": "AAPL", "name": "Apple Inc.", "market": "stocks", "currency": "USD", "active": True, "id": "asset_AAPL"}
        ]
        market_use_cases.market_repository.data['search_aapl'] = mock_data
        
        # Should find AAPL even with lowercase query
        results = await market_use_cases.search_assets("aapl")
        assert len(results) == 1
        assert results[0].symbol == "AAPL"
    
    async def test_validation_market_type_filtering(self, market_use_cases):
        """Should filter by market type correctly"""
        mock_data = [
            {"symbol": "AAPL", "name": "Apple Inc.", "market": "stocks", "currency": "USD", "active": True, "id": "asset_AAPL"},
            {"symbol": "BTC", "name": "Bitcoin", "market": "crypto", "currency": "USD", "active": True, "id": "asset_BTC"}
        ]
        market_use_cases.market_repository.data['search_test'] = mock_data
        
        # Test stocks filter
        results = await market_use_cases.search_assets("test", market_type=MarketType.STOCKS)
        assert len(results) == 1
        assert results[0].symbol == "AAPL"
        assert results[0].market == MarketType.STOCKS
        assert results[0].market.value == "stocks"
    
    async def test_validation_empty_results_handling(self, market_use_cases):
        """Should handle empty API results gracefully"""
        # Clear cache to ensure clean state
        await market_use_cases.cache_service.clear_pattern("assets_list_")
        
        # Test empty results array
        mock_data = {"results": []}
        market_use_cases.market_repository.data['market_2024-01-15'] = mock_data
        
        # Mock date utils to return our test date
        import app.utils.date_utils
        original_get_last_trading_day = app.utils.date_utils.get_last_trading_day
        app.utils.date_utils.get_last_trading_day = lambda: '2024-01-15'
        
        try:
            assets = await market_use_cases.get_assets_list(MarketType.STOCKS)
            assert len(assets) == 0
        
        finally:
            # Restore original function
            app.utils.date_utils.get_last_trading_day = original_get_last_trading_day
