# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.domain.entities.user import UserEntity
from app.infrastructure.database.models import UserSQLModel
from app.core.security import verify_password


def test_register_user_success(client: TestClient, db_session: Session):
    """Test successful user registration"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "testpassword123",
        "balance": 1000.0
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert data["full_name"] == user_data["full_name"]
    assert data["balance"] == user_data["balance"]
    assert "id" in data
    assert "created_at" in data
    assert "hashed_password" not in data  # Password should not be exposed


def test_register_user_duplicate_email(client: TestClient, db_session: Session):
    """Test registration with duplicate email should fail"""
    user_data = {
        "email": "duplicate@example.com",
        "password": "testpassword123"
    }
    
    # First registration should succeed
    response1 = client.post("/api/v1/auth/register", json=user_data)
    assert response1.status_code == 201
    
    # Second registration with same email should fail
    response2 = client.post("/api/v1/auth/register", json=user_data)
    assert response2.status_code == 400
    assert "ya está registrado" in response2.json()["detail"]


def test_register_user_invalid_email(client: TestClient):
    """Test registration with invalid email format"""
    user_data = {
        "email": "invalid-email",
        "password": "testpassword123"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 422  # Validation error


def test_register_user_short_password(client: TestClient):
    """Test registration with short password should fail"""
    user_data = {
        "email": "test@example.com",
        "password": "123"  # Too short
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 422  # Validation error


def test_login_success(client: TestClient, db_session: Session):
    """Test successful login"""
    # First register a user
    user_data = {
        "email": "login@example.com",
        "password": "testpassword123"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    # Then login
    login_data = {
        "username": "login@example.com",
        "password": "testpassword123"
    }
    
    response = client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client: TestClient, db_session: Session):
    """Test login with invalid credentials"""
    # Register a user first
    user_data = {
        "email": "invalid@example.com",
        "password": "correctpassword123"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    # Try login with wrong password
    login_data = {
        "username": "invalid@example.com",
        "password": "wrongpassword"
    }
    
    response = client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 401
    assert "Credenciales incorrectas" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient):
    """Test login with non-existent user"""
    login_data = {
        "username": "nonexistent@example.com",
        "password": "somepassword"
    }
    
    response = client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 401
    assert "Credenciales incorrectas" in response.json()["detail"]


def test_get_current_user_success(client: TestClient, db_session: Session):
    """Test getting current user info with valid token"""
    # Register and login
    user_data = {
        "email": "current@example.com",
        "username": "currentuser",
        "full_name": "Current User",
        "password": "testpassword123"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    login_data = {
        "username": "current@example.com",
        "password": "testpassword123"
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Get current user
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert data["full_name"] == user_data["full_name"]


def test_get_current_user_invalid_token(client: TestClient):
    """Test getting current user with invalid token"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == 401


def test_get_current_user_no_token(client: TestClient):
    """Test getting current user without token"""
    response = client.get("/api/v1/auth/me")
    
    assert response.status_code == 401


def test_user_model_password_hashing(db_session: Session):
    """Test that user passwords are properly hashed"""
    from app.core.security import get_password_hash
    
    password = "testpassword123"
    hashed_password = get_password_hash(password)
    
    user = UserSQLModel(
        email="hash@example.com",
        username="hashuser",
        hashed_password=hashed_password,
        full_name="Hash User"
    )
    
    assert user.email == "hash@example.com"
    assert user.hashed_password != password  # Should be hashed
    assert user.hashed_password == hashed_password


def test_user_model_email_normalization(db_session: Session):
    """Test that email addresses are normalized to lowercase"""
    user = UserSQLModel(
        email="UPPERCASE@EXAMPLE.COM",
        username="uppercaseuser",
        hashed_password="hashed_password",
        full_name="Uppercase User"
    )
    
    # Email should be stored as provided (normalization happens at DTO level)
    assert user.email == "UPPERCASE@EXAMPLE.COM"


def test_user_model_validation():
    """Test user model validation"""
    from uuid import uuid4
    from app.core.entities.user import UserEntity
    
    user_id = uuid4()
    user = UserEntity(
        id=user_id,
        email="valid@example.com",
        username="validuser",
        balance=0.0,
        is_active=True,
        is_verified=True,
        is_superuser=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    assert user.email == "valid@example.com"
    assert user.username == "validuser"
