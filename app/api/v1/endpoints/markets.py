# app/api/v1/endpoints/markets.py
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.schemas.market import MarketType, MarketOverview, Asset
from app.services.polygon.client import MassiveClient
from app.utils.market_utils import process_market_results, get_paginated_results, get_top_assets
from app.utils.date_utils import get_last_trading_day
from app.utils.cache_utils import market_cache
from app.core.security import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/markets", tags=["markets"])

@router.get("/cache/stats", response_model=Dict[str, Any])
async def get_cache_stats(current_user: User = Depends(get_current_active_user)):
    """
    Obtiene estadísticas del cache de mercado.
    
    Returns:
        Dict[str, Any]: Estadísticas del cache incluyendo entradas y TTL
    """
    return market_cache.get_stats()

@router.delete("/cache")
async def clear_cache(current_user: User = Depends(get_current_active_user)):
    """
    Limpia todo el cache de mercado.
    
    Returns:
        Dict[str, str]: Confirmación de limpieza
    """
    await market_cache.clear()
    return {"message": "Cache limpiado exitosamente"}

@router.delete("/cache/market-summary")
async def clear_market_summary_cache(current_user: User = Depends(get_current_active_user)):
    """
    Limpia específicamente el cache del market summary.
    
    Returns:
        Dict[str, str]: Confirmación de limpieza específica
    """
    await market_cache.clear_pattern("get_daily_market_summary")
    return {"message": "Cache de market summary limpiado exitosamente"}


@router.get("", response_model=List[dict])
async def list_markets():
    """
    Obtiene la lista de tipos de mercados disponibles en la API.
    
    Returns:
        List[dict]: Lista de mercados disponibles con su ID y nombre
    """
    return [
        {"id": market.value, "name": market.value.capitalize()} 
        for market in MarketType
    ]

@router.get("/{market_type}/overview", response_model=MarketOverview)
async def get_market_overview(market_type: MarketType):
    """
    Obtiene un resumen del mercado de acciones con datos del último día hábil.
    
    Incluye:
    - Total de activos en el mercado
    - Top 10 ganadores del día
    - Top 10 perdedores del día
    - Top 10 más activos por volumen
    
    Args:
        market_type: Debe ser 'stocks' (otros mercados no soportados actualmente)
        
    Returns:
        MarketOverview: Resumen del mercado con estadísticas
    """
    if market_type != MarketType.STOCKS:
        raise HTTPException(
            status_code=400,
            detail="Solo se soporta el mercado de acciones (stocks) actualmente"
        )
    
    last_trading_date = get_last_trading_day()
    
    async with MassiveClient() as client:
        try:
            market_summary = await client.get_daily_market_summary(date=last_trading_date)
            
            if not market_summary or "results" not in market_summary:
                raise HTTPException(
                    status_code=404,
                    detail=f"No se encontraron datos de mercado para la fecha {last_trading_date}"
                )
            
            processed_results = process_market_results(
                market_summary.get("results", []),
                max_results=500
            )
            
            top_assets = get_top_assets(processed_results, top_n=10)
            top_gainers = top_assets["top_gainers"]
            top_losers = top_assets["top_losers"]
            most_active = top_assets["most_active"]
            
            return MarketOverview(
                market=market_type,
                total_assets=len(processed_results),
                status="closed",
                last_updated=datetime.utcnow(),
                top_gainers=top_gainers,
                top_losers=top_losers,
                most_active=most_active
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error al obtener el resumen del mercado: {str(e)}"
            )


@router.get("/{market_type}/assets", response_model=List[Asset])
async def list_assets(
    market_type: MarketType, 
    limit: int = 50, 
    offset: int = 0
):
    """
    Lista los activos de un mercado específico ordenados por volumen.
    
    Args:
        market_type: Tipo de mercado (solo 'stocks' soportado actualmente)
        limit: Número máximo de resultados a devolver (máx 500)
        offset: Número de resultados a omitir
        
    Returns:
        List[Asset]: Lista básica de activos del mercado especificado, ordenados por volumen
    """
    
    if market_type != MarketType.STOCKS:
        raise HTTPException(
            status_code=400,
            detail="Solo se soporta el mercado de acciones (stocks) actualmente"
        )
    
    limit = max(1, min(500, limit))
    
    async with MassiveClient() as client:
        try:
            market_summary = await client.get_daily_market_summary(date=get_last_trading_day())
            
            if not market_summary or "results" not in market_summary:
                raise HTTPException(
                    status_code=404,
                    detail="No se encontraron datos de mercado"
                )
            
            processed_results = process_market_results(
                market_summary.get("results", []),
                max_results=500
            )
            
            paginated_results = get_paginated_results(
                processed_results,
                offset=offset,
                limit=limit
            )
            
            results = [
                Asset(
                    id=asset["symbol"].lower(),
                    symbol=asset["symbol"],
                    name=asset["symbol"],
                    market=market_type,
                    currency="USD",
                    active=True,
                    price=asset["close"],
                    change=asset["change"],
                    change_percent=asset["change_percent"],
                    volume=asset["volume"],
                    details={}
                )
                for asset in paginated_results
            ]
            
            return results
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error al obtener los activos: {str(e)}"
            )

@router.get("/assets/{symbol}", response_model=Asset)
async def get_asset(symbol: str):
    """
    Obtiene los detalles de un activo específico por su símbolo.
    
    Args:
        symbol: Símbolo del activo (ej: AAPL, MSFT)
        
    Returns:
        Asset: Detalles completos del activo
    """
    async with MassiveClient() as client:
        try:
            data = await client.get_ticker_details(symbol)
            
            return Asset(
                id=data["id"],
                symbol=data["symbol"],
                name=data["name"],
                market=data["market"],
                currency=data["currency"],
                active=data["active"],
                details=data
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al obtener el activo {symbol}: {str(e)}"
            )

@router.get("/{symbol}/candles")
async def get_candles(
    symbol: str,
    multiplier: int = 1,
    timespan: str = "day",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    adjusted: bool = True,
    sort: str = "asc",
    limit: int = 5000
):
    """
    Obtiene datos de velas (OHLC) para un símbolo específico.
    
    Ejemplo de uso:
    - /markets/AAPL/candles?timespan=day&multiplier=1&start_date=2023-01-01&end_date=2023-01-31
    - /markets/MSFT/candles?timespan=hour&multiplier=4&limit=100
    """
    async with MassiveClient() as client:
        try:
            data = await client.get_ohlc_data(
                symbol=symbol,
                multiplier=multiplier,
                timespan=timespan,
                start_date=start_date,
                end_date=end_date,
                adjusted=adjusted,
                sort=sort,
                limit=limit
            )
            return data
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al procesar la solicitud: {str(e)}"
            )