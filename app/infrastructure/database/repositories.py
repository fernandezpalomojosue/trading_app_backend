# app/infrastructure/database/repositories.py
from typing import Optional, List
from uuid import UUID
from sqlmodel import Session, select

from app.domain.entities.user import UserEntity
from app.domain.use_cases.user_use_cases import UserRepository
from app.infrastructure.database.models import UserSQLModel


class SQLUserRepository(UserRepository):
    
    def __init__(self, session: Session):
        self.session = session
    
    async def create_user(self, user: UserEntity, hashed_password: str) -> UserEntity:
        """Create a new user in the database"""
        user_model = UserSQLModel.from_domain_entity(user)
        user_model.hashed_password = hashed_password
        
        self.session.add(user_model)
        self.session.commit()
        self.session.refresh(user_model)
        
        return user_model.to_domain_entity()
    
    async def get_user_by_email(self, email: str) -> Optional[UserEntity]:
        """Get user by email"""
        statement = select(UserSQLModel).where(UserSQLModel.email == email)
        user_model = self.session.exec(statement).first()
        
        if user_model:
            return user_model.to_domain_entity()
        return None
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[UserEntity]:
        """Get user by ID"""
        statement = select(UserSQLModel).where(UserSQLModel.id == user_id)
        user_model = self.session.exec(statement).first()
        
        if user_model:
            return user_model.to_domain_entity()
        return None
    
    async def update_user(self, user: UserEntity) -> UserEntity:
        """Update user in database"""
        statement = select(UserSQLModel).where(UserSQLModel.id == user.id)
        user_model = self.session.exec(statement).first()
        
        if not user_model:
            raise ValueError("User not found")
        
        # Update fields using SQLModel approach
        user_data = user.model_dump(exclude_unset=True)
        for field, value in user_data.items():
            if hasattr(user_model, field):
                setattr(user_model, field, value)
        
        user_model.updated_at = user.updated_at
        
        self.session.add(user_model)
        self.session.commit()
        self.session.refresh(user_model)
        
        return user_model.to_domain_entity()
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Delete user from database"""
        statement = select(UserSQLModel).where(UserSQLModel.id == user_id)
        user_model = self.session.exec(statement).first()
        
        if user_model:
            self.session.delete(user_model)
            self.session.commit()
            return True
        return False
    
    async def user_exists(self, email: str) -> bool:
        """Check if user exists by email"""
        statement = select(UserSQLModel).where(UserSQLModel.email == email)
        user_model = self.session.exec(statement).first()
        return user_model is not None
    
    async def verify_password(self, email: str, password: str) -> bool:
        """Verify user password"""
        user_model = self.get_user_with_password(email)
        if not user_model:
            return False
        
        from app.infrastructure.security.password_service import PasslibPasswordService
        password_service = PasslibPasswordService()
        return password_service.verify_password(password, user_model.hashed_password)
    
    def get_user_with_password(self, email: str) -> Optional[UserSQLModel]:
        """Get user model with password (for authentication)"""
        statement = select(UserSQLModel).where(UserSQLModel.email == email)
        return self.session.exec(statement).first()