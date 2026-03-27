# tests/integration/test_indicators_endpoint.py
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.application.dto.indicators_dto import CombinedIndicatorsResponse


class TestIndicatorsEndpoint:
    """Integration tests for indicators endpoint with DTO"""

    def test_endpoint_returns_valid_dto_structure(self, client: TestClient, authenticated_user):
        """Should return response matching CombinedIndicatorsResponse structure"""
        # Mock the indicators service to avoid external API calls
        mock_response = CombinedIndicatorsResponse(
            symbol="AAPL",
            results=[
                {
                    "t": 1704067200000,
                    "ema": 150.5,
                    "sma": 149.8,
                    "rsi": 65.4,
                    "macd": 1.2,
                    "signal": 0.8,
                    "histogram": 0.4,
                    "order_signal": None
                }
            ]
        )
        
        with patch("app.domain.use_cases.indicators_use_cases.IndicatorsUseCases.get_indicators") as mock_get_indicators:
            mock_get_indicators.return_value = mock_response.model_dump()
            
            response = client.get(
                "/api/v1/indicators/AAPL?window=14&fast=12&slow=26&signal=9&timespan=day",
                headers=authenticated_user['headers']
            )
            
            assert response.status_code == 200
            
            data = response.json()
            assert "symbol" in data
            assert "results" in data
            assert isinstance(data["results"], list)
            
            if len(data["results"]) > 0:
                result = data["results"][0]
                assert "t" in result
                assert "ema" in result
                assert "sma" in result
                assert "rsi" in result
                assert "macd" in result
                assert "signal" in result
                assert "histogram" in result
                assert "order_signal" in result

    def test_endpoint_requires_authentication(self, client: TestClient):
        """Should require authentication to access indicators"""
        response = client.get("/api/v1/indicators/AAPL")
        
        # Should fail without auth (401 or 403)
        assert response.status_code in [401, 403]

    def test_endpoint_validates_parameters(self, client: TestClient, authenticated_user):
        """Should validate indicator parameters"""
        # Test fast >= slow validation
        response = client.get(
            "/api/v1/indicators/AAPL?fast=30&slow=20",  # fast > slow
            headers=authenticated_user['headers']
        )
        
        assert response.status_code == 400
        assert "fast" in response.json().get("detail", "").lower()

    def test_endpoint_handles_empty_results(self, client: TestClient, authenticated_user):
        """Should handle empty results gracefully"""
        mock_response = CombinedIndicatorsResponse(
            symbol="AAPL",
            results=[]
        )
        
        with patch("app.domain.use_cases.indicators_use_cases.IndicatorsUseCases.get_indicators") as mock_get_indicators:
            mock_get_indicators.return_value = mock_response.model_dump()
            
            response = client.get(
                "/api/v1/indicators/AAPL",
                headers=authenticated_user['headers']
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["symbol"] == "AAPL"
            assert data["results"] == []

    def test_endpoint_respects_limit_parameter(self, client: TestClient, authenticated_user):
        """Should respect the limit parameter"""
        # Create 10 mock results
        mock_results = [
            {
                "t": 1704067200000 + i * 86400000,
                "ema": 150.0 + i,
                "sma": 149.0 + i,
                "rsi": 50.0 + i,
                "macd": 1.0 + i * 0.1,
                "signal": 0.5 + i * 0.1,
                "histogram": 0.5,
                "order_signal": None
            }
            for i in range(10)
        ]
        
        mock_response = CombinedIndicatorsResponse(
            symbol="AAPL",
            results=mock_results
        )
        
        with patch("app.domain.use_cases.indicators_use_cases.IndicatorsUseCases.get_indicators") as mock_get_indicators:
            mock_get_indicators.return_value = mock_response.model_dump()
            
            response = client.get(
                "/api/v1/indicators/AAPL?limit=5",
                headers=authenticated_user['headers']
            )
            
            assert response.status_code == 200
            data = response.json()
            # The endpoint should slice the results based on limit
            assert len(data["results"]) <= 5

    def test_endpoint_response_matches_dto_schema(self, client: TestClient, authenticated_user):
        """Should return data that validates against CombinedIndicatorsResponse"""
        mock_response = CombinedIndicatorsResponse(
            symbol="MSFT",
            results=[
                {
                    "t": 1704067200000,
                    "ema": 250.5,
                    "sma": 249.8,
                    "rsi": 55.4,
                    "macd": 2.1,
                    "signal": 1.5,
                    "histogram": 0.6,
                    "order_signal": "buy"
                }
            ]
        )
        
        with patch("app.domain.use_cases.indicators_use_cases.IndicatorsUseCases.get_indicators") as mock_get_indicators:
            mock_get_indicators.return_value = mock_response.model_dump()
            
            response = client.get(
                "/api/v1/indicators/MSFT",
                headers=authenticated_user['headers']
            )
            
            assert response.status_code == 200
            
            # Validate the response can be parsed as the DTO
            data = response.json()
            validated = CombinedIndicatorsResponse.model_validate(data)
            
            assert validated.symbol == "MSFT"
            assert len(validated.results) == 1
            assert validated.results[0].order_signal == "buy"
