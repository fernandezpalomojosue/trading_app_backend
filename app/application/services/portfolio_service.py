# app/application/services/portfolio_service.py
import uuid
from typing import List, Optional
from abc import ABC, abstractmethod

from app.application.dto.portfolio_dto import (
    PortfolioSummaryResponse,
    HoldingResponse,
    TransactionResponse,
    BuyStockRequest,
    SellStockRequest
)
from app.domain.entities.portfolio import PortfolioHolding, Transaction


class PortfolioService(ABC):
    """Application interface for portfolio operations"""
    
    @abstractmethod
    async def get_portfolio_summary(self, user_id: uuid.UUID) -> PortfolioSummaryResponse:
        """Get portfolio summary for user"""
        pass
    
    @abstractmethod
    async def get_holdings(self, user_id: uuid.UUID) -> List[HoldingResponse]:
        """Get all holdings for user"""
        pass
    
    @abstractmethod
    async def get_transactions(self, user_id: uuid.UUID) -> List[TransactionResponse]:
        """Get all transactions for user"""
        pass
    
    @abstractmethod
    async def buy_stock(self, user_id: uuid.UUID, request: BuyStockRequest) -> TransactionResponse:
        """Buy stocks for user"""
        pass
    
    @abstractmethod
    async def sell_stock(self, user_id: uuid.UUID, request: SellStockRequest) -> TransactionResponse:
        """Sell stocks for user"""
        pass
    
    @abstractmethod
    async def update_holding_prices(self, user_id: uuid.UUID, price_updates: dict) -> bool:
        """Update holding prices (for market data integration)"""
        pass
