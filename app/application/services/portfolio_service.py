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
        return await self.portfolio_use_cases.get_portfolio_summary(user_id)
    
    async def get_holdings(self, user_id: uuid.UUID) -> List[HoldingResponse]:
        """Get all holdings for user"""
        return await self.portfolio_use_cases.get_holdings(user_id)
    
    async def get_transactions(self, user_id: uuid.UUID) -> List[TransactionResponse]:
        """Get all transactions for user"""
        return await self.portfolio_use_cases.get_transactions(user_id)
    
    async def buy_stock(self, user_id: uuid.UUID, request: BuyStockRequest) -> TransactionResponse:
        """Buy stocks for user"""
        return await self.portfolio_use_cases.buy_stock(
            user_id=user_id,
            symbol=request.symbol,
            quantity=request.quantity,
            price=request.price
        )
    
    async def sell_stock(self, user_id: uuid.UUID, request: SellStockRequest) -> TransactionResponse:
        """Sell stocks for user"""
        return await self.portfolio_use_cases.sell_stock(
            user_id=user_id,
            symbol=request.symbol,
            quantity=request.quantity,
            price=request.price
        )
    
    async def update_holding_prices(self, user_id: uuid.UUID, price_updates: dict) -> bool:
        """Update holding prices (for market data integration)"""
        return await self.portfolio_use_cases.update_holding_prices(user_id, price_updates)
