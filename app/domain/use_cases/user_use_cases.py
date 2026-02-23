# app/domain/use_cases/user_use_cases.py
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from app.application.dto.user_dto import UserResponse
from app.domain.entities.user import UserEntity, UserCredentials


class UserRepository(ABC):
    """Abstract repository for user operations"""
    
    @abstractmethod
    async def create_user(self, user: UserEntity, hashed_password: str) -> UserEntity:
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[UserEntity]:
        pass
    
    @abstractmethod
    async def get_user_by_id(self, user_id: UUID) -> Optional[UserEntity]:
        pass
    
    @abstractmethod
    async def update_user(self, user: UserEntity) -> UserEntity:
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: UUID) -> bool:
        pass
    
    @abstractmethod
    async def user_exists(self, email: str) -> bool:
        pass
    
    @abstractmethod
    async def verify_password(self, email: str, password: str) -> bool:
        pass


class PasswordService(ABC):
    """Abstract service for password operations"""
    
    @abstractmethod
    def hash_password(self, password: str) -> str:
        pass
    
    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        pass


class TokenService(ABC):
    """Abstract service for token operations"""
    
    @abstractmethod
    def create_access_token(self, data: dict) -> str:
        pass
    
    @abstractmethod
    def verify_token(self, token: str) -> Optional[str]:
        pass


class UserUseCases:
    """User business logic use cases"""
    
    def __init__(
        self,
        user_repository: UserRepository,
        password_service: PasswordService,
        token_service: TokenService
    ):
        self.user_repository = user_repository
        self.password_service = password_service
        self.token_service = token_service
    
    async def register_user(self, credentials: UserCredentials, username: Optional[str] = None, full_name: Optional[str] = None) -> UserResponse:
        """Register a new user"""
        # Check if user already exists
        if await self.user_repository.user_exists(credentials.email):
            raise ValueError("Email already registered")
        
        # Create user entity with provided fields or defaults
        user = UserEntity(
            email=credentials.email,
            username=username or credentials.email.split("@")[0],  # Use provided username or default
            full_name=full_name,  # Use provided full_name or None
            is_active=True,
            is_verified=True,
            is_superuser=False,
            balance=0.0
        )
        
        # Hash password
        hashed_password = self.password_service.hash_password(credentials.password)
        
        # Save user
        created_user = await self.user_repository.create_user(user, hashed_password)
        
        # Convert to DTO
        return UserResponse(
            id=created_user.id,
            email=created_user.email,
            username=created_user.username,
            full_name=created_user.full_name,
            is_active=created_user.is_active,
            is_verified=created_user.is_verified,
            is_superuser=created_user.is_superuser,
            balance=created_user.balance,
            created_at=created_user.created_at.isoformat(),
            updated_at=created_user.updated_at.isoformat()
        )
    
    async def authenticate_user(self, email: str, password: str) -> Optional[str]:
        """Authenticate user and return token"""
        # First verify the password
        if not await self.user_repository.verify_password(email, password):
            return None
        
        # Get the user
        user = await self.user_repository.get_user_by_email(email)
        if not user:
            return None
        
        # Create token
        token = self.token_service.create_access_token({"sub": email})
        return token
    
    async def get_user_profile(self, user_id: UUID) -> Optional[UserEntity]:
        """Get user profile by ID"""
        return await self.user_repository.get_user_by_id(user_id)
    
    async def get_user_profile_response(self, user_id: UUID) -> Optional[UserResponse]:
        """Get user profile by ID as DTO"""
        user = await self.user_repository.get_user_by_id(user_id)
        if not user:
            return None
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_superuser=user.is_superuser,
            balance=user.balance,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat()
        )
    
    async def update_user_balance(self, user_id: UUID, amount: float, is_addition: bool) -> UserEntity:
        """Update user balance"""
        user = await self.user_repository.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        if is_addition:
            user.add_balance(amount)
        else:
            user.subtract_balance(amount)
        
        return await self.user_repository.update_user(user)
