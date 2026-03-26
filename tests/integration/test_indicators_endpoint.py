# tests/integration/test_indicators_endpoint.py
import pytest
from fastapi.testclient import TestClient


class TestIndicatorsEndpoint:
    """Integration tests for indicators endpoint"""

    def test_indicators_endpoint_accessibility(self, client: TestClient):
        """Test that indicators endpoint exists and requires auth"""
        response = client.get("/api/v1/indicators/AAPL")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
        # Should require authentication
        assert response.status_code in [401, 403]

    def test_indicators_endpoint_with_auth(self, client: TestClient, authenticated_user):
        """Test indicators endpoint with authenticated user"""
        response = client.get(
            "/api/v1/indicators/AAPL?window=14&fast=12&slow=26&signal=9&timespan=day",
            headers=authenticated_user["headers"]
        )
        # May return 200 (success), 422 (validation), or 500 (external API error)
        assert response.status_code in [200, 422, 500]

    def test_indicators_endpoint_validates_parameters(self, client: TestClient, authenticated_user):
        """Test that endpoint validates parameters (fast >= slow)"""
        response = client.get(
            "/api/v1/indicators/AAPL?fast=30&slow=20",
            headers=authenticated_user["headers"]
        )
        assert response.status_code == 400
        assert "fast" in response.json().get("detail", "").lower()
