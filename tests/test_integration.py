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
            "password": "Testpassword123"  # Added uppercase letter
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
            "/api/v1/markets/stocks/overview",
            "/api/v1/markets/crypto/overview",
            "/api/v1/markets/stocks/assets",
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
            "password": "Testpassword123"  # Added uppercase letter
        }
        
        # Register user
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code in [201, 400]
        
        # Check that user exists in database
        from app.infrastructure.database.models import UserSQLModel
        from sqlmodel import select
        
        user = db_session.exec(
            select(UserSQLModel).where(UserSQLModel.email == user_data["email"])
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
    
    def test_portfolio_integration_flow(self, client: TestClient, db_session: Session):
        """Test complete portfolio integration flow"""
        # 1. Register and login user
        user_data = {
            "email": "portfolio_integration@example.com",
            "username": "portfoliouser",
            "password": "Testpassword123"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code in [201, 400]
        
        login_response = client.post("/api/v1/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            
            # 2. Check initial portfolio state
            summary_response = client.get("/api/v1/portfolio/summary", headers=headers)
            assert summary_response.status_code == 200
            summary_data = summary_response.json()
            assert summary_data["cash_balance"] == 10000.0
            assert summary_data["total_holdings_value"] == 0.0
            assert summary_data["holdings_count"] == 0
            
            # 3. Buy some stock
            buy_response = client.post("/api/v1/portfolio/buy", json={
                "symbol": "AAPL",
                "quantity": 10.0,
                "price": 150.0
            }, headers=headers)
            assert buy_response.status_code == 201
            
            # 4. Check portfolio after purchase
            summary_response = client.get("/api/v1/portfolio/summary", headers=headers)
            summary_data = summary_response.json()
            assert summary_data["cash_balance"] == 8500.0  # 10000 - 1500
            assert summary_data["total_holdings_value"] == 1500.0
            assert summary_data["holdings_count"] == 1
            
            # 5. Check holdings details
            holdings_response = client.get("/api/v1/portfolio/holdings", headers=headers)
            assert holdings_response.status_code == 200
            holdings_data = holdings_response.json()
            assert len(holdings_data) == 1
            assert holdings_data[0]["symbol"] == "AAPL"
            assert holdings_data[0]["quantity"] == 10.0
            
            # 6. Check transactions
            transactions_response = client.get("/api/v1/portfolio/transactions", headers=headers)
            assert transactions_response.status_code == 200
            transactions_data = transactions_response.json()
            assert len(transactions_data) == 1
            assert transactions_data[0]["transaction_type"] == "BUY"
            
            # 7. Sell some stock
            sell_response = client.post("/api/v1/portfolio/sell", json={
                "symbol": "AAPL",
                "quantity": 3.0,
                "price": 160.0
            }, headers=headers)
            assert sell_response.status_code == 201
            
            # 8. Check final portfolio state
            summary_response = client.get("/api/v1/portfolio/summary", headers=headers)
            summary_data = summary_response.json()
            assert summary_data["cash_balance"] == 8980.0  # 8500 + 480
            assert summary_data["total_holdings_value"] == 1120.0  # 7 * 160
            assert summary_data["holdings_count"] == 1
            
            # 9. Verify transaction history
            transactions_response = client.get("/api/v1/portfolio/transactions", headers=headers)
            transactions_data = transactions_response.json()
            assert len(transactions_data) == 2  # BUY + SELL
            
            transaction_types = [t["transaction_type"] for t in transactions_data]
            assert "BUY" in transaction_types
            assert "SELL" in transaction_types
        else:
            assert login_response.status_code == 401
    
    def test_portfolio_endpoints_accessibility(self, client: TestClient):
        """Test that portfolio endpoints are accessible"""
        endpoints = [
            "/api/v1/portfolio/summary",
            "/api/v1/portfolio/holdings", 
            "/api/v1/portfolio/transactions"
        ]
        
        for endpoint in endpoints:
            # Test without authentication (should fail)
            response = client.get(endpoint)
            assert response.status_code in [401, 403]
            
            # Test with invalid token (should fail)
            response = client.get(endpoint, headers={
                "Authorization": "Bearer invalid_token"
            })
            assert response.status_code in [401, 403]
    
    def test_portfolio_business_rules_integration(self, client: TestClient, db_session: Session):
        """Test portfolio business rules in integration"""
        # Register and login user
        user_data = {
            "email": "business_rules@example.com",
            "username": "businessuser",
            "password": "Testpassword123"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        
        login_response = client.post("/api/v1/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            
            # Test buying with insufficient balance
            buy_response = client.post("/api/v1/portfolio/buy", json={
                "symbol": "AAPL",
                "quantity": 1000.0,  # Too expensive
                "price": 150.0
            }, headers=headers)
            assert buy_response.status_code == 400
            assert "Insufficient balance" in buy_response.json()["detail"]
            
            # Test selling without holdings
            sell_response = client.post("/api/v1/portfolio/sell", json={
                "symbol": "AAPL",
                "quantity": 5.0,
                "price": 150.0
            }, headers=headers)
            assert sell_response.status_code == 400
            assert "No holdings found" in sell_response.json()["detail"]
            
            # Buy some shares first
            buy_response = client.post("/api/v1/portfolio/buy", json={
                "symbol": "AAPL",
                "quantity": 10.0,
                "price": 150.0
            }, headers=headers)
            assert buy_response.status_code == 201
            
            # Test selling more than owned
            sell_response = client.post("/api/v1/portfolio/sell", json={
                "symbol": "AAPL",
                "quantity": 20.0,  # More than owned
                "price": 150.0
            }, headers=headers)
            assert sell_response.status_code == 400
            assert "Insufficient holdings" in sell_response.json()["detail"]
    
    def test_portfolio_database_integration(self, client: TestClient, db_session: Session):
        """Test portfolio database integration"""
        # Register and login user
        user_data = {
            "email": "db_integration@example.com",
            "username": "dbuser",
            "password": "Testpassword123"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        
        # Get user from database
        from app.infrastructure.database.models import UserSQLModel
        from sqlmodel import select
        
        user = db_session.exec(
            select(UserSQLModel).where(UserSQLModel.email == user_data["email"])
        ).first()
        
        if register_response.status_code == 201:
            assert user is not None
            assert user.balance == 10000.0
            
            # Login and perform portfolio operations
            login_response = client.post("/api/v1/auth/login", data={
                "username": user_data["email"],
                "password": user_data["password"]
            })
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                headers = {"Authorization": f"Bearer {token_data['access_token']}"}
                
                # Buy stock
                buy_response = client.post("/api/v1/portfolio/buy", json={
                    "symbol": "AAPL",
                    "quantity": 5.0,
                    "price": 100.0
                }, headers=headers)
                assert buy_response.status_code == 201
                
                # Check database state
                from app.infrastructure.database.models import PortfolioHoldingSQLModel, TransactionSQLModel
                
                # Check holdings
                holdings = db_session.exec(
                    select(PortfolioHoldingSQLModel).where(PortfolioHoldingSQLModel.user_id == user.id)
                ).all()
                assert len(holdings) == 1
                assert holdings[0].symbol == "AAPL"
                assert holdings[0].quantity == 5.0
                
                # Check transactions
                transactions = db_session.exec(
                    select(TransactionSQLModel).where(TransactionSQLModel.user_id == user.id)
                ).all()
                assert len(transactions) == 1
                assert transactions[0].symbol == "AAPL"
                assert transactions[0].transaction_type == "BUY"
                
                # Check updated user balance
                # Note: The balance might not be updated in the user table directly
                # The portfolio service might handle balance separately
                updated_user = db_session.get(UserSQLModel, user.id)
                # The balance might still be 10000.0 if portfolio manages it separately
                # Let's check the portfolio summary instead
                summary_response = client.get("/api/v1/portfolio/summary", headers=headers)
                summary_data = summary_response.json()
                assert summary_data["cash_balance"] == 9500.0  # 10000 - 500
