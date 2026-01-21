# app/models/user.py
import re
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from pydantic import EmailStr, validator, Field as PydanticField
from passlib.context import CryptContext

# Configuración para el hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserBase(SQLModel):
    """Modelo base para usuarios"""
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
    
    @validator('email')
    def validate_email(cls, v):
        # Regex más robusta basada en RFC 5322 simplificada
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError("Formato de email inválido")
        return v.lower()  # Normalizar a minúsculas
    @validator('username')
    def username_must_be_alphanumeric(cls, v):
        if v is not None and not v.isalnum():
            raise ValueError('El nombre de usuario solo puede contener letras y números')
        return v

class User(UserBase, table=True):
    """Modelo de usuario para la base de datos"""
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True, unique=True),
        description="ID único del usuario (UUID nativo)"
    )
    hashed_password: str = Field(
        ..., 
        min_length=8, 
        description="Contraseña hasheada"
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
        # Índice compuesto para búsquedas por email/username
        {'sqlite_autoincrement': False},
    )
    # Relaciones
    # tokens: List["Token"] = Relationship(back_populates="user")

    def verify_password(self, password: str) -> bool:
        """Verifica si la contraseña coincide con el hash almacenado"""
        return pwd_context.verify(password, self.hashed_password)

class UserCreate(UserBase):
    """Modelo para la creación de usuarios"""
    password: str = Field(..., min_length=8, max_length=100, 
                         description="Contraseña en texto plano")
    
    def create_user(self) -> 'User':
        """Crea y retorna un nuevo objeto User con la contraseña hasheada"""
        hashed_password = pwd_context.hash(self.password)
        user_data = self.model_dump(
            exclude={"password"},
            exclude_unset=True,
            exclude_none=True
        )
        return User(
            **user_data,
            hashed_password=hashed_password,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            id=uuid.uuid4()  # UUID nativo
        )

class UserUpdate(SQLModel):
    """Modelo para actualización de usuarios"""
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    balance: Optional[float] = None

class UserPublic(UserBase):
    """Modelo para respuesta pública de usuarios"""
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

# Modelo para autenticación
class Token(SQLModel):
    """Modelo para tokens de autenticación"""
    access_token: str
    token_type: str = "bearer"

class TokenData(SQLModel):
    """Modelo para datos del token"""
    username: Optional[str] = None

# Actualizar las referencias circulares si es necesario
# Token.update_forward_refs(User=User)  # Descomentar cuando se implemente el modelo Token
