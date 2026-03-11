# app/domain/use_cases/portfolio_use_cases.py
import uuid
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime, timezone

from app.domain.entities.portfolio import PortfolioHolding, Transaction, TransactionType, Portfolio
from app.domain.entities.user import UserEntity


class PortfolioRepository(ABC):
    """Abstract repository for portfolio operations"""
    
    @abstractmethod
    async def get_user_holdings(self, user_id: uuid.UUID) -> List[PortfolioHolding]:
        pass
    
    @abstractmethod
    async def get_user_transactions(self, user_id: uuid.UUID) -> List[Transaction]:
        pass
    
    @abstractmethod
    async def get_holding_by_symbol(self, user_id: uuid.UUID, symbol: str) -> Optional[PortfolioHolding]:
        pass
    
    @abstractmethod
    async def create_holding(self, holding: PortfolioHolding) -> PortfolioHolding:
        pass
    
    @abstractmethod
    async def update_holding(self, holding: PortfolioHolding) -> PortfolioHolding:
        pass
    
    @abstractmethod
    async def delete_holding(self, holding_id: uuid.UUID) -> bool:
        pass
    
    @abstractmethod
    async def create_transaction(self, transaction: Transaction) -> Transaction:
        pass
    
    @abstractmethod
    async def update_user_balance(self, user_id: uuid.UUID, new_balance: float) -> bool:
        pass
    
    @abstractmethod
    async def get_user_balance(self, user_id: uuid.UUID) -> float:
        pass


class PortfolioUseCases:
    """Portfolio business logic use cases"""
    
    def __init__(self, portfolio_repository: PortfolioRepository):
        self.portfolio_repository = portfolio_repository
    
    async def get_portfolio_summary(self, user_id: uuid.UUID) -> dict:
        """Get complete portfolio summary"""
        holdings = await self.portfolio_repository.get_user_holdings(user_id)
        cash_balance = await self.portfolio_repository.get_user_balance(user_id)
        
        portfolio = Portfolio(
            user_id=user_id,
            holdings=holdings,
            cash_balance=cash_balance
        )
        
        return {
            "user_id": user_id,
            "cash_balance": cash_balance,
            "total_holdings_value": sum(holding.total_value for holding in holdings),
            "total_portfolio_value": portfolio.calculate_total_portfolio_value(),
            "total_unrealized_pnl": portfolio.calculate_total_unrealized_pnl(),
            "unrealized_pnl_percentage": portfolio.calculate_unrealized_pnl_percentage(),
            "holdings_count": len(holdings),
            "updated_at": datetime.now(timezone.utc)
        }
    
    async def get_holdings(self, user_id: uuid.UUID) -> List[PortfolioHolding]:
        """Get all user holdings"""
        return await self.portfolio_repository.get_user_holdings(user_id)
    
    async def get_transactions(self, user_id: uuid.UUID) -> List[Transaction]:
        """Get all user transactions"""
        return await self.portfolio_repository.get_user_transactions(user_id)
    
    async def buy_stock(self, user_id: uuid.UUID, symbol: str, quantity: float, price: float) -> Transaction:
        """Buy stocks - validate balance and create transaction"""
        total_cost = quantity * price
        current_balance = await self.portfolio_repository.get_user_balance(user_id)
        
        # Validate sufficient balance
        if current_balance < total_cost:
            raise ValueError(f"Insufficient balance. Required: ${total_cost:.2f}, Available: ${current_balance:.2f}")
        
        # Create transaction
        transaction = Transaction(
            user_id=user_id,
            symbol=symbol,
            transaction_type=TransactionType.BUY,
            quantity=quantity,
            price=price,
            total_amount=total_cost
        )
        
        # Update user balance
        new_balance = current_balance - total_cost
        await self.portfolio_repository.update_user_balance(user_id, new_balance)
        
        # Save transaction
        saved_transaction = await self.portfolio_repository.create_transaction(transaction)
        
        # Update or create holding
        existing_holding = await self.portfolio_repository.get_holding_by_symbol(user_id, symbol)
        
        if existing_holding:
            # Update existing holding
            existing_holding.add_shares(quantity, price)
            existing_holding.update_current_price(price)
            await self.portfolio_repository.update_holding(existing_holding)
        else:
            # Create new holding
            holding = PortfolioHolding(
                user_id=user_id,
                symbol=symbol,
                quantity=quantity,
                average_price=price,
                current_price=price,
                total_value=quantity * price,
                unrealized_pnl=0.0,
                pnl_percentage=0.0
            )
            await self.portfolio_repository.create_holding(holding)
        
        return saved_transaction
    
    async def sell_stock(self, user_id: uuid.UUID, symbol: str, quantity: float, price: float) -> Transaction:
        """Sell stocks - validate holdings and create transaction"""
        total_proceeds = quantity * price
        
        # Check if user has sufficient holdings
        existing_holding = await self.portfolio_repository.get_holding_by_symbol(user_id, symbol)
        if not existing_holding:
            raise ValueError(f"No holdings found for {symbol}")
        
        if existing_holding.quantity < quantity:
            raise ValueError(f"Insufficient holdings. Trying to sell: {quantity}, Available: {existing_holding.quantity}")
        
        # Create transaction
        transaction = Transaction(
            user_id=user_id,
            symbol=symbol,
            transaction_type=TransactionType.SELL,
            quantity=quantity,
            price=price,
            total_amount=total_proceeds
        )
        
        # Update user balance
        current_balance = await self.portfolio_repository.get_user_balance(user_id)
        new_balance = current_balance + total_proceeds
        await self.portfolio_repository.update_user_balance(user_id, new_balance)
        
        # Save transaction
        saved_transaction = await self.portfolio_repository.create_transaction(transaction)
        
        # Update holding
        existing_holding.remove_shares(quantity)
        
        if existing_holding.quantity == 0:
            # Remove holding completely
            await self.portfolio_repository.delete_holding(existing_holding.id)
        else:
            # Update existing holding
            existing_holding.update_current_price(price)
            await self.portfolio_repository.update_holding(existing_holding)
        
        return saved_transaction
    
    async def update_holding_prices(self, user_id: uuid.UUID, price_updates: dict) -> bool:
        """Update current prices for user holdings"""
        holdings = await self.portfolio_repository.get_user_holdings(user_id)
        
        for holding in holdings:
            if holding.symbol in price_updates:
                holding.update_current_price(price_updates[holding.symbol])
                await self.portfolio_repository.update_holding(holding)
        
        return True
