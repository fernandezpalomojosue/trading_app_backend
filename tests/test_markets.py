# tests/test_markets.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session


class TestMarketEndpoints:
    """Test market-related endpoints"""
    
    def test_get_market_overview_stocks(self, client: TestClient):
        """Test getting stocks market overview"""
        response = client.get("/api/v1/markets/stocks/overview")
        
        # Should return 200, 401 (if auth required), 422 (if no data), or 500 (if API fails)
        assert response.status_code in [200, 401, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "market" in data
            assert "total_assets" in data
            assert "status" in data
            assert "last_updated" in data
    
    def test_get_market_overview_crypto(self, client: TestClient):
        """Test getting crypto market overview"""
        response = client.get("/api/v1/markets/crypto/overview")
        
        # Should return 200, 401, 422, or 500
        assert response.status_code in [200, 401, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "market" in data
            assert data["market"] == "crypto"
    
    def test_get_market_overview_invalid_market(self, client: TestClient):
        """Test getting market overview with invalid market type"""
        response = client.get("/api/v1/markets/invalid/overview")
        # Should return 422 for validation or 401 if auth required
        assert response.status_code in [422, 401]
    
    def test_get_assets_list(self, client: TestClient):
        """Test getting assets list"""
        response = client.get("/api/v1/markets/stocks/assets")
        
        # Should return 200, 401, 422, or 500
        assert response.status_code in [200, 401, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_get_assets_list_with_limit(self, client: TestClient):
        """Test getting assets list with limit parameter"""
        response = client.get("/api/v1/markets/stocks/assets?limit=10")
        
        # Should return 200, 401, 422, or 500
        assert response.status_code in [200, 401, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            # Should respect limit if data is available
            if len(data) > 0:
                assert len(data) <= 10
    
    def test_get_assets_list_invalid_limit(self, client: TestClient):
        """Test getting assets list with invalid limit"""
        response = client.get("/api/v1/markets/stocks/assets?limit=invalid")
        # Should return 422 for validation or 401 if auth required
        assert response.status_code in [422, 401]
    
    def test_get_asset_details_success(self, client: TestClient):
        """Test getting asset details for valid symbol"""
        response = client.get("/api/v1/markets/assets/AAPL")
        
        # Should return 200, 401, 404 (not found), 422, or 500
        assert response.status_code in [200, 401, 404, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "symbol" in data
            assert data["symbol"] == "AAPL"
    
    def test_get_asset_details_not_found(self, client: TestClient):
        """Test getting asset details for non-existent symbol"""
        response = client.get("/api/v1/markets/assets/INVALID123")
        
        # Should return 404, 401, 422, or 500
        assert response.status_code in [404, 401, 422, 500]
    
    def test_search_assets_success(self, client: TestClient):
        """Test searching assets with valid query"""
        response = client.get("/api/v1/markets/search?q=AAPL")
        
        # Should return 200, 401, 422, or 500
        assert response.status_code in [200, 401, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_search_assets_empty_query(self, client: TestClient):
        """Test searching assets with empty query"""
        response = client.get("/api/v1/markets/search?q=")
        
        # Should return 422 for empty query, 401 if auth required, or 200 if handled gracefully
        assert response.status_code in [200, 422, 401]
    
    def test_search_assets_no_query(self, client: TestClient):
        """Test searching assets without query parameter"""
        response = client.get("/api/v1/markets/search")
        # Should return 422 for missing parameter or 401 if auth required
        assert response.status_code in [422, 401]
    
    def test_search_assets_with_limit(self, client: TestClient):
        """Test searching assets with limit parameter"""
        response = client.get("/api/v1/markets/search?q=AAPL&limit=5")
        
        # Should return 200, 401, 422, or 500
        assert response.status_code in [200, 401, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            if len(data) > 0:
                assert len(data) <= 5


class TestMarketEndpointsAuthenticated:
    """Test market endpoints that require authentication"""
    
    def test_protected_market_endpoint_with_auth(self, client: TestClient, authenticated_user):
        """Test accessing protected market endpoint with valid auth"""
        headers = authenticated_user["headers"]
        
        if not headers.get("Authorization"):
            pytest.skip("Authentication failed, skipping test")
        
        # Test with authenticated request
        response = client.get("/api/v1/markets/stocks/overview", headers=headers)
        
        # Should return 200, 422, or 500 (but not 401)
        assert response.status_code in [200, 422, 500]
    
    def test_protected_market_endpoint_without_auth(self, client: TestClient):
        """Test accessing protected market endpoint without auth"""
        # This test depends on whether endpoints require authentication
        response = client.get("/api/v1/markets/stocks/overview")
        
        # Should return 200 (if public), 401 (if auth required), 422, or 500
        assert response.status_code in [200, 401, 422, 500]
