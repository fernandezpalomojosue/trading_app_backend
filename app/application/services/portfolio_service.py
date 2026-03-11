# app/application/services/portfolio_service.py
import uuid
from typing import List, Optional

from app.domain.use_cases.portfolio_use_cases import PortfolioUseCases
from app.domain.entities.portfolio import PortfolioHolding, Transaction
from app.application.dto.portfolio_dto import (
    PortfolioSummaryResponse,
    HoldingResponse,
    TransactionResponse,
    BuyStockRequest,
    SellStockRequest
)


class PortfolioService:
    """Application service for portfolio operations"""
    
    def __init__(self, portfolio_use_cases: PortfolioUseCases):
        self.portfolio_use_cases = portfolio_use_cases
    
    async def get_portfolio_summary(self, user_id: uuid.UUID) -> PortfolioSummaryResponse:
        """Get portfolio summary for user"""
        summary = await self.portfolio_use_cases.get_portfolio_summary(user_id)
        
        return PortfolioSummaryResponse(
            user_id=summary["user_id"],
            cash_balance=summary["cash_balance"],
            total_holdings_value=summary["total_holdings_value"],
            total_portfolio_value=summary["total_portfolio_value"],
            total_unrealized_pnl=summary["total_unrealized_pnl"],
            unrealized_pnl_percentage=summary["unrealized_pnl_percentage"],
            holdings_count=summary["holdings_count"],
            updated_at=summary["updated_at"]
        )
    
    async def get_holdings(self, user_id: uuid.UUID) -> List[HoldingResponse]:
        """Get all holdings for user"""
        holdings = await self.portfolio_use_cases.get_holdings(user_id)
        
        return [
            HoldingResponse(
                id=holding.id,
                symbol=holding.symbol,
                quantity=holding.quantity,
                average_price=holding.average_price,
                current_price=holding.current_price,
                total_value=holding.total_value,
                unrealized_pnl=holding.unrealized_pnl,
                pnl_percentage=holding.pnl_percentage,
                created_at=holding.created_at,
                updated_at=holding.updated_at
            )
            for holding in holdings
        ]
    
    async def get_transactions(self, user_id: uuid.UUID) -> List[TransactionResponse]:
        """Get all transactions for user"""
        transactions = await self.portfolio_use_cases.get_transactions(user_id)
        
        return [
            TransactionResponse(
                id=transaction.id,
                symbol=transaction.symbol,
                transaction_type=transaction.transaction_type,
                quantity=transaction.quantity,
                price=transaction.price,
                total_amount=transaction.total_amount,
                created_at=transaction.created_at
            )
            for transaction in transactions
        ]
    
    async def buy_stock(self, user_id: uuid.UUID, request: BuyStockRequest) -> TransactionResponse:
        """Buy stocks for user"""
        transaction = await self.portfolio_use_cases.buy_stock(
            user_id=user_id,
            symbol=request.symbol,
            quantity=request.quantity,
            price=request.price
        )
        
        return TransactionResponse(
            id=transaction.id,
            symbol=transaction.symbol,
            transaction_type=transaction.transaction_type,
            quantity=transaction.quantity,
            price=transaction.price,
            total_amount=transaction.total_amount,
            created_at=transaction.created_at
        )
    
    async def sell_stock(self, user_id: uuid.UUID, request: SellStockRequest) -> TransactionResponse:
        """Sell stocks for user"""
        transaction = await self.portfolio_use_cases.sell_stock(
            user_id=user_id,
            symbol=request.symbol,
            quantity=request.quantity,
            price=request.price
        )
        
        return TransactionResponse(
            id=transaction.id,
            symbol=transaction.symbol,
            transaction_type=transaction.transaction_type,
            quantity=transaction.quantity,
            price=transaction.price,
            total_amount=transaction.total_amount,
            created_at=transaction.created_at
        )
    
    async def update_holding_prices(self, user_id: uuid.UUID, price_updates: dict) -> bool:
        """Update holding prices (for market data integration)"""
        return await self.portfolio_use_cases.update_holding_prices(user_id, price_updates)
