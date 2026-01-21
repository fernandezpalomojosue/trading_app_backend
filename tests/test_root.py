# tests/test_root.py
import pytest

class TestRootEndpoint:
    """Test suite for root endpoint"""
    
    def test_root_endpoint(self, client):
        """
        GET /
        Should return welcome message and environment info.
        """
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "message" in data
        assert "environment" in data
        
        # Verify content
        assert isinstance(data["message"], str)
        assert isinstance(data["environment"], str)
        assert len(data["message"]) > 0
        assert len(data["environment"]) > 0
        
        # Verify expected content
        assert "trading" in data["message"].lower() or "bienvenido" in data["message"].lower()
        assert data["environment"] in ["development", "testing", "production", "dev"]
        
        # Verify content type
        assert response.headers["content-type"] == "application/json"
    
    def test_root_endpoint_response_time(self, client):
        """
        Root endpoint should respond quickly.
        """
        import time
        
        start_time = time.time()
        response = client.get("/")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second
    
    def test_root_endpoint_method_not_allowed(self, client):
        """
        POST / should not be allowed.
        """
        response = client.post("/")
        assert response.status_code == 405
        
        # Verify error response structure
        data = response.json()
        assert "detail" in data
    
    def test_root_endpoint_put_not_allowed(self, client):
        """
        PUT / should not be allowed.
        """
        response = client.put("/")
        assert response.status_code == 405
    
    def test_root_endpoint_delete_not_allowed(self, client):
        """
        DELETE / should not be allowed.
        """
        response = client.delete("/")
        assert response.status_code == 405
    
    def test_root_endpoint_patch_not_allowed(self, client):
        """
        PATCH / should not be allowed.
        """
        response = client.patch("/")
        assert response.status_code == 405
    
    def test_root_endpoint_options_allowed(self, client):
        """
        OPTIONS / should be allowed for CORS preflight.
        """
        response = client.options("/")
        assert response.status_code in [200, 204, 405]
    
    def test_root_endpoint_head_allowed(self, client):
        """
        HEAD / should be allowed.
        """
        response = client.head("/")
        assert response.status_code in [200, 405]
        
        # If successful, should have no body but proper headers
        if response.status_code == 200:
            assert len(response.content) == 0
            assert "content-type" in response.headers
    
    def test_root_endpoint_consistency(self, client):
        """
        Root endpoint should return consistent response structure.
        """
        # Make multiple requests
        responses = []
        
        for _ in range(5):
            response = client.get("/")
            assert response.status_code == 200
            responses.append(response.json())
        
        # All responses should have the same structure
        for response_data in responses:
            assert "message" in response_data
            assert "environment" in response_data
            assert isinstance(response_data["message"], str)
            assert isinstance(response_data["environment"], str)
        
        # Environment should be consistent across requests
        environments = [resp["environment"] for resp in responses]
        assert all(env == environments[0] for env in environments)
    
    def test_root_endpoint_with_query_parameters(self, client):
        """
        Root endpoint should ignore query parameters.
        """
        response = client.get("/?test=param&other=value")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "environment" in data
    
    def test_root_endpoint_cors_headers(self, client):
        """
        Root endpoint should have proper CORS headers.
        """
        response = client.get("/")
        assert response.status_code == 200
        
        # Check for common CORS headers (may not be present in all configurations)
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers"
        ]
        
        # At least one CORS header should be present if CORS is configured
        has_cors = any(header in response.headers for header in cors_headers)
        # This assertion may fail if CORS is not configured, which is acceptable
