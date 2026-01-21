import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

from app.main import app
from app.db.base import engine, get_session


@pytest.fixture(scope="session")
def client():
    # Crear tablas antes de los tests
    SQLModel.metadata.create_all(engine)

    with TestClient(app) as c:
        yield c

    # Limpiar después de todos los tests
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session():
    """Provide a database session for tests"""
    with Session(engine) as session:
        yield session
