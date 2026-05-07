# app/presentation/api/v1/endpoints/routers.py
from fastapi import APIRouter

from app.presentation.api.v1.endpoints import auth, markets, portfolio, indicators, signals, strategies, ai_strategies, execution_plans

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(markets.router)
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(indicators.router, prefix="/indicators", tags=["indicators"])
api_router.include_router(signals.router, prefix="/signals", tags=["signals"])
api_router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
api_router.include_router(ai_strategies.router, prefix="/ai-strategies", tags=["ai-strategies"])
api_router.include_router(execution_plans.router, prefix="/execution-plans", tags=["execution-plans"])
