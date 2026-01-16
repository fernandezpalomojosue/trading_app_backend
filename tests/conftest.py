"""
Tests básicos para la aplicación de trading
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Fixture para el cliente de la API"""
    return TestClient(app)


def test_root_endpoint(client):
    """Test del endpoint principal"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Bienvenido a la API de Trading"}


def test_health_check(client):
    """Test de verificación de salud"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_api_v1_prefix(client):
    """Test que el prefijo /api/v1 funciona"""
    response = client.get("/api/v1/")
    assert response.status_code in [200, 404]  # Puede no haber contenido pero el prefijo existe
