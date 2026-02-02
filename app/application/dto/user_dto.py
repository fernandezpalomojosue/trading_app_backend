# app/application/dto/user_dto.py
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr


class UserRegistrationRequest(BaseModel):
    """DTO for user registration requests"""
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=8, max_length=100, description="Contraseña")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Nombre de usuario")
    full_name: Optional[str] = Field(None, max_length=100, description="Nombre completo")


class UserResponse(BaseModel):
    """DTO for user responses"""
    id: UUID
    email: str
    username: Optional[str]
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    is_superuser: bool
    balance: float
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """DTO for token responses"""
    access_token: str
    token_type: str = "bearer"
