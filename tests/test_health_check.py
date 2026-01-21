# tests/test_health_check.py
import pytest

class TestHealthCheck:
    """Test suite for health check endpoints"""
    
    def test_health_check(self, client):
        """
        GET /health
        Should return health status.
        """
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "status" in data
        assert data["status"] == "ok"
        
        # Verify content type
        assert response.headers["content-type"] == "application/json"
    
    def test_health_check_response_time(self, client):
        """
        Health check should respond quickly.
        """
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second
    
    def test_health_check_method_not_allowed(self, client):
        """
        POST /health should not be allowed.
        """
        response = client.post("/health")
        assert response.status_code == 405
    
    def test_health_check_put_not_allowed(self, client):
        """
        PUT /health should not be allowed.
        """
        response = client.put("/health")
        assert response.status_code == 405
    
    def test_health_check_delete_not_allowed(self, client):
        """
        DELETE /health should not be allowed.
        """
        response = client.delete("/health")
        assert response.status_code == 405
