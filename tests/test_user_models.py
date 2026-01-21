# tests/test_user_models.py
import pytest
import uuid
from datetime import datetime, timezone
from sqlmodel import Session

from app.models.user import User, UserCreate, UserUpdate, UserPublic, Token, TokenData


class TestUserModel:
    """Test User model and related classes"""
    
    def test_user_create_valid_data(self):
        """Test creating UserCreate with valid data"""
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password="securepassword123",
            balance=1000.0
        )
        
        assert user_data.email == "test@example.com"
        assert user_data.username == "testuser"
        assert user_data.full_name == "Test User"
        assert user_data.password == "securepassword123"
        assert user_data.balance == 1000.0
        assert user_data.is_active is True  # Default value
        assert user_data.is_verified is True  # Default value
        assert user_data.is_superuser is False  # Default value
    
    def test_user_create_email_validation(self):
        """Test email validation in UserCreate"""
        # Valid emails
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "user123@test-domain.com"
        ]
        
        for email in valid_emails:
            user = UserCreate(email=email, password="test123")
            assert user.email == email.lower()  # Should be normalized
    
    def test_user_create_invalid_email(self):
        """Test invalid email validation"""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test.example.com",
            "test@.com",
            "test@example.",
            "",
            "test space@example.com"
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValueError, match="Formato de email inválido"):
                UserCreate(email=email, password="test123")
    
    def test_user_create_username_validation(self):
        """Test username validation"""
        # Valid usernames
        valid_usernames = [
            "testuser",
            "user123",
            "TestUser",
            "USER123"
        ]
        
        for username in valid_usernames:
            user = UserCreate(email="test@example.com", username=username, password="test123")
            assert user.username == username
        
        # Invalid usernames
        invalid_usernames = [
            "test user",  # Contains space
            "test@user",  # Contains special character
            "test#user",  # Contains special character
            "test.user",  # Contains dot
            "test-user"   # Contains hyphen
        ]
        
        for username in invalid_usernames:
            with pytest.raises(ValueError, match="solo puede contener letras y números"):
                UserCreate(email="test@example.com", username=username, password="test123")
    
    def test_user_create_optional_fields(self):
        """Test UserCreate with optional fields"""
        # Minimal valid user
        user = UserCreate(email="minimal@example.com", password="test123")
        
        assert user.email == "minimal@example.com"
        assert user.username is None
        assert user.full_name is None
        assert user.balance == 0.0  # Default value
    
    def test_user_create_user_method(self, db_session: Session):
        """Test UserCreate.create_user() method"""
        user_create = UserCreate(
            email="create@example.com",
            username="createuser",
            full_name="Create User",
            password="testpassword123",
            balance=500.0
        )
        
        user = user_create.create_user()
        
        assert user.email == "create@example.com"
        assert user.username == "createuser"
        assert user.full_name == "Create User"
        assert user.balance == 500.0
        assert user.is_active is True
        assert user.is_verified is True
        assert user.is_superuser is False
        assert user.hashed_password != "testpassword123"  # Should be hashed
        assert len(user.hashed_password) > 50  # Bcrypt hash length
        assert isinstance(user.id, uuid.UUID)
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
    
    def test_user_password_verification(self, db_session: Session):
        """Test User.verify_password() method"""
        user_create = UserCreate(
            email="verify@example.com",
            password="correctpassword123"
        )
        
        user = user_create.create_user()
        
        # Correct password should verify
        assert user.verify_password("correctpassword123") is True
        
        # Wrong password should not verify
        assert user.verify_password("wrongpassword") is False
        
        # Empty password should not verify
        assert user.verify_password("") is False
    
    def test_user_model_timestamps(self, db_session: Session):
        """Test user model timestamps"""
        before_creation = datetime.now(timezone.utc)
        
        user_create = UserCreate(
            email="timestamp@example.com",
            password="test123"
        )
        
        user = user_create.create_user()
        
        after_creation = datetime.now(timezone.utc)
        
        # Timestamps should be within reasonable range
        assert before_creation <= user.created_at <= after_creation
        assert before_creation <= user.updated_at <= after_creation
    
    def test_user_update_model(self):
        """Test UserUpdate model"""
        user_update = UserUpdate(
            email="new@example.com",
            username="newuser",
            full_name="New Name",
            password="newpassword123",
            is_active=False,
            is_superuser=True,
            balance=2000.0
        )
        
        assert user_update.email == "new@example.com"
        assert user_update.username == "newuser"
        assert user_update.full_name == "New Name"
        assert user_update.password == "newpassword123"
        assert user_update.is_active is False
        assert user_update.is_superuser is True
        assert user_update.balance == 2000.0
        
        # Test with partial updates
        partial_update = UserUpdate(
            email="partial@example.com",
            balance=1500.0
        )
        
        assert partial_update.email == "partial@example.com"
        assert partial_update.balance == 1500.0
        assert partial_update.username is None
        assert partial_update.full_name is None
        assert partial_update.password is None
        assert partial_update.is_active is None
        assert partial_update.is_superuser is None
    
    def test_user_public_model(self, db_session: Session):
        """Test UserPublic model"""
        user_create = UserCreate(
            email="public@example.com",
            username="publicuser",
            full_name="Public User",
            password="test123"
        )
        
        user = user_create.create_user()
        
        # UserPublic should include sensitive fields
        user_public = UserPublic(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_superuser=user.is_superuser,
            balance=user.balance,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        assert user_public.id == user.id
        assert user_public.email == user.email
        assert user_public.username == user.username
        assert user_public.full_name == user.full_name
        assert user_public.created_at == user.created_at
        assert user_public.updated_at == user.updated_at
        # Should not include hashed_password
    
    def test_token_models(self):
        """Test Token and TokenData models"""
        token = Token(
            access_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            token_type="bearer"
        )
        
        assert token.access_token == "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        assert token.token_type == "bearer"
        
        # Test with default token_type
        token_default = Token(access_token="test_token")
        assert token_default.token_type == "bearer"
        
        # Test TokenData
        token_data = TokenData(username="testuser")
        assert token_data.username == "testuser"
        
        # Test TokenData with optional username
        token_data_none = TokenData()
        assert token_data_none.username is None
    
    def test_user_model_constraints(self):
        """Test user model field constraints"""
        # Test balance constraint (ge=0)
        with pytest.raises(ValueError):
            UserCreate(email="test@example.com", password="test123", balance=-100.0)
        
        # Test password length constraints
        with pytest.raises(ValueError):
            UserCreate(email="test@example.com", password="123")  # Too short
        
        # Test username length constraints
        with pytest.raises(ValueError):
            UserCreate(
                email="test@example.com", 
                password="test123", 
                username="a" * 51  # Too long
            )
        
        # Test full_name length constraint
        with pytest.raises(ValueError):
            UserCreate(
                email="test@example.com", 
                password="test123", 
                full_name="a" * 101  # Too long
            )
    
    def test_user_model_email_case_insensitive(self):
        """Test email case normalization"""
        user_create = UserCreate(
            email="UPPERCASE@EXAMPLE.COM",
            password="test123"
        )
        
        user = user_create.create_user()
        
        # Email should be normalized to lowercase
        assert user.email == "uppercase@example.com"
        
        # Create another user with lowercase version should fail (unique constraint)
        user_create2 = UserCreate(
            email="uppercase@example.com",  # Same as normalized
            password="test123"
        )
        
        # This would fail at database level due to unique constraint
        # but we can't test that without actual database operations
    
    def test_user_model_defaults(self):
        """Test user model default values"""
        user_create = UserCreate(
            email="defaults@example.com",
            password="test123"
        )
        
        user = user_create.create_user()
        
        # Check default values
        assert user.is_active is True
        assert user.is_verified is True
        assert user.is_superuser is False
        assert user.balance == 0.0
    
    def test_user_model_dict_method(self, db_session: Session):
        """Test UserCreate dict method for database operations"""
        user_create = UserCreate(
            email="dict@example.com",
            username="dictuser",
            full_name="Dict User",
            password="test123",
            balance=1000.0,
            is_active=False
        )
        
        user = user_create.create_user()
        
        # Test that all expected fields are present
        assert hasattr(user, 'id')
        assert hasattr(user, 'email')
        assert hasattr(user, 'username')
        assert hasattr(user, 'full_name')
        assert hasattr(user, 'hashed_password')
        assert hasattr(user, 'is_active')
        assert hasattr(user, 'is_verified')
        assert hasattr(user, 'is_superuser')
        assert hasattr(user, 'balance')
        assert hasattr(user, 'created_at')
        assert hasattr(user, 'updated_at')
