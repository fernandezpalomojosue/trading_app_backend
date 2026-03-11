# tests/test_portfolio.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from uuid import uuid4

from app.domain.entities.portfolio import PortfolioHolding, Transaction, TransactionType
from app.application.dto.portfolio_dto import BuyStockRequest, SellStockRequest


class TestPortfolioEndpoints:
    """Test portfolio endpoints"""
    
    def test_get_portfolio_summary_empty(self, client: TestClient, db_session: Session):
        """Test getting portfolio summary for new user (should be empty)"""
        # Create unique user for this test
        auth_headers = self.create_test_user(client, "test_summary_empty@example.com")
        
        response = client.get("/api/v1/portfolio/summary", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify initial state
        assert data["cash_balance"] == 10000.0  # Initial balance
        assert data["total_holdings_value"] == 0.0
        assert data["total_portfolio_value"] == 10000.0
        assert data["total_unrealized_pnl"] == 0.0
        assert data["unrealized_pnl_percentage"] == 0.0
        assert data["holdings_count"] == 0
    
    def test_get_holdings_empty(self, client: TestClient, db_session: Session):
        """Test getting holdings for new user (should be empty)"""
        # Create unique user for this test
        auth_headers = self.create_test_user(client, "test_holdings_empty@example.com")
        
        response = client.get("/api/v1/portfolio/holdings", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data == []  # Empty list
    
    def test_get_transactions_empty(self, client: TestClient, db_session: Session):
        """Test getting transactions for new user (should be empty)"""
        # Create unique user for this test
        auth_headers = self.create_test_user(client, "test_transactions_empty@example.com")
        
        response = client.get("/api/v1/portfolio/transactions", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data == []  # Empty list
    
    def test_buy_stock_success(self, client: TestClient, db_session: Session):
        """Test successful stock purchase"""
        # Create unique user for this test
        auth_headers = self.create_test_user(client, "test_buy_success@example.com")
        
        buy_request = {
            "symbol": "AAPL",
            "quantity": 10.0,
            "price": 150.0
        }
        
        response = client.post("/api/v1/portfolio/buy", json=buy_request, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify transaction details
        assert data["symbol"] == "AAPL"
        assert data["transaction_type"] == "BUY"
        assert data["quantity"] == 10.0
        assert data["price"] == 150.0
        assert data["total_amount"] == 1500.0
        
        # Verify portfolio summary updated
        summary_response = client.get("/api/v1/portfolio/summary", headers=auth_headers)
        summary_data = summary_response.json()
        assert summary_data["cash_balance"] == 8500.0  # 10000 - 1500
        assert summary_data["total_holdings_value"] == 1500.0
        assert summary_data["total_portfolio_value"] == 10000.0
        assert summary_data["holdings_count"] == 1
    
    def test_buy_stock_insufficient_balance(self, client: TestClient, db_session: Session):
        """Test buying stock with insufficient balance"""
        # Create unique user for this test
        auth_headers = self.create_test_user(client, "test_insufficient_balance@example.com")
        
        buy_request = {
            "symbol": "AAPL",
            "quantity": 100.0,  # Too many shares
            "price": 150.0
        }
        
        response = client.post("/api/v1/portfolio/buy", json=buy_request, headers=auth_headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "Insufficient balance" in data["detail"]
    
    def test_sell_stock_success(self, client: TestClient, db_session: Session):
        """Test successful stock sale (after buying first)"""
        # Create unique user for this test
        auth_headers = self.create_test_user(client, "test_sell_success@example.com")
        
        # First buy some stock
        buy_request = {
            "symbol": "AAPL",
            "quantity": 10.0,
            "price": 150.0
        }
        client.post("/api/v1/portfolio/buy", json=buy_request, headers=auth_headers)
        
        # Now sell some stock
        sell_request = {
            "symbol": "AAPL",
            "quantity": 5.0,
            "price": 160.0  # Higher price for profit
        }
        
        response = client.post("/api/v1/portfolio/sell", json=sell_request, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify transaction details
        assert data["symbol"] == "AAPL"
        assert data["transaction_type"] == "SELL"
        assert data["quantity"] == 5.0
        assert data["price"] == 160.0
        assert data["total_amount"] == 800.0
        
        # Verify portfolio summary updated
        summary_response = client.get("/api/v1/portfolio/summary", headers=auth_headers)
        summary_data = summary_response.json()
        assert summary_data["cash_balance"] == 9300.0  # 8500 + 800
        assert summary_data["total_holdings_value"] == 800.0  # 5 shares * 160
        assert summary_data["total_portfolio_value"] == 10100.0
        assert summary_data["total_unrealized_pnl"] == 50.0  # (800 - 750)
    
    def test_sell_stock_no_holdings(self, client: TestClient, db_session: Session):
        """Test selling stock without holdings"""
        # Create unique user for this test
        auth_headers = self.create_test_user(client, "test_no_holdings@example.com")
        
        sell_request = {
            "symbol": "AAPL",
            "quantity": 5.0,
            "price": 150.0
        }
        
        response = client.post("/api/v1/portfolio/sell", json=sell_request, headers=auth_headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "No holdings found" in data["detail"]
    
    def test_sell_stock_insufficient_holdings(self, client: TestClient, db_session: Session):
        """Test selling more shares than owned"""
        # Create unique user for this test
        auth_headers = self.create_test_user(client, "test_insufficient_holdings@example.com")
        
        # First buy some stock
        buy_request = {
            "symbol": "AAPL",
            "quantity": 5.0,
            "price": 150.0
        }
        client.post("/api/v1/portfolio/buy", json=buy_request, headers=auth_headers)
        
        # Try to sell more than owned
        sell_request = {
            "symbol": "AAPL",
            "quantity": 10.0,  # More than owned
            "price": 150.0
        }
        
        response = client.post("/api/v1/portfolio/sell", json=sell_request, headers=auth_headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "Insufficient holdings" in data["detail"]
    
    def create_test_user(self, client: TestClient, email: str) -> dict:
        """Create a test user and return auth headers"""
        # Register a user
        register_data = {
            "email": email,
            "username": email.split("@")[0].replace(".", "_").replace("+", "_"),
            "password": "TestPassword123",
            "full_name": f"Test User {email.split('@')[0]}"
        }
        
        register_response = client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code in [201, 400]  # 400 if user already exists
        
        # Login to get token
        login_data = {
            "username": register_data["email"],
            "password": register_data["password"]
        }
        
        login_response = client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
