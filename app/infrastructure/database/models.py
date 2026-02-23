# app/infrastructure/database/models.py
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import UUID


class UserSQLModel(SQLModel, table=True):
    """SQLModel for User table - Infrastructure layer"""
    __tablename__ = "users"
    
    # Use UUID for both production and testing (PostgreSQL)
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True, unique=True),
        description="ID único del usuario (UUID)"
    )
    email: str = Field(unique=True, index=True, description="Email del usuario")
    username: Optional[str] = Field(
        default=None, 
        index=True, 
        min_length=3, 
        max_length=50,
        description="Nombre de usuario único (opcional)"
    )
    full_name: Optional[str] = Field(
        default=None, 
        max_length=100, 
        description="Nombre completo del usuario"
    )
    hashed_password: str = Field(
        ..., 
        min_length=8, 
        description="Contraseña hasheada"
    )
    is_active: bool = Field(
        default=True, 
        description="Indica si el usuario está activo"
    )
    is_verified: bool = Field(
        default=True,
        description="Indica si el email del usuario ha sido verificado"
    )
    is_superuser: bool = Field(
        default=False, 
        description="Indica si el usuario es administrador"
    )
    balance: float = Field(
        default=0.0, 
        ge=0, 
        description="Saldo del usuario"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Fecha de creación del usuario"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Última actualización del usuario"
    )
    
    __table_args__ = (
        {'sqlite_autoincrement': False},
    )
    
    @classmethod
    def from_domain_entity(cls, user_entity):
        """Create SQLModel from domain entity"""
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
        """Convert SQLModel to domain entity"""
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
