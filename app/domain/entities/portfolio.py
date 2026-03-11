# app/domain/entities/portfolio.py
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class PortfolioHolding(BaseModel):
    """Represents a user's stock holding"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    symbol: str
    quantity: float = Field(gt=0, description="Number of shares owned")
    average_price: float = Field(gt=0, description="Average purchase price per share")
    current_price: float = Field(gt=0, description="Current market price per share")
    total_value: float = Field(ge=0, description="Total value of holding")
    unrealized_pnl: float = Field(description="Unrealized profit/loss")
    pnl_percentage: float = Field(description="Unrealized P&L percentage")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def update_current_price(self, new_price: float):
        """Update current price and recalculate P&L"""
        self.current_price = new_price
        self.total_value = self.quantity * new_price
        total_cost = self.quantity * self.average_price
        self.unrealized_pnl = self.total_value - total_cost
        self.pnl_percentage = (self.unrealized_pnl / total_cost * 100) if total_cost > 0 else 0.0
        self.updated_at = datetime.now(timezone.utc)
    
    def add_shares(self, quantity: float, price: float):
        """Add shares to holding (buy transaction)"""
        total_cost = self.quantity * self.average_price
        additional_cost = quantity * price
        
        self.quantity += quantity
        self.average_price = (total_cost + additional_cost) / self.quantity
        self.update_current_price(self.current_price)
    
    def remove_shares(self, quantity: float):
        """Remove shares from holding (sell transaction)"""
        if quantity >= self.quantity:
            # Selling all shares
            self.quantity = 0
        else:
            self.quantity -= quantity
        self.update_current_price(self.current_price)


class Transaction(BaseModel):
    """Represents a buy/sell transaction"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    symbol: str
    transaction_type: TransactionType
    quantity: float = Field(gt=0, description="Number of shares")
    price: float = Field(gt=0, description="Price per share")
    total_amount: float = Field(gt=0, description="Total transaction amount")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __init__(self, **data):
        if 'total_amount' not in data and 'quantity' in data and 'price' in data:
            data['total_amount'] = data['quantity'] * data['price']
        super().__init__(**data)


class Portfolio(BaseModel):
    """Represents a user's complete portfolio"""
    user_id: uuid.UUID
    holdings: List[PortfolioHolding] = Field(default_factory=list)
    transactions: List[Transaction] = Field(default_factory=list)
    cash_balance: float = Field(ge=0, description="Available cash balance")
    
    def add_holding(self, holding: PortfolioHolding):
        """Add a new holding to the portfolio"""
        self.holdings.append(holding)
    
    def add_transaction(self, transaction: Transaction):
        """Add a transaction to the portfolio"""
        self.transactions.append(transaction)
    
    def get_holding_by_symbol(self, symbol: str) -> Optional[PortfolioHolding]:
        """Get holding by symbol"""
        for holding in self.holdings:
            if holding.symbol == symbol:
                return holding
        return None
    
    def calculate_total_portfolio_value(self) -> float:
        """Calculate total portfolio value (holdings + cash)"""
        holdings_value = sum(holding.total_value for holding in self.holdings)
        return holdings_value + self.cash_balance
    
    def calculate_total_unrealized_pnl(self) -> float:
        """Calculate total unrealized P&L across all holdings"""
        return sum(holding.unrealized_pnl for holding in self.holdings)
    
    def calculate_unrealized_pnl_percentage(self) -> float:
        """Calculate total unrealized P&L percentage"""
        total_cost = sum(holding.quantity * holding.average_price for holding in self.holdings)
        if total_cost == 0:
            return 0.0
        total_pnl = self.calculate_total_unrealized_pnl()
        return (total_pnl / total_cost * 100)
    
    def update_all_holdings_prices(self, price_updates: dict):
        """Update current prices for all holdings"""
        for holding in self.holdings:
            if holding.symbol in price_updates:
                holding.update_current_price(price_updates[holding.symbol])
