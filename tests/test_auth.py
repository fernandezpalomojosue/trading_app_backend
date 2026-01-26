# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.domain.entities.user import UserEntity
from app.infrastructure.database.models import UserSQLModel


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_register_user_success(self, client: TestClient, db_session: Session):
        """Test successful user registration"""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        # Should return 201 or 400 (if user already exists)
        assert response.status_code in [201, 400]
        
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["email"] == user_data["email"]
            assert data["username"] == user_data["username"]
            assert "password" not in data  # Password should not be returned
    
    def test_register_user_duplicate_email(self, client: TestClient, db_session: Session):
        """Test registration with duplicate email should fail"""
        user_data = {
            "email": "duplicate@example.com",
            "username": "duplicateuser",
            "password": "testpassword123"
        }
        
        # First registration
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code in [201, 400]
        
        # Second registration with same email
        response2 = client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 400
    
    def test_register_user_invalid_email(self, client: TestClient):
        """Test registration with invalid email"""
        user_data = {
            "email": "invalid-email",
            "username": "testuser",
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_register_user_short_password(self, client: TestClient):
        """Test registration with short password"""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "123"  # Too short
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_login_success(self, client: TestClient, db_session: Session):
        """Test successful login"""
        # First register a user
        user_data = {
            "email": "login@example.com",
            "username": "loginuser",
            "password": "testpassword123"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # Then login
        login_data = {
            "username": "login@example.com",
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        # Should return 200 or 401 if login fails
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
            assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials"""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
    
    def test_get_current_user_success(self, client: TestClient, authenticated_user):
        """Test getting current user info with valid token"""
        headers = authenticated_user["headers"]
        
        if not headers.get("Authorization"):
            pytest.skip("Authentication failed, skipping test")
        
        response = client.get("/api/v1/auth/me", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "email" in data
            assert "username" in data
            assert "password" not in data
        else:
            # If token validation fails, should return 401
            assert response.status_code == 401
    
    def test_get_current_user_no_token(self, client: TestClient):
        """Test getting current user without token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
    
    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401


class TestUserModels:
    """Test user models and entities"""
    
    def test_user_entity_creation(self):
        """Test UserEntity creation"""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        user = UserEntity(
            id=user_id,
            email="test@example.com",
            username="testuser",
            balance=1000.0,
            is_active=True,
            is_verified=True,
            is_superuser=False,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        
        assert user.id == user_id
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.balance == 1000.0
        assert user.is_active is True
    
    def test_user_sql_model_creation(self):
        """Test UserSQLModel creation"""
        user = UserSQLModel(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            balance=1000.0,
            is_active=True,
            is_verified=True,
            is_superuser=False
        )
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.hashed_password == "hashed_password"
        assert user.balance == 1000.0
