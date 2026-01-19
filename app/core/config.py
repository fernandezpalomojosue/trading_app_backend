from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache
import os


# ==========================================================
# Base settings (común a todos los entornos)
# ==========================================================

class AppBaseSettings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "development"

    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Trading App API"
    PROJECT_DESCRIPTION: str = "API para la aplicación de trading"
    PROJECT_VERSION: str = "0.1.0"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 día

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"
    
    @property
    def cors_allow_methods_list(self) -> List[str]:
        return [method.strip() for method in self.CORS_ALLOW_METHODS.split(",")]
    
    @property
    def cors_allow_headers_list(self) -> List[str]:
        return [header.strip() for header in self.CORS_ALLOW_HEADERS.split(",")]

    # API Keys
    POLYGON_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = "utf-8"
        extra = "ignore"  # Permitir campos extra en .env


# ==========================================================
# Development settings (Postgres)
# ==========================================================

class DevelopmentSettings(AppBaseSettings):
    # Database (Postgres)
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Debug
    DEBUG: bool = True
    RELOAD: bool = True
    ECHO_SQL: bool = True

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


# ==========================================================
# Testing settings (SQLite)
# ==========================================================

class TestingSettings(AppBaseSettings):
    # Database (SQLite)
    DATABASE_URL: str = "sqlite:///./test.db"

    # Debug
    DEBUG: bool = True
    RELOAD: bool = False
    ECHO_SQL: bool = False


# ==========================================================
# Settings factory
# ==========================================================

@lru_cache
def get_settings():
    environment = os.getenv("ENVIRONMENT", "development")

    if environment == "testing":
        return TestingSettings()

    return DevelopmentSettings()


# ==========================================================
# Public settings instance
# ==========================================================

settings = get_settings()
