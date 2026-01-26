# app/application/services/user_service.py
from typing import Optional
from uuid import UUID

from app.domain.entities.user import UserEntity, UserCredentials
from app.domain.use_cases.user_use_cases import UserRepository, PasswordService, TokenService, UserUseCases


class UserService:
    """Application service for user operations"""
    
    def __init__(self, user_use_cases: UserUseCases):
        self.user_use_cases = user_use_cases
    
    async def register_user(self, email: str, password: str, username: Optional[str] = None, full_name: Optional[str] = None) -> UserEntity:
        """Register a new user"""
        credentials = UserCredentials(email=email, password=password)
        
        user = await self.user_use_cases.register_user(credentials)
        
        # Update additional fields if provided
        if username:
            user.username = username
        if full_name:
            user.full_name = full_name
        
        return await self.user_use_cases.user_repository.update_user(user)
    
    async def authenticate_user(self, email: str, password: str) -> Optional[str]:
        """Authenticate user and return access token"""
        return await self.user_use_cases.authenticate_user(email, password)
    
    async def get_user_profile(self, user_id: UUID) -> Optional[UserEntity]:
        """Get user profile"""
        return await self.user_use_cases.get_user_profile(user_id)
    
    async def update_balance(self, user_id: UUID, amount: float, operation: str = "add") -> UserEntity:
        """Update user balance"""
        is_addition = operation.lower() == "add"
        return await self.user_use_cases.update_user_balance(user_id, amount, is_addition)
