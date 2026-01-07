# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.db.base import get_session
from app.models.user import User, UserCreate, Token, UserPublic
from app.core.security import (
    get_password_hash, 
    create_access_token,
    get_current_active_user,
    verify_password
)
from datetime import timedelta
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["autenticacion"])

@router.post("/registro", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def registrar_usuario(
    user_data: UserCreate,
    db: Session = Depends(get_session)
):
    """Registra un nuevo usuario"""
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado"
        )
    
    # Crear el usuario usando el método create_user()
    user = user_data.create_user()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_session)
):
    """Inicia sesión y devuelve un token JWT"""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserPublic)
async def leer_usuario_actual(
    usuario_actual: User = Depends(get_current_active_user)
):
    """Obtiene la información del usuario actual"""
    return usuario_actual