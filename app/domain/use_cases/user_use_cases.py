# app/domain/use_cases/user_use_cases.py
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

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
    
    async def register_user(self, credentials: UserCredentials) -> UserEntity:
        """Register a new user"""
        # Check if user already exists
        if await self.user_repository.user_exists(credentials.email):
            raise ValueError("Email already registered")
        
        # Create user entity
        user = UserEntity(
            email=credentials.email,
            username=credentials.email.split("@")[0],  # Default username
            full_name=None,
            is_active=True,
            is_verified=True,
            is_superuser=False,
            balance=0.0
        )
        
        # Hash password
        hashed_password = self.password_service.hash_password(credentials.password)
        
        # Save user
        return await self.user_repository.create_user(user, hashed_password)
    
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
