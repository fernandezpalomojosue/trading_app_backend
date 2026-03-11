# tests/conftest.py
import pytest
import uuid
import os
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.main import app
from app.db.base import get_session
from app.domain.entities.user import UserEntity
from app.infrastructure.database.models import UserSQLModel


@pytest.fixture(scope="session")
def engine():
    """Create test database engine using PostgreSQL"""
    # Use PostgreSQL for testing (same as development)
    test_db_url = os.getenv("DATABASE_URL")
    if not test_db_url:
        raise ValueError("DATABASE_URL environment variable is required for testing")
    
    engine = create_engine(test_db_url)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(engine):
    """Create test database session"""
    with Session(engine) as session:
        # Clean up database before each test
        from app.infrastructure.database.models import UserSQLModel, PortfolioHoldingSQLModel, TransactionSQLModel
        session.query(TransactionSQLModel).delete()
        session.query(PortfolioHoldingSQLModel).delete()
        session.query(UserSQLModel).delete()
        session.commit()
        
        yield session


@pytest.fixture
def client(db_session):
    """Create test client with database session override"""
    def override_get_session():
        yield db_session
    
    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# Import user fixtures
from tests.fixtures.user_fixtures import (
    sample_user,
    sample_user_sql,
    sample_inactive_user,
    sample_unverified_user,
    sample_superuser,
    multiple_users,
    user_test_data,
    user_edge_cases,
    user_credentials_data,
    mock_user_repository
)


@pytest.fixture
def authenticated_user(client: TestClient, db_session: Session):
    """Create and authenticate a user for protected endpoint tests"""
    user_data = {
        "email": "auth@example.com",
        "username": "authuser",
        "password": "Testpassword123"
    }
    
    # Register user
    register_response = client.post("/api/v1/auth/register", json=user_data)
    
    # Login to get token
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    
    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        if token:
            return {
                "headers": {"Authorization": f"Bearer {token}"}, 
                "token": token,
                "user_data": user_data
            }
    
    # Return empty headers if login failed
    return {"headers": {}, "token": None, "user_data": user_data}
