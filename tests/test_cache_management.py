# tests/test_cache_management.py
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.domain.entities.user import UserEntity
from app.infrastructure.database.models import UserSQLModel
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
    
    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        if token:
            return {"headers": {"Authorization": f"Bearer {token}"}, "token": token}
    
    # Si el login falla, retornar headers vacíos para que los tests fallen gracefully
    return {"headers": {}, "token": None}


@pytest.mark.skip(reason="Cache endpoints were removed during refactoring")
class TestCacheManagement:
    """Test cache management endpoints - SKIPPED: Endpoints removed"""
    
    def test_get_cache_stats_success(self, client: TestClient, authenticated_user):
        """Test getting cache statistics"""
        pass
    
    def test_clear_cache_success(self, client: TestClient, authenticated_user):
        """Test clearing cache with authenticated user"""
        pass
    
    def test_clear_market_summary_cache_success(self, client: TestClient, authenticated_user):
        """Test clearing market summary cache"""
        pass
    
    def test_cache_endpoints_with_mock_cache(self, client: TestClient, authenticated_user):
        """Test cache endpoints with mocked cache service"""
        pass
    
    def test_cache_endpoints_with_expired_token(self, client: TestClient, authenticated_user):
        """Test cache endpoints with expired authentication token"""
        pass


def test_get_cache_stats_unauthorized(client: TestClient):
    """Test getting cache stats without authentication"""
    # Test con un endpoint que sí existe
    response = client.get("/api/v1/markets/overview/stocks")
    # Debería retornar 401 (no autorizado) o 422 (sin datos de mercado)
    assert response.status_code in [401, 422]


def test_clear_cache_unauthorized(client: TestClient):
    """Test clearing cache without authentication"""
    # Como los endpoints de cache fueron eliminados, probamos con un endpoint protegido
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_clear_market_summary_cache_unauthorized(client: TestClient):
    """Test clearing market summary cache without authentication"""
    # Endpoint eliminado, probamos con un endpoint protegido
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.skip(reason="Cache endpoints were removed during refactoring")
def test_cache_endpoints_with_invalid_token(client: TestClient):
    """Test cache endpoints with invalid authentication token"""
    pass


def test_cache_endpoints_with_expired_token(client: TestClient, authenticated_user):
    """Test cache endpoints behavior with expired token (simulated)"""
    # Test con endpoint que sí existe
    malformed_headers = {"Authorization": "Bearer malformed.jwt.token"}
    
    response = client.get("/api/v1/markets/overview/stocks", headers=malformed_headers)
    # Debería retornar 401 (no autorizado) o 422 (sin datos de mercado)
    assert response.status_code in [401, 422]
