# app/infrastructure/security/token_service.py
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt

from app.core.config import settings
from app.domain.use_cases.user_use_cases import TokenService


class JWTTokenService(TokenService):
    """JWT token service implementation"""
    
    def __init__(self, secret_key: str = None, algorithm: str = None, expire_minutes: int = None):
        self.secret_key = secret_key or settings.SECRET_KEY
        self.algorithm = algorithm or settings.ALGORITHM
        self.expire_minutes = expire_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    def create_access_token(self, data: dict) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.expire_minutes)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify a JWT token and return the subject"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("sub")
            if not email:
                return None
            return email
        except JWTError:
            return None
