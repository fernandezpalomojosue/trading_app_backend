# tests/unit/use_cases/test_portfolio_use_cases.py
"""Unit tests for portfolio use cases"""
import pytest
import pytest_asyncio
from uuid import uuid4
from app.domain.use_cases.portfolio_use_cases import PortfolioUseCases
from tests.fixtures.portfolio_fixtures import (
    MockPortfolioRepository,
    sample_portfolio_holding,
    sample_portfolio_transaction,
    sample_holding_response,
    sample_transaction_response,
    sample_portfolio_summary_response
)


@pytest.fixture
def mock_portfolio_repository():
    """Mock portfolio repository for testing"""
    return MockPortfolioRepository()


class TestPortfolioUseCases:
    """Test portfolio use cases"""
    
    @pytest.fixture
    def portfolio_use_cases(self, mock_portfolio_repository):
        """Portfolio use cases fixture"""
        return PortfolioUseCases(mock_portfolio_repository)
    
    @pytest.mark.asyncio
    async def test_get_portfolio_summary_empty(self, portfolio_use_cases):
        """Test getting portfolio summary for user with no holdings"""
        user_id = uuid4()
        
        result = await portfolio_use_cases.get_portfolio_summary(user_id)
        
        # Verify it returns PortfolioSummaryResponse DTO
        assert result.user_id == user_id
        assert result.cash_balance == 10000.0  # Default balance
        assert result.total_holdings_value == 0.0
        assert result.total_portfolio_value == 10000.0
        assert result.total_unrealized_pnl == 0.0
        assert result.unrealized_pnl_percentage == 0.0
        assert result.holdings_count == 0
        assert result.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_get_holdings_empty(self, portfolio_use_cases):
        """Test getting holdings for user with no holdings"""
        user_id = uuid4()
        
        result = await portfolio_use_cases.get_holdings(user_id)
        
        # Verify it returns list of HoldingResponse DTOs
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_transactions_empty(self, portfolio_use_cases):
        """Test getting transactions for user with no transactions"""
        user_id = uuid4()
        
        result = await portfolio_use_cases.get_transactions(user_id)
        
        # Verify it returns list of TransactionResponse DTOs
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_buy_stock_success(self, portfolio_use_cases, mock_portfolio_repository):
        """Test successful stock purchase"""
        user_id = uuid4()
        mock_portfolio_repository.set_user_balance(2000.0)
        
        # Create request DTO
        from app.application.dto.portfolio_dto import BuyStockRequest
        request = BuyStockRequest(
            symbol="AAPL",
            quantity=10.0,
            price=150.0
        )
        
        result = await portfolio_use_cases.buy_stock(user_id=user_id, request=request)
        
        # Verify it returns TransactionResponse DTO
        assert result.symbol == "AAPL"
        assert result.transaction_type.value == "BUY"
        assert result.quantity == 10.0
        assert result.price == 150.0
        assert result.total_amount == 1500.0
        assert result.created_at is not None
        
        # Verify balance was updated
        new_balance = await mock_portfolio_repository.get_user_balance(user_id)
        assert new_balance == 500.0  # 2000 - 1500
    
    @pytest.mark.asyncio
    async def test_buy_stock_insufficient_balance(self, portfolio_use_cases, mock_portfolio_repository):
        """Test stock purchase with insufficient balance"""
        user_id = uuid4()
        mock_portfolio_repository.set_user_balance(1000.0)  # Less than needed
        
        # Create request DTO
        from app.application.dto.portfolio_dto import BuyStockRequest
        request = BuyStockRequest(
            symbol="AAPL",
            quantity=10.0,
            price=150.0
        )
        
        with pytest.raises(ValueError, match="Insufficient balance"):
            await portfolio_use_cases.buy_stock(user_id=user_id, request=request)  # Costs 1500 but only 1000 available
    
    @pytest.mark.asyncio
    async def test_sell_stock_no_holdings(self, portfolio_use_cases):
        """Test selling stock with no holdings"""
        user_id = uuid4()
        
        # Create request DTO
        from app.application.dto.portfolio_dto import SellStockRequest
        request = SellStockRequest(
            symbol="AAPL",
            quantity=5.0,
            price=155.0
        )
        
        with pytest.raises(ValueError, match="No holdings found for AAPL"):
            await portfolio_use_cases.sell_stock(user_id=user_id, request=request)
    
    @pytest.mark.asyncio
    async def test_sell_stock_insufficient_holdings(self, portfolio_use_cases, mock_portfolio_repository):
        """Test selling more shares than owned"""
        user_id = uuid4()
        
        # Add a holding with only 3 shares
        from app.domain.entities.portfolio import PortfolioHolding
        holding = PortfolioHolding(
            id=uuid4(),
            user_id=user_id,
            symbol="AAPL",
            quantity=3.0,
            average_price=150.0,
            current_price=155.0,
            total_value=465.0,
            unrealized_pnl=15.0,
            pnl_percentage=3.33
        )
        await mock_portfolio_repository.create_holding(holding)
        
        with pytest.raises(ValueError, match="Insufficient holdings"):
            # Create request DTO
            from app.application.dto.portfolio_dto import SellStockRequest
            request = SellStockRequest(
                symbol="AAPL",
                quantity=5.0,  # Trying to sell 5 but only have 3
                price=155.0
            )
            await portfolio_use_cases.sell_stock(user_id=user_id, request=request)
