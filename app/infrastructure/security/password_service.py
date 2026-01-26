# app/infrastructure/security/password_service.py
from passlib.context import CryptContext

from app.domain.use_cases.user_use_cases import PasswordService


class PasslibPasswordService(PasswordService):
    """Password service implementation using passlib"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
