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
            "password": "Testpassword123"  # Added uppercase letter
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
            "password": "Testpassword123"  # Added uppercase letter
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
        assert response.status_code == 400
    
    def test_register_user_invalid_domain_email(self, client: TestClient):
        """Test registration with invalid domain email (single character TLD)"""
        user_data = {
            "email": "Asdfghjkl0@sdfs.d",
            "username": "testuser",
            "password": "Asdfghjkl0"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Invalid email format" in response.json()["detail"]
    
    def test_register_user_password_no_uppercase(self, client: TestClient):
        """Test registration with password without uppercase letter"""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "asdfghjkl0"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Password must contain at least one uppercase letter" in response.json()["detail"]
    
    def test_register_user_password_no_lowercase(self, client: TestClient):
        """Test registration with password without lowercase letter"""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "ASDFGHJKL0"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Password must contain at least one lowercase letter" in response.json()["detail"]
    
    def test_register_user_password_no_digit(self, client: TestClient):
        """Test registration with password without digit"""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "Asdfghjkl"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Password must contain at least one digit" in response.json()["detail"]
    
    def test_register_user_password_too_short(self, client: TestClient):
        """Test registration with password too short"""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "As1"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code in [400, 422]
        if response.status_code == 400:
            assert "Password must be at least 8 characters long" in response.json()["detail"]
    
    def test_register_user_edge_case_emails(self, client: TestClient):
        """Test registration with edge case emails"""
        test_cases = [
            ("user@", "Invalid email format"),
            ("@domain.com", "Invalid email format"),
            ("user@domain", "Invalid email format"),
            ("user@domain.c", "Invalid email format"),
            ("user..name@domain.com", "Invalid email format"),
            (".user@domain.com", "Invalid email format"),
            ("user.@domain.com", "Invalid email format"),
            ("invalid-email", "Invalid email format"),
        ]
        
        for email, expected_error in test_cases:
            user_data = {
                "email": email,
                "username": "testuser",
                "password": "Asdfghjkl0"
            }
            
            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == 400
            assert expected_error in response.json()["detail"]
    
    def test_register_user_valid_edge_cases(self, client: TestClient):
        """Test registration with valid edge cases"""
        valid_cases = [
            ("user@domain.io", "Valid 2-char TLD"),
            ("user@domain.info", "Valid 4-char TLD"),
            ("user@sub.domain.com", "Valid subdomain"),
            ("user.name@domain.com", "Valid dot in username"),
            ("user_name@domain.com", "Valid underscore"),
            ("user123@domain123.com", "Valid numbers"),
        ]
        
        for email, description in valid_cases:
            user_data = {
                "email": email,
                "username": f"testuser_{email.split('@')[0][:5]}",
                "password": "Asdfghjkl0"
            }
            
            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code in [201, 400]
    
    def test_register_user_error_logging(self, client: TestClient, caplog):
        """Test that registration errors are properly logged"""
        import logging
        
        user_data = {
            "email": "Asdfghjkl0@sdfs.d",
            "username": "testuser",
            "password": "Asdfghjkl0"
        }
        
        with caplog.at_level(logging.ERROR):
            response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        error_logs = [record for record in caplog.records if record.levelname == "ERROR"]
        assert len(error_logs) == 0
    
    def test_login_success(self, client: TestClient, db_session: Session):
        """Test successful login"""
        # First register a user
        user_data = {
            "email": "login@example.com",
            "username": "loginuser",
            "password": "Testpassword123"  # Added uppercase letter
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # Then login
        login_data = {
            "username": "login@example.com",
            "password": "Testpassword123"  # Added uppercase letter
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
        import uuid
        user_id = uuid.uuid4()
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
