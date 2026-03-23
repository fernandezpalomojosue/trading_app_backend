# app/presentation/api/v1/endpoints/routers.py
from fastapi import APIRouter

from app.presentation.api.v1.endpoints import auth, markets, portfolio, indicators

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(markets.router)
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(indicators.router)
