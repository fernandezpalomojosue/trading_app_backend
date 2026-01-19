from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache
import os


# ==========================================================
# Base settings (común a todos los entornos)
# ==========================================================

class AppBaseSettings(BaseSettings):
    ENVIRONMENT: str = "development"

    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Trading App API"
    PROJECT_DESCRIPTION: str = "API para la aplicación de trading"
    PROJECT_VERSION: str = "0.1.0"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"

    # API Keys
    POLYGON_API_KEY: Optional[str] = None

    # DB (se define por entorno)
    DATABASE_URL: str

    # Debug flags
    DEBUG: bool = False
    RELOAD: bool = False
    ECHO_SQL: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# ==========================================================
# Development settings (Postgres local)
# ==========================================================

class DevelopmentSettings(AppBaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

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
    DATABASE_URL: str = "sqlite:///./test.db"

    DEBUG: bool = True
    ECHO_SQL: bool = False


# ==========================================================
# Production settings (Render / cloud)
# ==========================================================

class ProductionSettings(AppBaseSettings):
    # DATABASE_URL viene DIRECTA del provider (Render)
    DEBUG: bool = False
    RELOAD: bool = False
    ECHO_SQL: bool = False


# ==========================================================
# Settings factory
# ==========================================================

@lru_cache
def get_settings():
    env = os.getenv("ENVIRONMENT", "development").lower()

    if env == "testing":
        return TestingSettings()

    if env == "production":
        return ProductionSettings()

    return DevelopmentSettings()


# ==========================================================
# Public settings instance
# ==========================================================

settings = get_settings()
