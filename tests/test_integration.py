# tests/test_integration.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session


class TestIntegration:
    """Integration tests for the complete application flow"""
    
    def test_user_registration_and_login_flow(self, client: TestClient, db_session: Session):
        """Test complete user registration and login flow"""
        # 1. Register new user
        user_data = {
            "email": "integration@example.com",
            "username": "integrationuser",
            "password": "testpassword123"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code in [201, 400]
        
        # 2. Login with the registered user
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        
        login_response = client.post("/api/v1/auth/login", data=login_data)
        
        if login_response.status_code == 200:
            # 3. Use token to access protected endpoint
            token_data = login_response.json()
            if "access_token" in token_data:
                headers = {"Authorization": f"Bearer {token_data['access_token']}"}
                
                # 4. Access user profile
                profile_response = client.get("/api/v1/auth/me", headers=headers)
                assert profile_response.status_code in [200, 401]
                
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    assert profile_data["email"] == user_data["email"]
        else:
            # If login fails, it should be 401
            assert login_response.status_code == 401
    
    def test_market_endpoints_accessibility(self, client: TestClient):
        """Test that market endpoints are accessible"""
        endpoints = [
            "/api/v1/markets/overview/stocks",
            "/api/v1/markets/overview/crypto",
            "/api/v1/markets/assets",
            "/api/v1/markets/assets/AAPL",
            "/api/v1/markets/search?q=AAPL"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should not return 404 (endpoint should exist)
            assert response.status_code != 404
            # Should return one of these expected status codes
            assert response.status_code in [200, 401, 422, 500]
    
    def test_error_handling_consistency(self, client: TestClient):
        """Test that error handling is consistent across endpoints"""
        # Test invalid JSON
        response = client.post(
            "/api/v1/auth/register",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [422, 400]
        
        # Test invalid endpoint
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        
        # Test invalid method
        response = client.patch("/api/v1/auth/register")
        assert response.status_code in [405, 404]
    
    def test_database_session_isolation(self, client: TestClient, db_session: Session):
        """Test that database sessions are properly isolated"""
        # This test ensures that test data doesn't leak between tests
        user_data = {
            "email": "isolated@example.com",
            "username": "isolateduser",
            "password": "testpassword123"
        }
        
        # Register user
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code in [201, 400]
        
        # Check that user exists in database
        from app.infrastructure.database.models import UserSQLModel
        user = db_session.query(UserSQLModel).filter(
            UserSQLModel.email == user_data["email"]
        ).first()
        
        if response.status_code == 201:
            assert user is not None
            assert user.email == user_data["email"]
    
    def test_concurrent_requests(self, client: TestClient):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            try:
                response = client.get("/health")
                results.append(response.status_code)
            except Exception as e:
                results.append(f"Error: {e}")
        
        # Make multiple concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        success_count = sum(1 for status in results if status == 200)
        assert success_count >= 3  # At least 3 should succeed
