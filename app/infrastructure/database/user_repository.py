# app/infrastructure/database/user_repository.py
from typing import Optional
from uuid import UUID
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import UserEntity
from app.domain.use_cases.user_use_cases import UserRepository
from app.infrastructure.database.models import UserSQLModel


class SQLUserRepository(UserRepository):
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_user(self, user: UserEntity, hashed_password: str) -> UserEntity:
        """Create a new user in the database"""
        user_model = UserSQLModel.from_domain_entity(user)
        user_model.hashed_password = hashed_password
        
        self.session.add(user_model)
        await self.session.commit()
        await self.session.refresh(user_model)
        
        return user_model.to_domain_entity()
    
    async def get_user_by_email(self, email: str) -> Optional[UserEntity]:
        """Get user by email"""
        statement = select(UserSQLModel).where(UserSQLModel.email == email)
        result = await self.session.execute(statement)
        user_model = result.scalar_one_or_none()
        
        if user_model:
            return user_model.to_domain_entity()
        return None
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[UserEntity]:
        """Get user by ID"""
        statement = select(UserSQLModel).where(UserSQLModel.id == user_id)
        result = await self.session.execute(statement)
        user_model = result.scalar_one_or_none()
        
        if user_model:
            return user_model.to_domain_entity()
        return None
    
    async def update_user(self, user: UserEntity) -> UserEntity:
        """Update user in database"""
        statement = select(UserSQLModel).where(UserSQLModel.id == user.id)
        result = await self.session.execute(statement)
        user_model = result.scalar_one_or_none()
        
        if user_model:
            user_model.username = user.username
            user_model.full_name = user.full_name
            user_model.is_active = user.is_active
            user_model.is_verified = user.is_verified
            user_model.is_superuser = user.is_superuser
            user_model.balance = user.balance
            user_model.updated_at = user.updated_at
            
            await self.session.commit()
            await self.session.refresh(user_model)
            
            return user_model.to_domain_entity()
        
        return user
    
    async def verify_password(self, email: str, password: str) -> bool:
        """Verify user password"""
        user_model = await self.get_user_with_password(email)
        
        if not user_model:
            return False
        
        from app.infrastructure.security.password_service import PasslibPasswordService
        password_service = PasslibPasswordService()
        return password_service.verify_password(password, user_model.hashed_password)
    
    async def get_user_with_password(self, email: str) -> Optional[UserSQLModel]:
        """Get user model with password (for authentication)"""
        statement = select(UserSQLModel).where(UserSQLModel.email == email)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Delete user from database"""
        statement = select(UserSQLModel).where(UserSQLModel.id == user_id)
        result = await self.session.execute(statement)
        user_model = result.scalar_one_or_none()
        
        if user_model:
            await self.session.delete(user_model)
            await self.session.commit()
            return True
        
        return False
    
    async def user_exists(self, email: str) -> bool:
        """Check if user exists by email"""
        statement = select(UserSQLModel).where(UserSQLModel.email == email)
        result = await self.session.execute(statement)
        user_model = result.scalar_one_or_none()
        return user_model is not None
