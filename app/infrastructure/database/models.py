# app/infrastructure/database/models.py
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String


class UserSQLModel(SQLModel, table=True):
    """SQLModel for User table"""
    __tablename__ = "users"
    
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True, unique=True),
        description="User unique ID (UUID)"
    )
    email: str = Field(unique=True, index=True, description="User email")
    username: Optional[str] = Field(
        default=None, 
        index=True, 
        min_length=3, 
        max_length=50,
        description="Unique username (optional)"
    )
    full_name: Optional[str] = Field(
        default=None, 
        max_length=100, 
        description="User full name"
    )
    hashed_password: str = Field(
        ..., 
        min_length=8, 
        description="Hashed password"
    )
    is_active: bool = Field(
        default=True, 
        description="Indicates if user is active"
    )
    is_verified: bool = Field(
        default=True,
        description="Indicates if user email has been verified"
    )
    is_superuser: bool = Field(
        default=False, 
        description="Indicates if user is admin"
    )
    balance: float = Field(
        default=10000.0, 
        ge=0, 
        description="User balance"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="User creation date"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="User last update date"
    )
    
    __table_args__ = (
        {'sqlite_autoincrement': False},
    )
    
    @classmethod
    def from_domain_entity(cls, user_entity):
        return cls(
            id=user_entity.id,
            email=user_entity.email,
            username=user_entity.username,
            full_name=user_entity.full_name,
            is_active=user_entity.is_active,
            is_verified=user_entity.is_verified,
            is_superuser=user_entity.is_superuser,
            balance=user_entity.balance,
            created_at=user_entity.created_at,
            updated_at=user_entity.updated_at
        )
    
    def to_domain_entity(self):
        from app.domain.entities.user import UserEntity
        
        return UserEntity(
            id=self.id,
            email=self.email,
            username=self.username,
            full_name=self.full_name,
            is_active=self.is_active,
            is_verified=self.is_verified,
            is_superuser=self.is_superuser,
            balance=self.balance,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
    

class PortfolioHoldingSQLModel(SQLModel, table=True):
    """SQLModel for Portfolio Holdings table"""
    __tablename__ = "portfolio_holdings"
    
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True, unique=True),
        description="Portfolio holding unique ID (UUID)"
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), index=True),
        description="User ID who owns this holding"
    )
    symbol: str = Field(
        index=True,
        description="Stock symbol (e.g., AAPL, GOOGL)"
    )
    quantity: float = Field(
        gt=0,
        description="Number of shares owned"
    )
    average_price: float = Field(
        gt=0,
        description="Average purchase price per share"
    )
    current_price: float = Field(
        gt=0,
        description="Current market price per share"
    )
    total_value: float = Field(
        gt=0,
        description="Total value of holding (quantity * current_price)"
    )
    unrealized_pnl: float = Field(
        description="Unrealized profit/loss (total_value - total_cost)"
    )
    pnl_percentage: float = Field(
        description="Unrealized P&L percentage"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Holding creation date"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Holding last update date"
    )
    
    __table_args__ = (
        {"sqlite_autoincrement": False},
    )


class TransactionSQLModel(SQLModel, table=True):
    """SQLModel for Transactions table"""
    __tablename__ = "transactions"
    
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True, unique=True),
        description="Transaction unique ID (UUID)"
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), index=True),
        description="User ID who made this transaction"
    )
    symbol: str = Field(
        index=True,
        description="Stock symbol (e.g., AAPL, GOOGL)"
    )
    transaction_type: str = Field(
        description="Transaction type: BUY or SELL"
    )
    quantity: float = Field(
        gt=0,
        description="Number of shares transacted"
    )
    price: float = Field(
        gt=0,
        description="Price per share at time of transaction"
    )
    total_amount: float = Field(
        gt=0,
        description="Total amount of transaction (quantity * price)"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Transaction date"
    )
    
    __table_args__ = (
        {"sqlite_autoincrement": False},
    )


class FavoriteStockSQLModel(SQLModel, table=True):
    """SQLModel for Favorite Stocks table"""
    __tablename__ = "favorite_stocks"
    
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True, unique=True),
        description="Favorite stock unique ID (UUID)"
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), index=True),
        description="User ID who owns this favorite"
    )
    symbol: str = Field(
        sa_column=Column(String(10), index=True),
        description="Stock symbol (e.g., AAPL, GOOGL)"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Date when stock was added to favorites"
    )
    
    __table_args__ = (
        {"sqlite_autoincrement": False},
    )
    
    @classmethod
    def from_domain_entity(cls, favorite_entity):
        return cls(
            id=favorite_entity.id,
            user_id=favorite_entity.user_id,
            symbol=favorite_entity.symbol,
            created_at=favorite_entity.created_at
        )
    
    def to_domain_entity(self):
        from app.domain.entities.favorite_stock import FavoriteStockEntity
        
        return FavoriteStockEntity(
            id=self.id,
            user_id=self.user_id,
            symbol=self.symbol,
            created_at=self.created_at
        )
class SignalStockSQLModel(SQLModel, table=True):
    """SQLModel for Signal Stocks table"""
    __tablename__ = "signal_stocks"
    
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True, unique=True),
        description="Signal stock unique ID (UUID)"
    )
    symbol: str = Field(
        sa_column=Column(String(10), index=True),
        description="Stock symbol (e.g., AAPL, GOOGL)"
    )
    signal: str = Field(
        description="Signal type: BUY, SELL, or HOLD"
    )
    stop_loss: float = Field(
        description="Stop loss price"
    )
    take_profit: float = Field(
        description="Take profit price"
    )
    confidence: float = Field(
        description="Confidence level (0-1)"
    )
    reason: str = Field(
        description="Reason for the signal"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        description="Signal creation date"
    )
    
    __table_args__ = (
        {"sqlite_autoincrement": False},
    )
    
    @classmethod
    def from_domain_entity(cls, signal_entity):
        # Ensure created_at is timezone-naive for PostgreSQL
        created_at = signal_entity.created_at
        if created_at.tzinfo is not None:
            created_at = created_at.replace(tzinfo=None)
        
        return cls(
            id=signal_entity.id,
            symbol=signal_entity.symbol,
            signal=signal_entity.signal,
            stop_loss=signal_entity.stop_loss,
            take_profit=signal_entity.take_profit,
            confidence=signal_entity.confidence,
            reason=signal_entity.reason,
            created_at=created_at
        )
    
    def to_domain_entity(self):
        from app.domain.entities.signal_stock import SignalStockEntity
        
        return SignalStockEntity(
            id=self.id,
            symbol=self.symbol,
            signal=self.signal,
            stop_loss=self.stop_loss,
            take_profit=self.take_profit,
            confidence=self.confidence,
            reason=self.reason,
            created_at=self.created_at
        )