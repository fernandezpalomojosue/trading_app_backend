# app/domain/entities/user.py
import uuid
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, validator
import re


class UserEntity(BaseModel):
    """Core user entity - pure business logic"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    email: str = Field(description="Email del usuario")
    username: Optional[str] = Field(
        default=None, 
        min_length=3, 
        max_length=50,
        description="Nombre de usuario único (opcional)"
    )
    full_name: Optional[str] = Field(
        default=None, 
        max_length=100, 
        description="Nombre completo del usuario"
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
    
    @validator('email')
    def validate_email(cls, v):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError("Formato de email inválido")
        return v.lower()
    
    @validator('username')
    def username_must_be_alphanumeric(cls, v):
        if v is not None and not v.isalnum():
            raise ValueError('El nombre de usuario solo puede contener letras y números')
        return v
    
    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now(timezone.utc)
    
    def can_trade(self) -> bool:
        """Check if user can perform trading operations"""
        return self.is_active and self.is_verified
    
    def add_balance(self, amount: float) -> None:
        """Add amount to user balance"""
        if amount < 0:
            raise ValueError("Amount must be positive")
        self.balance += amount
        self.update_timestamp()
    
    def subtract_balance(self, amount: float) -> None:
        """Subtract amount from user balance"""
        if amount < 0:
            raise ValueError("Amount must be positive")
        if self.balance < amount:
            raise ValueError("Insufficient balance")
        self.balance -= amount
        self.update_timestamp()


class UserCredentials(BaseModel):
    """User credentials entity - separate from user entity for security"""
    email: str
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
