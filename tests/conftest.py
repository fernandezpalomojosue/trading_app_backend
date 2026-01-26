# tests/conftest.py
import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.db.base import get_session
from app.domain.entities.user import UserEntity
from app.infrastructure.database.models import UserSQLModel


@pytest.fixture(scope="session")
def engine():
    """Create test database engine"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(engine):
    """Create test database session"""
    with Session(engine) as session:
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


@pytest.fixture
def sample_user():
    """Sample user entity for testing"""
    return UserEntity(
        id=uuid.uuid4(),
        email="test@example.com",
        username="testuser",
        balance=1000.0,
        is_active=True,
        is_verified=True,
        is_superuser=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def authenticated_user(client: TestClient, db_session: Session):
    """Create and authenticate a user for protected endpoint tests"""
    user_data = {
        "email": "auth@example.com",
        "username": "authuser",
        "password": "testpassword123"
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
