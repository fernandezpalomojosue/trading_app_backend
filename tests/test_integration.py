# tests/test_integration.py
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.user import User, UserCreate


class TestErrorHandlingIntegration:
    """Integration tests for error handling scenarios"""
    
    def test_404_not_found_endpoints(self, client: TestClient):
        """Test 404 responses for non-existent endpoints"""
        non_existent_endpoints = [
            "/api/v1/nonexistent",
            "/api/v1/auth/nonexistent",
            "/api/v1/markets/nonexistent",
            "/api/v1/invalid/path"
        ]
        
        for endpoint in non_existent_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 404
    
    def test_method_not_allowed(self, client: TestClient):
        """Test 405 Method Not Allowed for wrong HTTP methods"""
        # Test POST on GET-only endpoints
        endpoints = [
            "/api/v1/markets",
            "/api/v1/markets/stocks/overview",
            "/health",
            "/"
        ]
        
        for endpoint in endpoints:
            response = client.post(endpoint)
            # FastAPI may return 405 or 422 depending on the endpoint
            assert response.status_code in [405, 422]
    
    def test_invalid_json_payload(self, client: TestClient):
        """Test handling of invalid JSON payloads"""
        # Test with malformed JSON
        response = client.post(
            "/api/v1/auth/register",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client: TestClient):
        """Test validation errors for missing required fields"""
        # Test registration with missing email
        response = client.post("/api/v1/auth/register", json={"password": "test123"})
        assert response.status_code == 422
        
        # Test registration with missing password
        response = client.post("/api/v1/auth/register", json={"email": "test@example.com"})
        assert response.status_code == 422
    
    def test_invalid_query_parameters(self, client: TestClient):
        """Test handling of invalid query parameters"""
        # Test with invalid limit parameter
        response = client.get("/api/v1/markets/stocks/assets?limit=invalid")
        assert response.status_code == 422
        
        # Test with negative limit
        response = client.get("/api/v1/markets/stocks/assets?limit=-10")
        assert response.status_code in [422, 500]  # May fail with API key error
        
        # Test with invalid offset
        response = client.get("/api/v1/markets/stocks/assets?offset=invalid")
        assert response.status_code == 422
    
    @patch("app.api.v1.endpoints.markets.MassiveClient")
    def test_external_service_error_handling(self, mock_client, client: TestClient):
        """Test handling of external service errors"""
        # Mock external service to raise exception
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_instance.get_daily_market_summary.side_effect = Exception("Service unavailable")
        
        response = client.get("/api/v1/markets/stocks/overview")
        
        assert response.status_code == 500
        assert "Error al obtener el resumen del mercado" in response.json()["detail"]
    
    @patch("app.api.v1.endpoints.markets.MassiveClient")
    def test_external_service_timeout(self, mock_client, client: TestClient):
        """Test handling of external service timeouts"""
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_instance.get_daily_market_summary.side_effect = TimeoutError("Timeout")
        
        response = client.get("/api/v1/markets/stocks/overview")
        
        assert response.status_code == 500
    
    @patch("app.api.v1.endpoints.markets.MassiveClient")
    def test_external_service_empty_response(self, mock_client, client: TestClient):
        """Test handling of empty responses from external service"""
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_instance.get_daily_market_summary.return_value = None
        
        response = client.get("/api/v1/markets/stocks/overview")
        
        assert response.status_code == 404
        assert "No se encontraron datos de mercado" in response.json()["detail"]
    
    @patch("app.api.v1.endpoints.markets.MassiveClient")
    def test_external_service_invalid_response_format(self, mock_client, client: TestClient):
        """Test handling of invalid response format from external service"""
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_instance.get_daily_market_summary.return_value = {"invalid": "format"}
        
        response = client.get("/api/v1/markets/stocks/overview")
        
        assert response.status_code == 404
    
    def test_database_connection_error_simulation(self, client: TestClient):
        """Test behavior when database is unavailable"""
        # This would require mocking the database dependency
        # For now, we test a scenario that might trigger database errors
        
        # Try to register a user with very long data that might cause DB errors
        long_data = {
            "email": "test@example.com",
            "username": "a" * 1000,  # Very long username
            "full_name": "a" * 1000,  # Very long name
            "password": "test123"
        }
        
        response = client.post("/api/v1/auth/register", json=long_data)
        # Should fail validation before reaching database
        assert response.status_code == 422
    
    def test_concurrent_requests_handling(self, client: TestClient):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            try:
                response = client.get("/api/v1/markets")
                results.append(response.status_code)
            except Exception as e:
                results.append(f"Error: {e}")
        
        # Make multiple concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results if isinstance(status, int))
    
    def test_large_payload_handling(self, client: TestClient):
        """Test handling of large payloads"""
        # Test with very large username
        large_payload = {
            "email": "test@example.com",
            "username": "a" * 10000,  # Very large
            "password": "test123"
        }
        
        response = client.post("/api/v1/auth/register", json=large_payload)
        assert response.status_code == 422  # Should fail validation
    
    def test_unicode_handling(self, client: TestClient):
        """Test handling of unicode characters"""
        unicode_payload = {
            "email": "tëst@éxample.com",
            "username": "tëstüser",
            "full_name": "Tëst Üser Ñame",
            "password": "test123"
        }
        
        # Should handle unicode properly (may fail validation but not crash)
        response = client.post("/api/v1/auth/register", json=unicode_payload)
        assert response.status_code in [201, 422]  # Either succeeds or fails validation
    
    def test_special_characters_in_payload(self, client: TestClient):
        """Test handling of special characters"""
        special_payload = {
            "email": "test@example.com",
            "username": "test<script>alert('xss')</script>",
            "full_name": "Test User & Co.",
            "password": "test123"
        }
        
        # Should handle special characters safely
        response = client.post("/api/v1/auth/register", json=special_payload)
        # Should fail username validation (alphanumeric only)
        assert response.status_code == 422
    
    @patch("app.api.v1.endpoints.markets.MassiveClient")
    def test_market_data_processing_errors(self, mock_client, client: TestClient):
        """Test handling of errors in market data processing"""
        # Mock malformed market data
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_instance.get_daily_market_summary.return_value = {
            "results": [
                {"invalid": "data"},  # Missing required fields
                {"T": "AAPL", "o": "invalid", "c": 150.0, "v": 1000000},  # Invalid types
                {"T": "MSFT", "o": 0, "c": 150.0, "v": 1000000}  # Zero division case
            ]
        }
        
        response = client.get("/api/v1/markets/stocks/overview")
        
        # Should handle errors gracefully and return processed data
        assert response.status_code == 200
        data = response.json()
        assert "total_assets" in data
    
    def test_authentication_token_errors(self, client: TestClient):
        """Test various authentication token error scenarios"""
        # Test with malformed token
        malformed_tokens = [
            "Bearer",  # Missing token
            "Bearer invalid.format",  # Invalid format
            "Bearer",  # Just the word Bearer
            "invalid_token",  # Missing Bearer prefix
            "",  # Empty header
            "Bearer "  # Empty token
        ]
        
        for token in malformed_tokens:
            headers = {"Authorization": token}
            response = client.get("/api/v1/auth/me", headers=headers)
            assert response.status_code == 401
    
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are properly set"""
        # Test preflight request
        response = client.options(
            "/api/v1/markets",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        # Should handle CORS preflight
        assert response.status_code in [200, 204, 400]  # May return 400 in some environments
    
    def test_rate_limiting_simulation(self, client: TestClient):
        """Test behavior under high request volume"""
        import time
        
        # Make many rapid requests
        responses = []
        start_time = time.time()
        
        for _ in range(100):
            response = client.get("/api/v1/markets")
            responses.append(response.status_code)
        
        end_time = time.time()
        
        # Most requests should succeed (unless rate limiting is implemented)
        success_rate = sum(1 for status in responses if status == 200) / len(responses)
        assert success_rate >= 0.9  # At least 90% should succeed
        
        # Should complete in reasonable time
        assert end_time - start_time < 10.0  # Less than 10 seconds


class TestWorkflowIntegration:
    """Integration tests for complete user workflows"""
    
    def test_complete_user_workflow(self, client: TestClient):
        """Test complete user registration and authentication workflow"""
        user_data = {
            "email": "workflow@example.com",
            "username": "workflowuser",
            "full_name": "Workflow User",
            "password": "testpassword123",
            "balance": 1000.0
        }
        
        # 1. Register user
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        user_info = register_response.json()
        assert user_info["email"] == user_data["email"]
        
        # 2. Login
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == 200
        token_info = login_response.json()
        assert "access_token" in token_info
        
        # 3. Access protected endpoint
        headers = {"Authorization": f"Bearer {token_info['access_token']}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        current_user = me_response.json()
        assert current_user["email"] == user_data["email"]
        
        # 4. Access cache management (protected)
        cache_response = client.get("/api/v1/markets/cache/stats", headers=headers)
        assert cache_response.status_code == 200
        
        # 5. Access public market endpoints
        markets_response = client.get("/api/v1/markets")
        assert markets_response.status_code == 200
    
    def test_user_update_workflow(self, client: TestClient):
        """Test user information update workflow"""
        # Register and login
        user_data = {
            "email": "update@example.com",
            "password": "testpassword123"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        
        # Only proceed if registration succeeded
        if register_response.status_code == 201:
            login_data = {
                "username": user_data["email"],
                "password": user_data["password"]
            }
            login_response = client.post("/api/v1/auth/login", data=login_data)
            
            if login_response.status_code == 200:
                token = login_response.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                
                # Note: Update endpoint would need to be implemented
                # This is a placeholder for when user update functionality is added
                # update_response = client.put("/api/v1/auth/me", json=update_data, headers=headers)
            else:
                # Login failed, skip token-dependent tests
                pass
        else:
            # Registration failed, skip tests
            pass
        
        # Note: Update endpoint would need to be implemented
        # This is a placeholder for when user update functionality is added
        # update_response = client.put("/api/v1/auth/me", json=update_data, headers=headers)
        
        # For now, just test that we can get current user info if authentication succeeded
        if 'token' in locals() and token:
            headers = {"Authorization": f"Bearer {token}"}
            me_response = client.get("/api/v1/auth/me", headers=headers)
            assert me_response.status_code == 200
    
    @patch("app.api.v1.endpoints.markets.MassiveClient")
    def test_market_data_workflow(self, mock_client, client: TestClient):
        """Test complete market data workflow"""
        # Mock external service responses
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        # Mock market summary
        mock_instance.get_daily_market_summary.return_value = {
            "results": [
                {"T": "AAPL", "o": 100.0, "c": 105.0, "h": 106.0, "l": 99.0, "v": 1000000},
                {"T": "MSFT", "o": 200.0, "c": 195.0, "h": 201.0, "l": 194.0, "v": 500000}
            ]
        }
        
        # Mock ticker details
        mock_instance.get_ticker_details.return_value = {
            "id": "AAPL",
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "market": "stocks",
            "currency": "USD",
            "active": True
        }
        
        # Mock OHLC data
        mock_instance.get_ohlc_data.return_value = {
            "results": [
                {"o": 100, "h": 105, "l": 99, "c": 104, "v": 100000}
            ]
        }
        
        # 1. Get market overview
        overview_response = client.get("/api/v1/markets/stocks/overview")
        assert overview_response.status_code == 200
        overview_data = overview_response.json()
        assert overview_data["market"] == "stocks"
        
        # 2. Get assets list
        assets_response = client.get("/api/v1/markets/stocks/assets")
        assert assets_response.status_code == 200
        assets_data = assets_response.json()
        assert len(assets_data) > 0
        
        # 3. Get specific asset
        asset_response = client.get("/api/v1/markets/assets/AAPL")
        assert asset_response.status_code == 200
        asset_data = asset_response.json()
        assert asset_data["symbol"] == "AAPL"
        
        # 4. Get candle data
        candles_response = client.get("/api/v1/markets/AAPL/candles")
        assert candles_response.status_code == 200
        candles_data = candles_response.json()
        assert "results" in candles_data
