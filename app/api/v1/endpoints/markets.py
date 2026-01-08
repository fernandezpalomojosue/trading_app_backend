# app/api/v1/endpoints/markets.py
from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import List, Optional

from app.schemas.market import MarketType, MarketOverview, Asset
from app.services.polygon.client import MassiveClient

router = APIRouter(prefix="/markets", tags=["markets"])

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

# app/api/v1/endpoints/markets.py
@router.get("/{market_type}/overview", response_model=MarketOverview)
async def get_market_overview(market_type: MarketType):
    """
    Obtiene un resumen del mercado de acciones con datos en tiempo real.
    
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
    
    async with MassiveClient() as client:
        try:
            # 1. Obtener el resumen diario del mercado
            market_summary = await client.get_daily_market_summary()
            
            if not market_summary or "results" not in market_summary:
                raise HTTPException(
                    status_code=404,
                    detail="No se encontraron datos de mercado"
                )
            
            # 2. Procesar los resultados
            results = market_summary.get("results", [])
            
            # 3. Filtrar y formatear los datos
            processed_results = []
            for r in results:
                try:
                    if all(k in r for k in ["T", "c", "o", "h", "l", "v", "vw"]):
                        change = r["c"] - r["o"]
                        change_percent = (change / r["o"]) * 100 if r["o"] > 0 else 0
                        
                        processed_results.append({
                            "symbol": r["T"],
                            "open": r["o"],
                            "high": r["h"],
                            "low": r["l"],
                            "close": r["c"],
                            "volume": r["v"],
                            "vwap": r["vw"],
                            "change": round(change, 4),
                            "change_percent": round(change_percent, 2)
                        })
                except (TypeError, KeyError):
                    continue
            
            # 4. Ordenar y obtener top ganadores, perdedores y más activos
            top_gainers = sorted(
                processed_results,
                key=lambda x: x["change_percent"],
                reverse=True
            )[:10]
            
            top_losers = sorted(
                processed_results,
                key=lambda x: x["change_percent"]
            )[:10]
            
            most_active = sorted(
                processed_results,
                key=lambda x: x["volume"],
                reverse=True
            )[:10]
            
            # 5. Construir la respuesta
            return MarketOverview(
                market=market_type,
                total_assets=len(processed_results),
                status="open",
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
    Lista los activos de un mercado específico.
    
    Args:
        market_type: Tipo de mercado
        limit: Número máximo de resultados a devolver (máx 1000)
        offset: Número de resultados a omitir
        
    Returns:
        List[Asset]: Lista de activos del mercado especificado
    """
    limit = max(1, min(1000, limit))  # Limitar entre 1 y 1000
    
    async with MassiveClient() as client:
        try:
            response = await client.get_tickers(
                market=market_type.value,
                limit=limit,
                offset=offset
            )
            
            return [
                Asset(
                    id=ticker.get("ticker"),
                    symbol=ticker.get("ticker"),
                    name=ticker.get("name", ""),
                    market=market_type,
                    currency=ticker.get("currency_name"),
                    active=ticker.get("active", True),
                    details=ticker
                )
                for ticker in response.get("results", [])
            ]
            
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
        symbol: Símbolo del activo (ej: AAPL, BTC-USD)
        
    Returns:
        Asset: Detalles del activo solicitado
    """
    async with MassiveClient() as client:
        try:
            ticker = await client.get_ticker_details(symbol)
            if not ticker:
                raise HTTPException(
                    status_code=404, 
                    detail=f"No se encontró el activo con símbolo {symbol}"
                )
            
            # Get market type from ticker details, default to STOCKS if not found
            market = ticker.get("market", "stocks").lower()
            market_enum = MarketType(market) if market in [m.value for m in MarketType] else MarketType.STOCKS
            
            # Extract basic fields
            ticker_symbol = ticker.get("ticker") or symbol.upper()
            
            # Create a clean details dict without duplicating fields
            details = {
                "description": ticker.get("description"),
                "homepage_url": ticker.get("homepage_url"),
                "market_cap": ticker.get("market_cap"),
                "shares_outstanding": ticker.get("share_class_shares_outstanding"),
                "primary_exchange": ticker.get("primary_exchange"),
                "market_data": ticker.get("market_data", {})
            }
            
            # Remove None values from details
            details = {k: v for k, v in details.items() if v is not None}
            
            return Asset(
                id=ticker_symbol.lower(),
                symbol=ticker_symbol,
                name=ticker.get("name", ticker_symbol),
                market=market_enum,
                currency=ticker.get("currency", "USD"),
                active=ticker.get("active", True),
                details=details
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error al obtener el activo: {str(e)}"
            )