# app/db/__init__.py
from .base import SQLModel, engine, get_session, create_db_and_tables
from app.infrastructure.database.models import UserSQLModel