# app/infrastructure/database/models.py
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import UUID


class UserSQLModel(SQLModel, table=True):
    """SQLModel for User table"""
    __tablename__ = "users"
    
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True, unique=True),
        description="User unique ID (UUID)"
    )
    email: str = Field(unique=True, index=True, description="User email")
    username: Optional[str] = Field(
        default=None, 
        index=True, 
        min_length=3, 
        max_length=50,
        description="Unique username (optional)"
    )
    full_name: Optional[str] = Field(
        default=None, 
        max_length=100, 
        description="User full name"
    )
    hashed_password: str = Field(
        ..., 
        min_length=8, 
        description="Hashed password"
    )
    is_active: bool = Field(
        default=True, 
        description="Indicates if user is active"
    )
    is_verified: bool = Field(
        default=True,
        description="Indicates if user email has been verified"
    )
    is_superuser: bool = Field(
        default=False, 
        description="Indicates if user is admin"
    )
    balance: float = Field(
        default=0.0, 
        ge=0, 
        description="User balance"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="User creation date"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="User last update date"
    )
    
    __table_args__ = (
        {'sqlite_autoincrement': False},
    )
    
    @classmethod
    def from_domain_entity(cls, user_entity):
        return cls(
            id=user_entity.id,
            email=user_entity.email,
            username=user_entity.username,
            full_name=user_entity.full_name,
            is_active=user_entity.is_active,
            is_verified=user_entity.is_verified,
            is_superuser=user_entity.is_superuser,
            balance=user_entity.balance,
            created_at=user_entity.created_at,
            updated_at=user_entity.updated_at
        )
    
    def to_domain_entity(self):
        from app.domain.entities.user import UserEntity
        
        return UserEntity(
            id=self.id,
            email=self.email,
            username=self.username,
            full_name=self.full_name,
            is_active=self.is_active,
            is_verified=self.is_verified,
            is_superuser=self.is_superuser,
            balance=self.balance,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
