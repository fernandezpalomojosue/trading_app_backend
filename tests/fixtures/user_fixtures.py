"""
User-specific fixtures for testing
Provides reusable test data and mock implementations for user functionality
"""
import pytest
from datetime import datetime, timezone
from typing import List, Dict, Any
from unittest.mock import Mock

from app.domain.entities.user import UserEntity
from app.infrastructure.database.models import UserSQLModel
from app.domain.use_cases.user_use_cases import UserRepository


class MockUserRepository(UserRepository):
    """Mock user repository for testing"""
    
    def __init__(self):
        self.data = {}
        self.call_count = {}
        self.call_history = []
    
    async def get_by_id(self, user_id):
        self._record_call('get_by_id', user_id=user_id)
        return self.data.get(f'user_{user_id}')
    
    async def get_by_email(self, email):
        self._record_call('get_by_email', email=email)
        for key, user in self.data.items():
            if user.email == email:
                return user
        return None
    
    async def get_by_username(self, username):
        self._record_call('get_by_username', username=username)
        for key, user in self.data.items():
            if user.username == username:
                return user
        return None
    
    async def email_exists(self, email):
        self._record_call('email_exists', email=email)
        user = await self.get_by_email(email)
        return user is not None
    
    async def username_exists(self, username):
        self._record_call('username_exists', username=username)
        user = await self.get_by_username(username)
        return user is not None
    
    async def create(self, user):
        self._record_call('create', user=user)
        self.data[f'user_{user.id}'] = user
        return user
    
    async def update(self, user):
        self._record_call('update', user=user)
        self.data[f'user_{user.id}'] = user
        return user
    
    async def delete(self, user_id):
        self._record_call('delete', user_id=user_id)
        if f'user_{user_id}' in self.data:
            del self.data[f'user_{user_id}']
            return True
        return False
    
    def _record_call(self, method: str, **kwargs):
        """Record method calls for testing"""
        self.call_count[method] = self.call_count.get(method, 0) + 1
        self.call_history.append({
            'method': method,
            'kwargs': kwargs,
            'timestamp': datetime.now(timezone.utc)
        })
    
    def reset_call_tracking(self):
        """Reset call tracking for clean test state"""
        self.call_count.clear()
        self.call_history.clear()


@pytest.fixture
def mock_user_repository():
    """Mock user repository for testing"""
    return MockUserRepository()


@pytest.fixture
def sample_user():
    """Sample user entity for testing"""
    import uuid
    
    return UserEntity(
        id=uuid.uuid4(),
        email="test@example.com",
        username="testuser",
        balance=10000.0,  # Updated to match new default balance
        is_active=True,
        is_verified=True,
        is_superuser=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_user_sql():
    """Sample user SQL model for testing"""
    import uuid
    
    return UserSQLModel(
        id=uuid.uuid4(),
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        balance=10000.0,  # Updated to match new default balance
        is_active=True,
        is_verified=True,
        is_superuser=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_inactive_user():
    """Sample inactive user for testing"""
    import uuid
    
    return UserEntity(
        id=uuid.uuid4(),
        email="inactive@example.com",
        username="inactiveuser",
        balance=5000.0,
        is_active=False,
        is_verified=True,
        is_superuser=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_unverified_user():
    """Sample unverified user for testing"""
    import uuid
    
    return UserEntity(
        id=uuid.uuid4(),
        email="unverified@example.com",
        username="unverifieduser",
        balance=7500.0,
        is_active=True,
        is_verified=False,
        is_superuser=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_superuser():
    """Sample superuser for testing"""
    import uuid
    
    return UserEntity(
        id=uuid.uuid4(),
        email="admin@example.com",
        username="admin",
        balance=50000.0,
        is_active=True,
        is_verified=True,
        is_superuser=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def multiple_users():
    """Multiple users for comprehensive testing"""
    import uuid
    
    return [
        UserEntity(
            id=uuid.uuid4(),
            email="user1@example.com",
            username="user1",
            balance=10000.0,
            is_active=True,
            is_verified=True,
            is_superuser=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        UserEntity(
            id=uuid.uuid4(),
            email="user2@example.com",
            username="user2",
            balance=15000.0,
            is_active=True,
            is_verified=True,
            is_superuser=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        UserEntity(
            id=uuid.uuid4(),
            email="user3@example.com",
            username="user3",
            balance=25000.0,
            is_active=True,
            is_verified=True,
            is_superuser=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    ]


@pytest.fixture
def user_test_data():
    """Complete user test data set"""
    import uuid
    
    user_id = uuid.uuid4()
    
    return {
        "user_id": user_id,
        "user_entity": UserEntity(
            id=user_id,
            email="test@example.com",
            username="testuser",
            balance=10000.0,
            is_active=True,
            is_verified=True,
            is_superuser=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        "user_sql_model": UserSQLModel(
            id=user_id,
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            balance=10000.0,
            is_active=True,
            is_verified=True,
            is_superuser=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        "registration_data": {
            "email": "test@example.com",
            "username": "testuser",
            "password": "TestPassword123",
            "full_name": "Test User"
        },
        "login_data": {
            "username": "test@example.com",
            "password": "TestPassword123"
        }
    }


@pytest.fixture
def user_edge_cases():
    """Edge case scenarios for user testing"""
    import uuid
    
    return {
        "zero_balance_user": UserEntity(
            id=uuid.uuid4(),
            email="zero@example.com",
            username="zerobalance",
            balance=0.0,
            is_active=True,
            is_verified=True,
            is_superuser=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        "high_balance_user": UserEntity(
            id=uuid.uuid4(),
            email="high@example.com",
            username="highbalance",
            balance=1000000.0,
            is_active=True,
            is_verified=True,
            is_superuser=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        "fractional_balance_user": UserEntity(
            id=uuid.uuid4(),
            email="fractional@example.com",
            username="fractional",
            balance=12345.67,
            is_active=True,
            is_verified=True,
            is_superuser=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    }


@pytest.fixture
def user_credentials_data():
    """User credentials test data"""
    return {
        "valid_credentials": {
            "username": "test@example.com",
            "password": "TestPassword123"
        },
        "invalid_email": {
            "username": "invalid-email",
            "password": "TestPassword123"
        },
        "invalid_password": {
            "username": "test@example.com",
            "password": "wrong"
        },
        "missing_fields": {
            "username": "test@example.com"
            # Missing password
        },
        "empty_credentials": {
            "username": "",
            "password": ""
        }
    }
