# app/infrastructure/security/auth_dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core.config import settings
from app.db.base import get_session
from app.domain.entities.user import UserEntity
from app.infrastructure.security.token_service import JWTTokenService
from app.infrastructure.database.repositories import SQLUserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user_dependency(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_session)
) -> UserEntity:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token
    token_service = JWTTokenService()
    email = token_service.verify_token(token)
    if not email:
        raise credentials_exception
    
    # Get user from database
    user_repository = SQLUserRepository(db)
    user = await user_repository.get_user_by_email(email)
    if not user:
        raise credentials_exception
    
    return user


# Alias for compatibility
get_current_active_user = get_current_user_dependency
