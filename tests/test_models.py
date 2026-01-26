# tests/test_models.py
import pytest
import uuid
from datetime import datetime, timezone

from app.domain.entities.user import UserEntity
from app.domain.entities.market import Asset, MarketSummary, MarketOverview, MarketType
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
            balance=1000.0,
            is_active=True,
            is_verified=True,
            is_superuser=False,
            created_at=created_at,
            updated_at=updated_at
        )
        
        assert user.id == user_id
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.balance == 1000.0
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
            balance=0.0,
            is_active=True,
            is_verified=False,
            is_superuser=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        assert user.balance == 0.0
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
        
        assert user.balance == 0.0
        assert user.is_active is True
        assert user.is_verified is False
        assert user.is_superuser is False


class TestMarketEntities:
    """Test market domain entities"""
    
    def test_asset_creation(self):
        """Test Asset entity creation"""
        asset = Asset(
            symbol="AAPL",
            name="Apple Inc.",
            price=150.0,
            change=2.5,
            change_percent=1.67,
            volume=1000000,
            is_tradable=True
        )
        
        assert asset.symbol == "AAPL"
        assert asset.name == "Apple Inc."
        assert asset.price == 150.0
        assert asset.change == 2.5
        assert asset.change_percent == 1.67
        assert asset.volume == 1000000
        assert asset.is_tradable is True
    
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
        assert summary.price_range == "147.0 - 152.0"
    
    def test_market_overview_creation(self):
        """Test MarketOverview entity creation"""
        timestamp = datetime.now(timezone.utc)
        
        gainers = [
            MarketSummary(
                symbol="AAPL",
                open=148.0,
                close=150.0,
                high=152.0,
                low=147.0,
                volume=1000000,
                change=2.0,
                change_percent=1.35
            )
        ]
        
        losers = [
            MarketSummary(
                symbol="TSLA",
                open=200.0,
                close=195.0,
                high=205.0,
                low=194.0,
                volume=2000000,
                change=-5.0,
                change_percent=-2.5
            )
        ]
        
        most_active = gainers + losers
        
        overview = MarketOverview(
            market=MarketType.STOCKS,
            total_assets=2,
            status="active",
            last_updated=timestamp,
            top_gainers=gainers,
            top_losers=losers,
            most_active=most_active
        )
        
        assert overview.market == MarketType.STOCKS
        assert overview.total_assets == 2
        assert overview.status == "active"
        assert overview.last_updated == timestamp
        assert len(overview.top_gainers) == 1
        assert len(overview.top_losers) == 1
        assert len(overview.most_active) == 2
    
    def test_market_type_enum(self):
        """Test MarketType enum"""
        assert MarketType.STOCKS.value == "stocks"
        assert MarketType.CRYPTO.value == "crypto"
        assert MarketType.FOREX.value == "forex"
