# app/application/services/user_service.py
from typing import Optional
from uuid import UUID
from abc import ABC, abstractmethod

from app.application.dto.user_dto import UserResponse
from app.domain.entities.user import UserEntity, UserCredentials


class UserService(ABC):
    """Application interface for user operations"""
    
    @abstractmethod
    async def register_user(self, credentials: UserCredentials, username: Optional[str] = None, full_name: Optional[str] = None) -> UserResponse:
        """Register a new user"""
        pass
    
    @abstractmethod
    async def authenticate_user(self, email: str, password: str) -> Optional[str]:
        """Authenticate user and return access token"""
        pass
    
    @abstractmethod
    async def get_user_profile(self, user_id: UUID) -> Optional[UserEntity]:
        """Get user profile"""
        pass
    
    @abstractmethod
    async def get_user_profile_response(self, user_id: UUID) -> Optional[UserResponse]:
        """Get user profile as DTO"""
        pass
    
    @abstractmethod
    async def update_balance(self, user_id: UUID, amount: float, is_addition: bool) -> UserEntity:
        """Update user balance"""
        pass
