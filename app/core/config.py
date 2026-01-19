# app/core/config.py

from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class AppBaseSettings(BaseSettings):
    ENVIRONMENT: str = "development"
    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    CORS_ORIGINS: str = ""
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = True

    @property
    def cors_origins_list(self):
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o]

    @property
    def cors_allow_methods_list(self):
        return self.CORS_ALLOW_METHODS.split(",")

    @property
    def cors_allow_headers_list(self):
        return self.CORS_ALLOW_HEADERS.split(",")

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings():
    return AppBaseSettings()
