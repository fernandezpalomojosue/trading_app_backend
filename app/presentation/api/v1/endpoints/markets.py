# app/presentation/api/v1/endpoints/markets.py
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional

from app.application.dto.market_dto import (
    MarketOverviewResponse, AssetResponse, CandleStickResponse
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
        details=asset.details
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


@router.get("/{symbol}/candles", response_model=List[CandleStickResponse])
async def get_candlestick_data(
    symbol: str,
    timeframe: str = Query("1d", description="Timeframe: 1m, 5m, 15m, 1h, 1d"),
    timespan: str = Query(None, description="Alternative timespan: minute, hour, day"),
    multiplier: int = Query(None, description="Multiplier for timespan (e.g., 5 for 5-minute candles)"),
    limit: int = Query(100, ge=1, le=5000, description="Number of candlesticks to return"),
    start_date: str = Query(None, description="Start date in YYYY-MM-DD format"),
    market_service: MarketService = Depends(get_market_service),
    current_user = Depends(get_current_user_dependency)
):
    """Get candlestick data for charting"""
    # Support both timeframe and timespan parameters
    effective_timeframe = timeframe
    if timespan:
        # Convert timespan to timeframe format with multiplier
        timespan_mapping = {
            "minute": "1m",
            "hour": "1h", 
            "day": "1d"
        }
        base_timeframe = timespan_mapping.get(timespan, timeframe)
        
        # Apply multiplier if provided
        if multiplier and multiplier > 1:
            if timespan == "minute":
                effective_timeframe = f"{multiplier}m"
            elif timespan == "hour":
                effective_timeframe = f"{multiplier}h"
            elif timespan == "day":
                effective_timeframe = f"{multiplier}d"
        else:
            effective_timeframe = base_timeframe
    
    candlesticks = await market_service.get_candlestick_data(symbol, effective_timeframe, limit, start_date)
    
    return [
        CandleStickResponse(
            timestamp=candle.timestamp.isoformat(),
            open=candle.open,
            high=candle.high,
            low=candle.low,
            close=candle.close,
            volume=candle.volume
        )
        for candle in candlesticks
    ]
