# app/presentation/api/v1/endpoints/markets.py
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from uuid import UUID

from app.application.dto.market_dto import (
    MarketOverviewResponse, AssetResponse, CandleStickDataResponse,
    FavoriteStockResponse, FavoriteStockListResponse
)
from app.application.services.market_service import MarketService
from app.domain.entities.market import MarketType
from app.domain.repositories.market_repository import MarketRepository, MarketDataCache
from app.domain.use_cases.market_use_cases import MarketUseCases
from app.infrastructure.external.market_client import PolygonMarketClient
from app.infrastructure.cache.memory_cache import MemoryMarketCache
from app.infrastructure.cache.redis_cache import RedisMarketCache
from app.core.config import get_settings
from app.infrastructure.security.auth_dependencies import get_current_user_dependency
from app.domain.use_cases.portfolio_use_cases import PortfolioRepository
from app.infrastructure.database.user_repository import SQLUserRepository
from app.infrastructure.database.portfolio_repository import SQLPortfolioRepository
from app.infrastructure.database.favorite_repository import SQLFavoriteStockRepository
from app.db.base import get_session 
from sqlmodel import Session

router = APIRouter(prefix="/markets", tags=["market_info"])


def get_market_service(db: Session = Depends(get_session)) -> MarketService:
    """Get market service instance (use cases implementation)"""
    settings = get_settings()
    
    # Choose cache implementation based on configuration
    if settings.CACHE_TYPE == "redis":
        cache = RedisMarketCache(settings.REDIS_URL)
    else:
        cache = MemoryMarketCache()
    
    # Create repositories
    market_repository = PolygonMarketClient()
    portfolio_repository = SQLPortfolioRepository(db)
    
    class MarketRepository(MarketRepository):
        def __init__(self, base_repo: MarketRepository, favorite_repo: SQLFavoriteStockRepository):
            self.base_repo = base_repo
            self.favorite_repo = favorite_repo
        
        # Market data methods
        async def fetch_raw_market_data(self):
            return await self.base_repo.fetch_raw_market_data()
        
        async def fetch_ticker_details(self, symbol: str):
            return await self.base_repo.fetch_ticker_details(symbol)
        
        async def search_assets(self, query: str, market_type: Optional[str] = None):
            return await self.base_repo.search_assets(query, market_type)
        
        async def fetch_candlestick_data(self, symbol: str, timespan: str, multiplier: int, limit: int, start_date: Optional[str] = None, end_date: Optional[str] = None):
            return await self.base_repo.fetch_candlestick_data(symbol, timespan, multiplier, limit, start_date, end_date)
        
        # Favorite stock methods
        async def add_favorite(self, user_id: UUID, symbol: str):
            return await self.favorite_repo.add_favorite(user_id, symbol)
        
        async def remove_favorite(self, user_id: UUID, symbol: str):
            return await self.favorite_repo.remove_favorite(user_id, symbol)
        
        async def get_user_favorites(self, user_id: UUID):
            return await self.favorite_repo.get_user_favorites(user_id)
        
        async def is_favorite(self, user_id: UUID, symbol: str):
            return await self.favorite_repo.is_favorite(user_id, symbol)
        
        async def get_favorite_by_user_and_symbol(self, user_id: UUID, symbol: str):
            return await self.favorite_repo.get_favorite_by_user_and_symbol(user_id, symbol)
    
    favorite_stock_repository = SQLFavoriteStockRepository(db)
    
    return MarketUseCases(market_repository, cache, portfolio_repository, favorite_stock_repository)


@router.get("/{market_type}/overview", response_model=MarketOverviewResponse)
async def get_market_summary(
    market_type: MarketType,
    market_service: MarketService = Depends(get_market_service),
    current_user = Depends(get_current_user_dependency)
):
    """Get market summary by type"""
    return await market_service.get_market_overview(market_type)


@router.get("/{market_type}/assets", response_model=List[AssetResponse])
async def get_assets_list(
    market_type: MarketType,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of assets to return"),
    offset: int = Query(0, ge=0, description="Number of assets to skip for pagination"),
    market_service: MarketService = Depends(get_market_service),
    current_user = Depends(get_current_user_dependency)
):
    """List assets from raw market data"""
    if not market_type:
        market_type = MarketType.STOCKS  # Default to stocks
    
    assets = await market_service.get_assets_list(market_type, limit, offset)
    
    return assets


@router.get("/assets/{symbol}", response_model=AssetResponse)
async def get_asset_details(
    symbol: str,
    market_service: MarketService = Depends(get_market_service),
    current_user = Depends(get_current_user_dependency)
):
    """Get asset details by symbol"""
    asset = await market_service.get_asset_details(current_user, symbol)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return asset


@router.get("/search", response_model=List[AssetResponse])
async def search_assets(
    q: str = Query(..., min_length=2, description="Search query"),
    market_type: Optional[MarketType] = Query(None, description="Filter by market type"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of results"),
    market_service: MarketService = Depends(get_market_service),
    current_user = Depends(get_current_user_dependency)
):
    """Search for assets by query"""
    assets = await market_service.search_assets(q, market_type)
    
    # Apply limit
    return assets[:limit]


@router.get("/{symbol}/candles", response_model=CandleStickDataResponse)
async def get_candlestick_data(
    symbol: str,
    timespan: str = Query("day", description="Timespan: minute, hour, day, week, month, quarter, year"),
    multiplier: int = Query(1, description="Multiplier for timespan (e.g., 5 for 5-minute candles)"),
    limit: int = Query(100, ge=1, le=5000, description="Number of candlesticks to return"),
    start_date: str = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(None, description="End date in YYYY-MM-DD format (default: last trading date)"),
    market_service: MarketService = Depends(get_market_service),
    current_user = Depends(get_current_user_dependency)
):  
    """Get candlestick data for charting"""
    return await market_service.get_candlestick_data(
        symbol=symbol,
        timespan=timespan,
        multiplier=multiplier,
        limit=limit,
        start_date=start_date,
        end_date=end_date
    )


@router.post("/favorites/{symbol}", response_model=FavoriteStockResponse)
async def add_favorite_stock(
    symbol: str,
    market_service: MarketService = Depends(get_market_service),
    current_user = Depends(get_current_user_dependency)
):
    """Add a stock to user's favorites"""
    try:
        favorite = await market_service.add_favorite_stock(current_user.id, symbol)
        return favorite
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/favorites/{symbol}", response_model=FavoriteStockResponse)
async def remove_favorite_stock(
    symbol: str,
    market_service: MarketService = Depends(get_market_service),
    current_user = Depends(get_current_user_dependency)
):
    """Remove a stock from user's favorites"""
    try:
        favorite = await market_service.remove_favorite_stock(current_user.id, symbol)
        return favorite
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/favorites", response_model=FavoriteStockListResponse)
async def get_favorite_stocks(
    market_service: MarketService = Depends(get_market_service),
    current_user = Depends(get_current_user_dependency)
):
    """Get user's favorite stocks"""
    try:
        favorites = await market_service.get_user_favorite_stocks(current_user.id)
        return FavoriteStockListResponse(
            favorites=favorites,
            total=len(favorites)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))