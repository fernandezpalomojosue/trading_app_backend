"""
Portfolio-specific fixtures for testing
Provides reusable test data and mock implementations for portfolio functionality
"""
import pytest
from datetime import datetime, timezone
from typing import List, Dict, Any
from unittest.mock import Mock

from app.domain.entities.portfolio import PortfolioHolding, Transaction, TransactionType, Portfolio
from app.application.dto.portfolio_dto import BuyStockRequest, SellStockRequest, PortfolioSummaryResponse, HoldingResponse, TransactionResponse
from app.domain.use_cases.portfolio_use_cases import PortfolioRepository


class MockPortfolioRepository(PortfolioRepository):
    """Mock portfolio repository for testing"""
    
    def __init__(self):
        self.data = {}
        self.call_count = {}
        self.call_history = []
        self.user_balance = 10000.0  # Default balance
    
    async def get_user_holdings(self, user_id):
        self._record_call('get_user_holdings', user_id=user_id)
        return self.data.get(f'holdings_{user_id}', [])
    
    async def get_user_transactions(self, user_id):
        self._record_call('get_user_transactions', user_id=user_id)
        return self.data.get(f'transactions_{user_id}', [])
    
    async def get_holding_by_symbol(self, user_id, symbol):
        self._record_call('get_holding_by_symbol', user_id=user_id, symbol=symbol)
        holdings = self.data.get(f'holdings_{user_id}', [])
        for holding in holdings:
            if holding.symbol == symbol:
                return holding
        return None
    
    async def create_holding(self, holding):
        self._record_call('create_holding', holding=holding)
        user_holdings = self.data.get(f'holdings_{holding.user_id}', [])
        user_holdings.append(holding)
        self.data[f'holdings_{holding.user_id}'] = user_holdings
        return holding
    
    async def update_holding(self, holding):
        self._record_call('update_holding', holding=holding)
        holdings = self.data.get(f'holdings_{holding.user_id}', [])
        for i, h in enumerate(holdings):
            if h.id == holding.id:
                holdings[i] = holding
                break
        self.data[f'holdings_{holding.user_id}'] = holdings
        return holding
    
    async def delete_holding(self, holding_id):
        self._record_call('delete_holding', holding_id=holding_id)
        # Find and delete holding
        for user_key in list(self.data.keys()):
            if user_key.startswith('holdings_'):
                holdings = self.data[user_key]
                self.data[user_key] = [h for h in holdings if h.id != holding_id]
        return True

    async def is_a_holding(self, symbol):
        self._record_call('is_a_holding', symbol=symbol)
        # Check if any holding has this symbol
        for user_key in list(self.data.keys()):
            if user_key.startswith('holdings_'):
                holdings = self.data[user_key]
                for holding in holdings:
                    if holding.symbol == symbol:
                        return True
        return False
    
    async def create_transaction(self, transaction):
        self._record_call('create_transaction', transaction=transaction)
        user_transactions = self.data.get(f'transactions_{transaction.user_id}', [])
        user_transactions.append(transaction)
        self.data[f'transactions_{transaction.user_id}'] = user_transactions
        return transaction
    
    async def update_user_balance(self, user_id, new_balance):
        self._record_call('update_user_balance', user_id=user_id, new_balance=new_balance)
        self.user_balance = new_balance
        return True
    
    async def get_user_balance(self, user_id):
        self._record_call('get_user_balance', user_id=user_id)
        return self.user_balance
    
    def _record_call(self, method: str, **kwargs):
        """Record method calls for testing"""
        self.call_count[method] = self.call_count.get(method, 0) + 1
        self.call_history.append({
            'method': method,
            'kwargs': kwargs,
            'timestamp': datetime.now(timezone.utc)
        })
    
    def reset_call_tracking(self):
        """Reset call tracking for clean test state"""
        self.call_count.clear()
        self.call_history.clear()
    
    def set_user_balance(self, balance: float):
        """Set user balance for testing"""
        self.user_balance = balance


@pytest.fixture
def mock_portfolio_repository():
    """Mock portfolio repository for testing"""
    return MockPortfolioRepository()


@pytest.fixture
def sample_portfolio_holding():
    """Sample portfolio holding for testing"""
    import uuid
    
    return PortfolioHolding(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        symbol="AAPL",
        quantity=10.0,
        average_price=150.0,
        current_price=155.0,
        total_value=1550.0,
        unrealized_pnl=50.0,
        pnl_percentage=3.33,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_portfolio_transaction():
    """Sample portfolio transaction for testing"""
    import uuid
    
    return Transaction(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        symbol="AAPL",
        transaction_type=TransactionType.BUY,
        quantity=10.0,
        price=150.0,
        total_amount=1500.0,
        created_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_buy_request():
    """Sample buy request for testing"""
    return BuyStockRequest(
        symbol="AAPL",
        quantity=10.0,
        price=150.0
    )


@pytest.fixture
def sample_sell_request():
    """Sample sell request for testing"""
    return SellStockRequest(
        symbol="AAPL",
        quantity=5.0,
        price=155.0
    )


@pytest.fixture
def sample_holding_response():
    """Sample holding response DTO for testing"""
    import uuid
    
    return HoldingResponse(
        id=uuid.uuid4(),
        symbol="AAPL",
        quantity=10.0,
        average_price=150.0,
        current_price=155.0,
        total_value=1550.0,
        unrealized_pnl=50.0,
        pnl_percentage=3.33,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_transaction_response():
    """Sample transaction response DTO for testing"""
    import uuid
    
    return TransactionResponse(
        id=uuid.uuid4(),
        symbol="AAPL",
        transaction_type=TransactionType.BUY,
        quantity=10.0,
        price=150.0,
        total_amount=1500.0,
        created_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_portfolio_summary_response():
    """Sample portfolio summary response DTO for testing"""
    import uuid
    
    user_id = uuid.uuid4()
    
    return PortfolioSummaryResponse(
        user_id=user_id,
        cash_balance=7500.0,
        total_holdings_value=2525.0,
        total_portfolio_value=10025.0,
        total_unrealized_pnl=25.0,
        unrealized_pnl_percentage=0.99,
        holdings_count=2,
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def portfolio_test_data():
    """Complete portfolio test data set"""
    import uuid
    
    user_id = uuid.uuid4()
    
    holdings = [
        PortfolioHolding(
            id=uuid.uuid4(),
            user_id=user_id,
            symbol="AAPL",
            quantity=10.0,
            average_price=150.0,
            current_price=155.0,
            total_value=1550.0,
            unrealized_pnl=50.0,
            pnl_percentage=3.33,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        PortfolioHolding(
            id=uuid.uuid4(),
            user_id=user_id,
            symbol="GOOGL",
            quantity=5.0,
            average_price=200.0,
            current_price=195.0,
            total_value=975.0,
            unrealized_pnl=-25.0,
            pnl_percentage=-2.5,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    ]
    
    transactions = [
        Transaction(
            id=uuid.uuid4(),
            user_id=user_id,
            symbol="AAPL",
            transaction_type=TransactionType.BUY,
            quantity=10.0,
            price=150.0,
            total_amount=1500.0,
            created_at=datetime.now(timezone.utc)
        ),
        Transaction(
            id=uuid.uuid4(),
            user_id=user_id,
            symbol="GOOGL",
            transaction_type=TransactionType.BUY,
            quantity=5.0,
            price=200.0,
            total_amount=1000.0,
            created_at=datetime.now(timezone.utc)
        )
    ]
    
    portfolio = Portfolio(
        user_id=user_id,
        holdings=holdings,
        transactions=transactions,
        cash_balance=7500.0  # 10000 - 1500 - 1000
    )
    
    return {
        "user_id": user_id,
        "holdings": holdings,
        "transactions": transactions,
        "portfolio": portfolio,
        "cash_balance": 7500.0,
        "total_holdings_value": 2525.0,  # 1550 + 975
        "total_portfolio_value": 10025.0,  # 7500 + 2525
        "total_unrealized_pnl": 25.0,  # 50 - 25
        "unrealized_pnl_percentage": 0.99  # 25 / 2525 * 100
    }


@pytest.fixture
def multiple_portfolio_holdings():
    """Multiple portfolio holdings for comprehensive testing"""
    import uuid
    
    user_id = uuid.uuid4()
    
    return [
        PortfolioHolding(
            id=uuid.uuid4(),
            user_id=user_id,
            symbol="AAPL",
            quantity=10.0,
            average_price=150.0,
            current_price=155.0,
            total_value=1550.0,
            unrealized_pnl=50.0,
            pnl_percentage=3.33,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        PortfolioHolding(
            id=uuid.uuid4(),
            user_id=user_id,
            symbol="GOOGL",
            quantity=5.0,
            average_price=200.0,
            current_price=195.0,
            total_value=975.0,
            unrealized_pnl=-25.0,
            pnl_percentage=-2.5,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        PortfolioHolding(
            id=uuid.uuid4(),
            user_id=user_id,
            symbol="MSFT",
            quantity=8.0,
            average_price=300.0,
            current_price=320.0,
            total_value=2560.0,
            unrealized_pnl=160.0,
            pnl_percentage=6.67,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        PortfolioHolding(
            id=uuid.uuid4(),
            user_id=user_id,
            symbol="TSLA",
            quantity=3.0,
            average_price=250.0,
            current_price=220.0,
            total_value=660.0,
            unrealized_pnl=-90.0,
            pnl_percentage=-12.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    ]


@pytest.fixture
def portfolio_transaction_history():
    """Complete transaction history for testing"""
    import uuid
    
    user_id = uuid.uuid4()
    
    return [
        Transaction(
            id=uuid.uuid4(),
            user_id=user_id,
            symbol="AAPL",
            transaction_type=TransactionType.BUY,
            quantity=10.0,
            price=150.0,
            total_amount=1500.0,
            created_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)
        ),
        Transaction(
            id=uuid.uuid4(),
            user_id=user_id,
            symbol="GOOGL",
            transaction_type=TransactionType.BUY,
            quantity=5.0,
            price=200.0,
            total_amount=1000.0,
            created_at=datetime(2024, 1, 15, 11, 00, tzinfo=timezone.utc)
        ),
        Transaction(
            id=uuid.uuid4(),
            user_id=user_id,
            symbol="AAPL",
            transaction_type=TransactionType.SELL,
            quantity=3.0,
            price=155.0,
            total_amount=465.0,
            created_at=datetime(2024, 1, 15, 14, 30, tzinfo=timezone.utc)
        ),
        Transaction(
            id=uuid.uuid4(),
            user_id=user_id,
            symbol="MSFT",
            transaction_type=TransactionType.BUY,
            quantity=8.0,
            price=300.0,
            total_amount=2400.0,
            created_at=datetime(2024, 1, 16, 9, 15, tzinfo=timezone.utc)
        )
    ]


@pytest.fixture
def portfolio_edge_cases():
    """Edge case scenarios for portfolio testing"""
    import uuid
    
    return {
        "minimal_position": PortfolioHolding(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            symbol="MINIMAL",
            quantity=0.01,  # Minimal positive quantity
            average_price=100.0,
            current_price=100.0,
            total_value=1.0,
            unrealized_pnl=0.0,
            pnl_percentage=0.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        "large_position": PortfolioHolding(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            symbol="LARGE",
            quantity=10000.0,
            average_price=1.0,
            current_price=1.05,
            total_value=10500.0,
            unrealized_pnl=500.0,
            pnl_percentage=50.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        "fractional_shares": PortfolioHolding(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            symbol="FRAC",
            quantity=0.123456,
            average_price=1234.56,
            current_price=1250.00,
            total_value=154.32,
            unrealized_pnl=1.91,
            pnl_percentage=1.25,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    }
