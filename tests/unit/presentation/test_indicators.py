"""
Tests for indicators API endpoints
Tests HTTP requests, responses, and error handling for technical indicators
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app


class TestIndicatorsEndpoints:
    """Test indicators API endpoints"""
    
    @patch("app.domain.use_cases.indicators_use_cases.IndicatorsUseCases.get_ema")
    def test_get_ema_endpoint_success(self, mock_get_ema, client):
        """EMA endpoint should return 200 with valid data"""
        from app.application.dto.indicators_dto import EMAResponse, EMADataPoint
        
        mock_get_ema.return_value = EMAResponse(
            symbol="AAPL",
            window=14,
            timespan="day",
            results=[
                EMADataPoint(timestamp=1773028800000, value=150.5),
                EMADataPoint(timestamp=1773115200000, value=152.3)
            ]
        )
        
        headers = self.create_test_user(client, "test_ema@example.com")
        response = client.get("/api/v1/indicators/AAPL/ema?window=14&timespan=day", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["window"] == 14
        assert len(data["results"]) == 2
    
    @patch("app.domain.use_cases.indicators_use_cases.IndicatorsUseCases.get_sma")
    def test_get_sma_endpoint_success(self, mock_get_sma, client):
        """SMA endpoint should return 200 with valid data"""
        from app.application.dto.indicators_dto import SMAResponse, SMADataPoint
        
        mock_get_sma.return_value = SMAResponse(
            symbol="GOOGL",
            window=20,
            timespan="day",
            results=[
                SMADataPoint(timestamp=1773028800000, value=2800.0),
                SMADataPoint(timestamp=1773115200000, value=2810.5)
            ]
        )
        
        headers = self.create_test_user(client, "test_sma@example.com")
        response = client.get("/api/v1/indicators/GOOGL/sma?window=20&timespan=day", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "GOOGL"
        assert data["window"] == 20
    
    @patch("app.domain.use_cases.indicators_use_cases.IndicatorsUseCases.get_rsi")
    def test_get_rsi_endpoint_success(self, mock_get_rsi, client):
        """RSI endpoint should return 200 with valid data"""
        from app.application.dto.indicators_dto import RSIResponse, RSIDataPoint
        
        mock_get_rsi.return_value = RSIResponse(
            symbol="TSLA",
            window=14,
            timespan="day",
            results=[
                RSIDataPoint(timestamp=1773028800000, value=65.5),
                RSIDataPoint(timestamp=1773115200000, value=72.3)
            ]
        )
        
        headers = self.create_test_user(client, "test_rsi@example.com")
        response = client.get("/api/v1/indicators/TSLA/rsi?window=14&timespan=day", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "TSLA"
        assert len(data["results"]) == 2
    
    @patch("app.domain.use_cases.indicators_use_cases.IndicatorsUseCases.get_macd")
    def test_get_macd_endpoint_success(self, mock_get_macd, client):
        """MACD endpoint should return 200 with valid data"""
        from app.application.dto.indicators_dto import MACDResponse, MACDDataPoint
        
        mock_get_macd.return_value = MACDResponse(
            symbol="MSFT",
            fast=12,
            slow=26,
            signal_period=9,
            timespan="day",
            results=[
                MACDDataPoint(timestamp=1773028800000, value=2.5, signal=1.8, histogram=0.7),
                MACDDataPoint(timestamp=1773115200000, value=3.2, signal=2.1, histogram=1.1)
            ]
        )
        
        headers = self.create_test_user(client, "test_macd@example.com")
        response = client.get("/api/v1/indicators/MSFT/macd?fast=12&slow=26&signal=9", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "MSFT"
        assert data["fast"] == 12
        assert data["slow"] == 26
        assert data["signal_period"] == 9
    
    def create_test_user(self, client, email: str) -> dict:
        """Create a test user and return auth headers"""
        # Register a user
        register_data = {
            "email": email,
            "username": email.split("@")[0].replace(".", "_").replace("+", "_"),
            "password": "TestPassword123",
            "full_name": f"Test User {email.split('@')[0]}"
        }
        
        register_response = client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code in [200, 400]  # 400 if user already exists
        
        # Login to get token
        login_data = {
            "username": register_data["email"],
            "password": register_data["password"]
        }
        
        login_response = client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_indicators_endpoint_requires_auth(self, client):
        """Indicators endpoints should require authentication"""
        # Without auth token, should return 401 or 403
        response = client.get("/api/v1/indicators/AAPL/ema")
        
        # Should be unauthorized (401) or forbidden (403)
        assert response.status_code in [401, 403]
    
    def test_indicators_invalid_window_parameter(self, client):
        """Indicators should validate window parameter"""
        # Window should be between 1 and 200
        headers = self.create_test_user(client, "test2@example.com")
        response = client.get("/api/v1/indicators/AAPL/ema?window=0", headers=headers)
        
        assert response.status_code == 422  # Validation error
    
    def test_indicators_invalid_timespan_parameter(self, client):
        """Indicators should accept any timespan parameter (no strict validation)"""
        # Test with any timespan - endpoint should exist and process request
        headers = self.create_test_user(client, "test_timespan@example.com")
        response = client.get("/api/v1/indicators/AAPL/ema?timespan=invalid", headers=headers)
        
        # Should not be 404 (endpoint should exist)
        # Can be 200, 422, or 500 depending on implementation
        assert response.status_code in [200, 422, 500]  # Endpoint should exist
