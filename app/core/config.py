from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Trading App"
    DEBUG: bool = True
    
    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    RELOAD: bool = True
    
    # Database
    POSTGRES_USER: str = "leo"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    TEST_DATABASE_URL: str = "postgresql://postgres:postgres@localhost/test_trading_app"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Cambia esto en producción
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 1 día
    
    # API Keys
    POLYGON_API_KEY: Optional[str] = None  # Will be loaded from .env
    
    # Environment
    ENVIRONMENT: str = "development"  # 'development', 'testing', 'production'
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'

# Crear instancia de configuración
settings = Settings()
