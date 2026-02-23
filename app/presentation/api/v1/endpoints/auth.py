# app/presentation/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.db.base import get_session
from app.application.dto.user_dto import UserRegistrationRequest, UserResponse, TokenResponse
from app.application.services.user_service import UserService
from app.domain.use_cases.user_use_cases import UserUseCases, UserRepository
from app.infrastructure.database.repositories import SQLUserRepository
from app.infrastructure.security.password_service import PasslibPasswordService
from app.infrastructure.security.token_service import JWTTokenService
from app.infrastructure.security.auth_dependencies import get_current_user_dependency

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_user_service(db: Session = Depends(get_session)) -> UserService:
    """Dependency to get user service"""
    user_repository = SQLUserRepository(db)
    password_service = PasslibPasswordService()
    token_service = JWTTokenService()
    user_use_cases = UserUseCases(user_repository, password_service, token_service)
    return UserService(user_use_cases)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegistrationRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Register a new user"""
    try:
        return await user_service.register_user(
            email=user_data.email,
            password=user_data.password,
            username=user_data.username,
            full_name=user_data.full_name
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service)
):
    """Login and return access token"""
    token = await user_service.authenticate_user(form_data.username, form_data.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return TokenResponse(access_token=token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user = Depends(get_current_user_dependency),
    user_service: UserService = Depends(get_user_service)
):
    """Get current user profile"""
    user_response = await user_service.get_user_profile_response(current_user.id)
    if not user_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user_response
