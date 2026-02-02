# app/presentation/api/v1/endpoints/markets.py
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional

from app.application.dto.market_dto import (
    MarketOverviewResponse, AssetResponse, CandleStickDataResponse
)
from app.application.services.market_service import MarketService
from app.domain.entities.market import MarketType
from app.domain.use_cases.market_use_cases import MarketUseCases, MarketRepository, MarketDataCache
from app.infrastructure.external.market_client import PolygonMarketClient
from app.infrastructure.cache.memory_cache import MemoryMarketCache
from app.infrastructure.security.auth_dependencies import get_current_user_dependency

router = APIRouter(prefix="/markets", tags=["markets"])


def get_market_service() -> MarketService:
    """Dependency to get market service"""
    cache_service = MemoryMarketCache()
    market_repository = PolygonMarketClient()
    market_use_cases = MarketUseCases(market_repository, cache_service)
    return MarketService(market_use_cases)


@router.get("/{market_type}/overview", response_model=MarketOverviewResponse)
async def get_market_overview(
    market_type: MarketType,
    market_service: MarketService = Depends(get_market_service),
    current_user = Depends(get_current_user_dependency)
):
    """Get market overview by type"""
    overview = await market_service.get_market_overview(market_type)
    
    return MarketOverviewResponse(
        market=overview.market,
        total_assets=overview.total_assets,
        status=overview.status,
        last_updated=overview.last_updated.isoformat(),
        top_gainers=overview.top_gainers,
        top_losers=overview.top_losers,
        most_active=overview.most_active
    )


@router.get("/{market_type}/assets", response_model=List[AssetResponse])
async def list_assets(
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
    
    return [
        AssetResponse(
            id=asset.id,
            symbol=asset.symbol,
            name=asset.name,
            market=asset.market,
            currency=asset.currency,
            active=asset.active,
            price=asset.price,
            change=asset.change,
            change_percent=asset.change_percent,
            volume=asset.volume,
            details=asset.details
        )
        for asset in assets
    ]


@router.get("/assets/{symbol}", response_model=AssetResponse)
async def get_asset_details(
    symbol: str,
    market_service: MarketService = Depends(get_market_service),
    current_user = Depends(get_current_user_dependency)
):
    """Get asset details by symbol"""
    asset = await market_service.get_asset_details(symbol)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    structured_details = {
        "market_data": {
            "price": asset.price,
            "change": asset.change,
            "change_percent": asset.change_percent,
            "volume": asset.volume,
            "open": asset.details.get("open"),
            "high": asset.details.get("high"),
            "low": asset.details.get("low"),
            "vwap": asset.details.get("vwap")
        },
        "source": asset.details.get("source"),
        "market_cap": asset.details.get("market_cap"),
        "primary_exchange": asset.details.get("primary_exchange"),
        "description": asset.details.get("description"),
        "homepage_url": asset.details.get("homepage_url")
    }
    
    return AssetResponse(
        id=asset.id,
        symbol=asset.symbol,
        name=asset.name,
        market=asset.market,
        currency=asset.currency,
        active=asset.active,
        price=asset.price,
        change=asset.change,
        change_percent=asset.change_percent,
        volume=asset.volume,
        details=structured_details
    )


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
    limited_assets = assets[:limit]
    
    return [
        AssetResponse(
            id=asset.id,
            symbol=asset.symbol,
            name=asset.name,
            market=asset.market,
            currency=asset.currency,
            active=asset.active,
            price=asset.price,
            change=asset.change,
            change_percent=asset.change_percent,
            volume=asset.volume,
            details=asset.details
        )
        for asset in limited_assets
    ]


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
    candlesticks = await market_service.get_candlestick_data(
        symbol, timespan, multiplier, limit, start_date, end_date
    )
    
    from app.application.dto.market_dto import CandleData
    
    return CandleStickDataResponse(
        results=[
            CandleData(
                t=int(candle.timestamp.timestamp() * 1000),
                c=candle.close,
                o=candle.open,
                h=candle.high,
                l=candle.low,
                v=candle.volume
            )
            for candle in candlesticks
        ]
    )
