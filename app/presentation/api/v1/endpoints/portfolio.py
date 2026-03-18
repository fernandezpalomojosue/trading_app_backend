# app/presentation/api/v1/endpoints/portfolio.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from sqlmodel import Session

from app.application.services.portfolio_service import PortfolioService
from app.application.dto.portfolio_dto import (
    PortfolioSummaryResponse,
    HoldingResponse,
    TransactionResponse,
    BuyStockRequest,
    SellStockRequest
)
from app.core.security import get_current_user
from app.domain.entities.user import UserEntity
from app.db.base import get_session
from app.infrastructure.database.repositories import SQLPortfolioRepository


router = APIRouter()


# Dependency injection for PortfolioService
def get_portfolio_service(db: Session = Depends(get_session)) -> PortfolioService:
    """Get portfolio service instance (use cases implementation)"""
    from app.infrastructure.database.repositories import SQLPortfolioRepository
    portfolio_repository = SQLPortfolioRepository(db)
    from app.domain.use_cases.portfolio_use_cases import PortfolioUseCases
    return PortfolioUseCases(portfolio_repository)


@router.get("/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(
    current_user: UserEntity = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """Get portfolio summary for current user"""
    try:
        return await portfolio_service.get_portfolio_summary(current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving portfolio summary: {str(e)}"
        )


@router.get("/holdings", response_model=List[HoldingResponse])
async def get_holdings(
    current_user: UserEntity = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """Get all holdings for current user"""
    try:
        return await portfolio_service.get_holdings(current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving holdings: {str(e)}"
        )


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    current_user: UserEntity = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """Get all transactions for current user"""
    try:
        return await portfolio_service.get_transactions(current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving transactions: {str(e)}"
        )


@router.post("/buy", response_model=TransactionResponse)
async def buy_stock(
    request: BuyStockRequest,
    current_user: UserEntity = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """Buy stocks"""
    try:
        return await portfolio_service.buy_stock(current_user.id, request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error buying stocks: {str(e)}"
        )


@router.post("/sell", response_model=TransactionResponse)
async def sell_stock(
    request: SellStockRequest,
    current_user: UserEntity = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """Sell stocks"""
    try:
        return await portfolio_service.sell_stock(current_user.id, request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error selling stocks: {str(e)}"
        )