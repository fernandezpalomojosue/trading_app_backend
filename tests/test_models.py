# tests/test_models.py
import pytest
import uuid
from datetime import datetime, timezone

from app.domain.entities.user import UserEntity
from app.domain.entities.market import Asset, MarketType, MarketSummary
from app.domain.entities.portfolio import PortfolioHolding, Transaction, TransactionType, Portfolio
from app.infrastructure.database.models import UserSQLModel


class TestUserEntity:
    """Test UserEntity domain model"""
    
    def test_user_entity_creation(self):
        """Test UserEntity creation with all fields"""
        user_id = uuid.uuid4()
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        user = UserEntity(
            id=user_id,
            email="test@example.com",
            username="testuser",
            balance=10000.0,  
            is_active=True,
            is_verified=True,
            is_superuser=False,
            created_at=created_at,
            updated_at=updated_at
        )
        
        assert user.id == user_id
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.balance == 10000.0  # Test explicit value
        assert user.is_active is True
        assert user.is_verified is True
        assert user.is_superuser is False
        assert user.created_at == created_at
        assert user.updated_at == updated_at
    
    def test_user_entity_defaults(self):
        """Test UserEntity with default values"""
        user_id = uuid.uuid4()
        
        user = UserEntity(
            id=user_id,
            email="test@example.com",
            username="testuser",
            balance=0.0,  # Explicit test value for defaults test
            is_active=True,
            is_verified=False,
            is_superuser=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        assert user.id == user_id
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.balance == 0.0  # Test explicit value
        assert user.is_active is True
        assert user.is_verified is False
        assert user.is_superuser is False


class TestUserSQLModel:
    """Test UserSQLModel database model"""
    
    def test_user_sql_model_creation(self):
        """Test UserSQLModel creation"""
        user = UserSQLModel(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            balance=1000.0,
            is_active=True,
            is_verified=True,
            is_superuser=False
        )
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.hashed_password == "hashed_password"
        assert user.balance == 1000.0
        assert user.is_active is True
        assert user.is_verified is True
        assert user.is_superuser is False
    
    def test_user_sql_model_defaults(self):
        """Test UserSQLModel with default values"""
        user = UserSQLModel(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password"
        )
        
        assert user.balance == 10000.0
        assert user.is_active is True
        assert user.is_verified is True  # Default is True in the model
        assert user.is_superuser is False


class TestMarketEntities:
    """Test market domain entities"""
    
    def test_asset_creation(self):
        """Test Asset entity creation"""
        asset = Asset(
            id="AAPL",
            symbol="AAPL",
            name="Apple Inc.",
            market=MarketType.STOCKS,
            currency="USD",
            price=150.0,
            change=2.5,
            change_percent=1.67,
            volume=1000000,
            active=True
        )
        
        assert asset.id == "AAPL"
        assert asset.symbol == "AAPL"
        assert asset.name == "Apple Inc."
        assert asset.market == MarketType.STOCKS
        assert asset.currency == "USD"
        assert asset.price == 150.0
        assert asset.change == 2.5
        assert asset.change_percent == 1.67
        assert asset.volume == 1000000
        assert asset.active is True
        assert asset.is_tradable() is True
    
    def test_market_summary_creation(self):
        """Test MarketSummary entity creation"""
        timestamp = datetime.now(timezone.utc)
        
        summary = MarketSummary(
            symbol="AAPL",
            open=148.0,
            close=150.0,
            high=152.0,
            low=147.0,
            volume=1000000,
            change=2.0,
            change_percent=1.35,
            timestamp=timestamp
        )
        
        assert summary.symbol == "AAPL"
        assert summary.open == 148.0
        assert summary.close == 150.0
        assert summary.high == 152.0
        assert summary.low == 147.0
        assert summary.volume == 1000000
        assert summary.change == 2.0
        assert summary.change_percent == 1.35
        assert summary.timestamp == timestamp
    
    def test_market_summary_properties(self):
        """Test MarketSummary computed properties"""
        summary = MarketSummary(
            symbol="AAPL",
            open=148.0,
            close=150.0,
            high=152.0,
            low=147.0,
            volume=1000000,
            change=2.0,
            change_percent=1.35
        )
        
        assert summary.is_positive is True
        assert summary.price_range == 5.0  # high - low = 152.0 - 147.0
    
    def test_market_type_enum(self):
        """Test MarketType enum"""
        assert MarketType.STOCKS.value == "stocks"
        assert MarketType.CRYPTO.value == "crypto"
        assert MarketType.FX.value == "fx"  # Changed from FOREX to FX
        assert MarketType.INDICES.value == "indices"


class TestPortfolioModels:
    """Test portfolio domain models"""
    
    def test_portfolio_holding_creation(self):
        """Test PortfolioHolding creation with all fields"""
        holding_id = uuid.uuid4()
        user_id = uuid.uuid4()
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        holding = PortfolioHolding(
            id=holding_id,
            user_id=user_id,
            symbol="AAPL",
            quantity=10.0,
            average_price=150.0,
            current_price=155.0,
            total_value=1550.0,
            unrealized_pnl=50.0,
            pnl_percentage=3.33,
            created_at=created_at,
            updated_at=updated_at
        )
        
        assert holding.id == holding_id
        assert holding.user_id == user_id
        assert holding.symbol == "AAPL"
        assert holding.quantity == 10.0
        assert holding.average_price == 150.0
        assert holding.current_price == 155.0
        assert holding.total_value == 1550.0
        assert holding.unrealized_pnl == 50.0
        assert holding.pnl_percentage == 3.33
        assert holding.created_at == created_at
        assert holding.updated_at == updated_at
    
    def test_portfolio_holding_update_price(self):
        """Test PortfolioHolding price update functionality"""
        holding = PortfolioHolding(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            symbol="AAPL",
            quantity=10.0,
            average_price=150.0,
            current_price=150.0,
            total_value=1500.0,
            unrealized_pnl=0.0,
            pnl_percentage=0.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Update price to 160.0
        holding.update_current_price(160.0)
        
        assert holding.current_price == 160.0
        assert holding.total_value == 1600.0  # 10 * 160
        assert holding.unrealized_pnl == 100.0  # 1600 - 1500
        assert holding.pnl_percentage == 6.666666666666667
        assert holding.updated_at > holding.created_at
    
    def test_portfolio_holding_add_shares(self):
        """Test PortfolioHolding add shares functionality"""
        holding = PortfolioHolding(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            symbol="AAPL",
            quantity=10.0,
            average_price=150.0,
            current_price=150.0,
            total_value=1500.0,
            unrealized_pnl=0.0,
            pnl_percentage=0.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Add 5 more shares at 155.0
        holding.add_shares(5.0, 155.0)
        
        assert holding.quantity == 15.0  # 10 + 5
        assert holding.average_price == 151.66666666666666
        assert holding.total_value == 2250.0  # 15 * 150
        assert holding.updated_at > holding.created_at
    
    def test_portfolio_holding_remove_shares(self):
        """Test PortfolioHolding remove shares functionality"""
        holding = PortfolioHolding(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            symbol="AAPL",
            quantity=10.0,
            average_price=150.0,
            current_price=160.0,
            total_value=1600.0,
            unrealized_pnl=100.0,
            pnl_percentage=6.67,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Remove 3 shares
        holding.remove_shares(3.0)
        
        assert holding.quantity == 7.0  # 10 - 3
        assert holding.total_value == 1120.0  # 7 * 160
        assert holding.updated_at > holding.created_at
    
    def test_portfolio_transaction_creation(self):
        """Test Transaction creation with all fields"""
        transaction_id = uuid.uuid4()
        user_id = uuid.uuid4()
        created_at = datetime.now(timezone.utc)
        
        transaction = Transaction(
            id=transaction_id,
            user_id=user_id,
            symbol="AAPL",
            transaction_type=TransactionType.BUY,
            quantity=10.0,
            price=150.0,
            total_amount=1500.0,
            created_at=created_at
        )
        
        assert transaction.id == transaction_id
        assert transaction.user_id == user_id
        assert transaction.symbol == "AAPL"
        assert transaction.transaction_type == TransactionType.BUY
        assert transaction.quantity == 10.0
        assert transaction.price == 150.0
        assert transaction.total_amount == 1500.0
        assert transaction.created_at == created_at
    
    def test_portfolio_transaction_auto_calculate_total(self):
        """Test Transaction auto-calculates total amount"""
        transaction = Transaction(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            symbol="AAPL",
            transaction_type=TransactionType.BUY,
            quantity=10.0,
            price=150.0,
            total_amount=1500.0  # Will be auto-calculated
        )
        
        assert transaction.total_amount == 1500.0  # 10 * 150
    
    def test_portfolio_creation(self):
        """Test Portfolio aggregate creation"""
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
            )
        ]
        
        portfolio = Portfolio(
            user_id=user_id,
            holdings=holdings,
            transactions=transactions,
            cash_balance=8500.0
        )
        
        assert portfolio.user_id == user_id
        assert len(portfolio.holdings) == 1
        assert len(portfolio.transactions) == 1
        assert portfolio.cash_balance == 8500.0
    
    def test_portfolio_calculations(self):
        """Test Portfolio calculation methods"""
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
        
        portfolio = Portfolio(
            user_id=user_id,
            holdings=holdings,
            transactions=[],
            cash_balance=7500.0
        )
        
        # Test calculations
        assert portfolio.calculate_total_portfolio_value() == 10025.0  # 7500 + 1550 + 975
        assert portfolio.calculate_total_unrealized_pnl() == 25.0  # 50 - 25
        assert portfolio.calculate_unrealized_pnl_percentage() == 1.0  # (25 / 2500) * 100
    
    def test_portfolio_get_holding_by_symbol(self):
        """Test Portfolio get holding by symbol functionality"""
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
        
        portfolio = Portfolio(
            user_id=user_id,
            holdings=holdings,
            transactions=[],
            cash_balance=7500.0
        )
        
        # Test getting existing holding
        aapl_holding = portfolio.get_holding_by_symbol("AAPL")
        assert aapl_holding is not None
        assert aapl_holding.symbol == "AAPL"
        assert aapl_holding.quantity == 10.0
        
        # Test getting non-existing holding
        non_existing = portfolio.get_holding_by_symbol("TSLA")
        assert non_existing is None


class TestUserModels:
    """Test user domain models"""
    
    def test_user_entity_creation(self, sample_user):
        """Test UserEntity creation using fixture"""
        user = sample_user
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.balance == 10000.0
        assert user.is_active is True
        assert user.is_verified is True
        assert user.is_superuser is False
        assert user.id is not None
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_sql_model_creation(self, sample_user_sql):
        """Test UserSQLModel creation using fixture"""
        user = sample_user_sql
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.balance == 10000.0
        assert user.is_active is True
        assert user.is_verified is True
        assert user.is_superuser is False
        assert user.hashed_password == "hashed_password"
        assert user.id is not None
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_inactive_user(self, sample_inactive_user):
        """Test inactive user fixture"""
        user = sample_inactive_user
        
        assert user.is_active is False
        assert user.is_verified is True
        assert user.balance == 5000.0
    
    def test_unverified_user(self, sample_unverified_user):
        """Test unverified user fixture"""
        user = sample_unverified_user
        
        assert user.is_active is True
        assert user.is_verified is False
        assert user.balance == 7500.0
    
    def test_superuser(self, sample_superuser):
        """Test superuser fixture"""
        user = sample_superuser
        
        assert user.is_superuser is True
        assert user.balance == 50000.0
        assert user.username == "admin"
    
    def test_multiple_users(self, multiple_users):
        """Test multiple users fixture"""
        users = multiple_users
        
        assert isinstance(users, list)
        assert len(users) == 3
        
        # Verify each user has required properties
        for user in users:
            assert isinstance(user, UserEntity)
            assert user.email is not None
            assert user.username is not None
            assert user.balance >= 0
            assert user.is_active is True
            assert user.is_verified is True
            assert user.is_superuser is False
        
        # Verify specific users
        emails = [user.email for user in users]
        assert "user1@example.com" in emails
        assert "user2@example.com" in emails
        assert "user3@example.com" in emails
        
        balances = [user.balance for user in users]
        assert 10000.0 in balances
        assert 15000.0 in balances
        assert 25000.0 in balances
    
    def test_user_test_data_completeness(self, user_test_data):
        """Test user test data set completeness"""
        data = user_test_data
        
        # Verify all expected keys exist
        expected_keys = ["user_id", "user_entity", "user_sql_model", "registration_data", "login_data"]
        
        for key in expected_keys:
            assert key in data, f"Missing key: {key}"
        
        # Verify data types
        assert isinstance(data["user_id"], uuid.UUID)
        assert isinstance(data["user_entity"], UserEntity)
        assert isinstance(data["user_sql_model"], UserSQLModel)
        assert isinstance(data["registration_data"], dict)
        assert isinstance(data["login_data"], dict)
        
        # Verify consistency between entity and SQL model
        entity = data["user_entity"]
        sql_model = data["user_sql_model"]
        
        assert entity.id == sql_model.id
        assert entity.email == sql_model.email
        assert entity.username == sql_model.username
        assert entity.balance == sql_model.balance
        assert entity.is_active == sql_model.is_active
        assert entity.is_verified == sql_model.is_verified
        assert entity.is_superuser == sql_model.is_superuser
    
    def test_user_edge_cases(self, user_edge_cases):
        """Test user edge cases fixture"""
        edge_cases = user_edge_cases
        
        assert isinstance(edge_cases, dict)
        assert len(edge_cases) == 3
        
        # Test zero balance user
        zero_balance = edge_cases["zero_balance_user"]
        assert isinstance(zero_balance, UserEntity)
        assert zero_balance.balance == 0.0
        
        # Test high balance user
        high_balance = edge_cases["high_balance_user"]
        assert isinstance(high_balance, UserEntity)
        assert high_balance.balance == 1000000.0
        
        # Test fractional balance user
        fractional_balance = edge_cases["fractional_balance_user"]
        assert isinstance(fractional_balance, UserEntity)
        assert fractional_balance.balance == 12345.67
    
    def test_user_credentials_data(self, user_credentials_data):
        """Test user credentials data fixture"""
        credentials = user_credentials_data
        
        assert isinstance(credentials, dict)
        assert len(credentials) == 5
        
        # Verify all credential types exist
        expected_keys = ["valid_credentials", "invalid_email", "invalid_password", "missing_fields", "empty_credentials"]
        
        for key in expected_keys:
            assert key in credentials, f"Missing credentials type: {key}"
        
        # Verify valid credentials structure
        valid = credentials["valid_credentials"]
        assert "username" in valid
        assert "password" in valid
        assert "@" in valid["username"]  # Email format
        
        # Verify invalid cases
        invalid_email = credentials["invalid_email"]
        assert "@" not in invalid_email["username"]
        
        missing_fields = credentials["missing_fields"]
        assert "password" not in missing_fields
        
        empty_credentials = credentials["empty_credentials"]
        assert empty_credentials["username"] == ""
        assert empty_credentials["password"] == ""
