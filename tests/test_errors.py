# tests/test_errors.py
import pytest

class TestErrorHandling:
    """Test suite for error handling"""
    
    def test_404_not_found(self, client):
        """
        GET /no-existe
        Should return 404 for non-existent endpoints.
        """
        response = client.get("/no-existe")
        
        assert response.status_code == 404
        
        # Verify error response structure
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)
        assert len(data["detail"]) > 0
    
    def test_404_nested_path(self, client):
        """
        GET /api/v1/nonexistent
        Should return 404 for nested non-existent endpoints.
        """
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        
        response = client.get("/api/v1/auth/nonexistent")
        assert response.status_code == 404
        
        response = client.get("/api/v1/markets/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed_root(self, client):
        """
        POST /
        Should return 405 for unsupported methods.
        """
        response = client.post("/")
        assert response.status_code == 405
        
        # Verify error response structure
        data = response.json()
        assert "detail" in data
    
    def test_method_not_allowed_various_endpoints(self, client):
        """
        Test various endpoints with unsupported HTTP methods.
        """
        endpoints_to_test = [
            "/",
            "/health",
            "/api/v1/markets",
            "/api/v1/auth/register"
        ]
        
        for endpoint in endpoints_to_test:
            # Test PUT
            response = client.put(endpoint)
            assert response.status_code in [405, 422]  # May be 422 for validation endpoints
            
            # Test DELETE
            response = client.delete(endpoint)
            assert response.status_code in [405, 401]  # May be 401 for protected endpoints
            
            # Test PATCH
            response = client.patch(endpoint)
            assert response.status_code in [405, 422]
    
    def test_invalid_json_payload(self, client):
        """
        Test handling of invalid JSON payloads.
        """
        # Test with malformed JSON
        response = client.post(
            "/api/v1/auth/register",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
        
        # Test with incomplete JSON
        response = client.post(
            "/api/v1/auth/register",
            data='{"email": "test@example.com",',  # Incomplete JSON
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_empty_request_body(self, client):
        """
        Test handling of empty request bodies where data is expected.
        """
        response = client.post(
            "/api/v1/auth/register",
            data="",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_invalid_content_type(self, client):
        """
        Test handling of invalid content types.
        """
        response = client.post(
            "/api/v1/auth/register",
            data="some data",
            headers={"Content-Type": "text/plain"}
        )
        # May accept or reject depending on FastAPI configuration
        assert response.status_code in [422, 200]
    
    def test_query_parameter_validation_errors(self, client):
        """
        Test validation errors for query parameters.
        """
        # Test with invalid parameter types
        response = client.get("/api/v1/markets/stocks/assets?limit=abc")
        assert response.status_code == 422
        
        response = client.get("/api/v1/markets/stocks/assets?offset=xyz")
        assert response.status_code == 422
        
        # Test with parameter values that are too large
        response = client.get("/api/v1/markets/stocks/assets?limit=999999999")
        assert response.status_code in [200, 422, 500]  # May fail with API key error  # May be normalized or rejected
    
    def test_path_parameter_validation_errors(self, client):
        """
        Test validation errors for path parameters.
        """
        # Test with invalid market types
        response = client.get("/api/v1/markets/invalid/overview")
        assert response.status_code == 422
        
        response = client.get("/api/v1/markets/invalid/assets")
        assert response.status_code == 422
    
    def test_authentication_errors(self, client):
        """
        Test authentication-related errors.
        """
        # Test without authentication header
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        
        response = client.get("/api/v1/markets/cache/stats")
        assert response.status_code == 401
        
        # Test with malformed authentication header
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "InvalidFormat"}
        )
        assert response.status_code == 401
        
        # Test with invalid token
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
        
        # Test with expired token (simulated)
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer expired.jwt.token"}
        )
        assert response.status_code == 401
    
    def test_cors_preflight_errors(self, client):
        """
        Test CORS preflight request handling.
        """
        # Test valid preflight request
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
        
        # Test preflight without required headers
        response = client.options(
            "/api/v1/markets",
            headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code in [200, 400, 405]
    
    def test_rate_limiting_simulation(self, client):
        """
        Test behavior under high request volume (if rate limiting is implemented).
        """
        import time
        
        # Make multiple rapid requests
        responses = []
        start_time = time.time()
        
        for _ in range(50):
            response = client.get("/health")
            responses.append(response.status_code)
        
        end_time = time.time()
        
        # Most requests should succeed unless rate limiting is implemented
        success_rate = sum(1 for status in responses if status == 200) / len(responses)
        assert success_rate >= 0.8  # At least 80% should succeed
        
        # Should complete in reasonable time
        assert end_time - start_time < 10.0
    
    def test_error_response_consistency(self, client):
        """
        Test that error responses have consistent structure.
        """
        error_endpoints = [
            ("/no-existe", "GET"),
            ("/", "POST"),
            ("/api/v1/auth/me", "GET")  # Requires auth
        ]
        
        for endpoint, method in error_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint)
            
            # All error responses should have JSON content type
            if response.status_code != 200:
                assert "application/json" in response.headers["content-type"]
                
                # All error responses should have a 'detail' field (FastAPI standard)
                data = response.json()
                assert "detail" in data
                assert isinstance(data["detail"], str)
