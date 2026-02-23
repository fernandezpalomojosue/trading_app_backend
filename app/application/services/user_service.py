# app/application/services/user_service.py
from typing import Optional
from uuid import UUID

from app.application.dto.user_dto import UserResponse
from app.domain.entities.user import UserEntity, UserCredentials
from app.domain.use_cases.user_use_cases import UserRepository, PasswordService, TokenService, UserUseCases


class UserService:
    """Application service for user operations"""
    
    def __init__(self, user_use_cases: UserUseCases):
        self.user_use_cases = user_use_cases
    
    async def register_user(self, email: str, password: str, username: Optional[str] = None, full_name: Optional[str] = None) -> UserResponse:
        """Register a new user"""
        credentials = UserCredentials(email=email, password=password)
        
        return await self.user_use_cases.register_user(credentials, username, full_name)
    
    async def authenticate_user(self, email: str, password: str) -> Optional[str]:
        """Authenticate user and return access token"""
        return await self.user_use_cases.authenticate_user(email, password)
    
    async def get_user_profile(self, user_id: UUID) -> Optional[UserEntity]:
        """Get user profile"""
        return await self.user_use_cases.get_user_profile(user_id)
    
    async def get_user_profile_response(self, user_id: UUID) -> Optional[UserResponse]:
        """Get user profile as DTO"""
        return await self.user_use_cases.get_user_profile_response(user_id)
    
    async def update_balance(self, user_id: UUID, amount: float, operation: str = "add") -> UserEntity:
        """Update user balance"""
        is_addition = operation.lower() == "add"
        return await self.user_use_cases.update_user_balance(user_id, amount, is_addition)
