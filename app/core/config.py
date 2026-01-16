from pydantic_settings import BaseSettings
from typing import Optional, List
import os

# Detect if we're in testing mode
IS_TESTING = os.getenv("PYTEST_CURRENT_TEST") is not None

class BaseSettings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Trading App API"
    PROJECT_DESCRIPTION: str = "API para la aplicación de trading"
    PROJECT_VERSION: str = "0.1.0"
    
    # Database
    ECHO_SQL: bool = False
    
    # Database Connection
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    
    @property
    def DATABASE_URL(self) -> str:
        if IS_TESTING:
            return self.TEST_DATABASE_URL or "sqlite:///./test.db"
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Test Database (fallback to SQLite if not provided)
    TEST_DATABASE_URL: Optional[str] = None
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 1 día
    
    # API Keys
    POLYGON_API_KEY: Optional[str] = None
    
    # CORS Settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Environment
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'

class DevelopmentSettings(BaseSettings):
    DEBUG: bool = True
    RELOAD: bool = True
    ECHO_SQL: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'

class TestingSettings(BaseSettings):
    DEBUG: bool = True
    RELOAD: bool = False
    ECHO_SQL: bool = False
    TEST_DATABASE_URL: Optional[str] = None  # Will use SQLite fallback if not provided
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'

def get_settings():
    if IS_TESTING:
        return TestingSettings()
    else:
        return DevelopmentSettings()

# Crear instancia de configuración
settings = get_settings()
