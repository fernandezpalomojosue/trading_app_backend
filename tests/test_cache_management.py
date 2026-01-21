# tests/test_cache_management.py
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.user import User, UserCreate
from app.core.security import verify_password


@pytest.fixture
def authenticated_user(client: TestClient, db_session: Session):
    """Create and authenticate a user for protected endpoint tests"""
    user_data = {
        "email": "cacheuser@example.com",
        "password": "testpassword123"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    login_data = {
        "username": "cacheuser@example.com",
        "password": "testpassword123"
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    return {"headers": {"Authorization": f"Bearer {token}"}}


def test_get_cache_stats_success(client: TestClient, authenticated_user):
    """Test getting cache statistics with authenticated user"""
    headers = authenticated_user["headers"]
    response = client.get("/api/v1/markets/cache/stats", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    # Cache stats should contain typical cache information
    assert "entries" in data or "size" in data or "stats" in data


def test_get_cache_stats_unauthorized(client: TestClient):
    """Test getting cache stats without authentication"""
    response = client.get("/api/v1/markets/cache/stats")
    
    assert response.status_code == 401


def test_clear_cache_success(client: TestClient, authenticated_user):
    """Test clearing cache with authenticated user"""
    headers = authenticated_user["headers"]
    response = client.delete("/api/v1/markets/cache", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "limpiado exitosamente" in data["message"]


def test_clear_cache_unauthorized(client: TestClient):
    """Test clearing cache without authentication"""
    response = client.delete("/api/v1/markets/cache")
    
    assert response.status_code == 401


def test_clear_market_summary_cache_success(client: TestClient, authenticated_user):
    """Test clearing market summary cache with authenticated user"""
    headers = authenticated_user["headers"]
    response = client.delete("/api/v1/markets/cache/market-summary", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "market summary limpiado exitosamente" in data["message"]


def test_clear_market_summary_cache_unauthorized(client: TestClient):
    """Test clearing market summary cache without authentication"""
    response = client.delete("/api/v1/markets/cache/market-summary")
    
    assert response.status_code == 401


@patch("app.api.v1.endpoints.markets.market_cache")
def test_cache_endpoints_with_mock_cache(mock_cache, client: TestClient, authenticated_user):
    """Test cache endpoints with mocked cache utilities"""
    headers = authenticated_user["headers"]
    
    # Mock get_stats
    mock_cache.get_stats.return_value = {
        "entries": 10,
        "hits": 100,
        "misses": 20,
        "hit_rate": 0.83
    }
    
    response = client.get("/api/v1/markets/cache/stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["entries"] == 10
    assert data["hit_rate"] == 0.83
    
    # Mock clear
    mock_cache.clear = AsyncMock()
    
    response = client.delete("/api/v1/markets/cache", headers=headers)
    assert response.status_code == 200
    mock_cache.clear.assert_called_once()
    
    # Mock clear_pattern
    mock_cache.clear_pattern = AsyncMock()
    
    response = client.delete("/api/v1/markets/cache/market-summary", headers=headers)
    assert response.status_code == 200
    mock_cache.clear_pattern.assert_called_once_with("get_daily_market_summary")


def test_cache_endpoints_with_invalid_token(client: TestClient):
    """Test cache endpoints with invalid authentication token"""
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    
    # Test all cache endpoints with invalid token
    endpoints = [
        ("/api/v1/markets/cache/stats", "GET"),
        ("/api/v1/markets/cache", "DELETE"),
        ("/api/v1/markets/cache/market-summary", "DELETE")
    ]
    
    for endpoint, method in endpoints:
        if method == "GET":
            response = client.get(endpoint, headers=invalid_headers)
        else:
            response = client.delete(endpoint, headers=invalid_headers)
        
        assert response.status_code == 401


def test_cache_endpoints_with_expired_token(client: TestClient, authenticated_user):
    """Test cache endpoints behavior with expired token (simulated)"""
    # This test would require mocking JWT token validation
    # For now, just test with malformed token
    malformed_headers = {"Authorization": "Bearer malformed.jwt.token"}
    
    response = client.get("/api/v1/markets/cache/stats", headers=malformed_headers)
    assert response.status_code == 401
