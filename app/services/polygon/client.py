# app/services/polygon/client.py
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import aiohttp
import os
from fastapi import HTTPException

class RateLimiter:
    """Clase para manejar el rate limiting"""
    def __init__(self, calls_per_minute: int = 5):
        self.calls_per_minute = calls_per_minute
        self.calls = []
        self.lock = asyncio.Lock()
    
    async def wait_if_needed(self):
        async with self.lock:
            now = time.time()
            # Eliminar llamadas más antiguas a 1 minuto
            self.calls = [t for t in self.calls if now - t < 60]
            
            if len(self.calls) >= self.calls_per_minute:
                # Calcular cuánto tiempo esperar
                oldest_call = self.calls[0]
                wait_time = 60 - (now - oldest_call)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
            
            self.calls.append(time.time())

class MassiveClient:
    """Cliente para interactuar con la API de Massive"""
    
    BASE_URL = "https://api.massive.com"  # Asegúrate de que esta sea la URL correcta
    
    def __init__(self, api_key: str = None, rate_limit: int = 5):
        self.api_key = api_key or os.getenv("MASSIVE_API_KEY") or os.getenv("POLYGON_API_KEY")
        if not self.api_key:
            raise ValueError("Se requiere una API key para Massive API")
        self.rate_limiter = RateLimiter(calls_per_minute=rate_limit)
        self.session = None
    
    async def __aenter__(self):
        """Inicializa la sesión asíncrona"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        """Cierra la sesión asíncrona"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Método interno para realizar peticiones a la API con rate limiting"""
        if not self.session:
            raise RuntimeError("La sesión no está inicializada. Usa 'async with MassiveClient()'")
        
        # Esperar si es necesario para cumplir con el rate limit
        await self.rate_limiter.wait_if_needed()
        
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.request(
                method, 
                url, 
                headers=headers,
                **{k: v for k, v in kwargs.items() if v is not None}
            ) as response:
                print("Yey")
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            error_msg = f"Error en la petición a {url}: {str(e)}"
            if hasattr(e, 'status'):
                if e.status == 429:
                    error_msg = "Demasiadas peticiones. Por favor, espera un momento antes de intentar de nuevo."
                elif e.status == 401:
                    error_msg = "Error de autenticación. Verifica tu API key."
            raise HTTPException(
                status_code=getattr(e, 'status', 500),
                detail=error_msg
            )
    
    async def get_tickers(self, limit: int = 100) -> Dict[str, Any]:
        """Obtiene una lista de tickers disponibles"""
        return await self._make_request(
            "GET",
            "/v3/reference/tickers",
            params={
                "active": "true",
                "limit": 1
            }
        )
    
    async def get_previous_day(self, ticker: str, adjusted: bool = True) -> Dict[str, Any]:
        """Obtiene los datos del día anterior para un ticker específico"""
        return await self._make_request(
            "GET",
            f"/v2/aggs/ticker/{ticker.upper()}/prev",
            params={"adjusted": str(adjusted).lower()}
        )
    async def get_ticker_details(self, symbol: str) -> Dict[str, Any]:
        """Obtiene los detalles de un ticker específico con datos del día actual
        
        Args:
            symbol: Símbolo del ticker (ej: AAPL, MSFT)
            
        Returns:
            Dict con los detalles del ticker incluyendo información de la empresa y datos de mercado
        """
        try:
            # Obtener información básica del ticker
            ticker_info = await self._make_request(
                "GET",
                f"/v3/reference/tickers/{symbol.upper()}"
            )
        
            if not ticker_info or 'results' not in ticker_info or not ticker_info['results']:
                raise HTTPException(status_code=404, detail=f"No se encontró información para el símbolo {symbol}")
        
            result = ticker_info['results']
        
            yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
            current_day = await self._make_request(
                "GET",
                f"/v1/open-close/{symbol.upper()}/{yesterday}",
                params={"adjusted": "true"}
            )
        
            market_data = {}
            if current_day and 'status' in current_day and current_day['status'] == 'OK':
                market_data = {
                    'price': current_day.get('close'),
                    'open': current_day.get('open'),
                    'high': current_day.get('high'),
                    'low': current_day.get('low'),
                    'volume': current_day.get('volume'),
                    'change': round(current_day.get('close', 0) - current_day.get('open', 0), 2) if current_day.get('open') else 0,
                    'change_percent': round(((current_day.get('close', 0) - current_day.get('open', 0)) / current_day['open'] * 100), 2) if current_day.get('open') else 0,
                    'after_hours': current_day.get('afterHours'),
                    'pre_market': current_day.get('preMarket'),
                    'last_updated': datetime.utcnow().isoformat()
                }
        
            # Construir la respuesta
            return {
                'id': result.get('ticker', '').lower(),
                'symbol': result.get('ticker', ''),
                'name': result.get('name', ''),
                'market': result.get('market', 'stocks'),
                'currency': result.get('currency_name', 'USD'),
                'active': result.get('active', False),
                'description': result.get('description', ''),
                'homepage_url': result.get('homepage_url'),
                'market_cap': result.get('market_cap'),
                'shares_outstanding': result.get('share_class_shares_outstanding'),
                'primary_exchange': result.get('primary_exchange'),
                'market_data': market_data
            }
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al obtener detalles del ticker {symbol}: {str(e)}"
            )
    async def get_daily_market_summary(self, date: str = None) -> Dict[str, Any]:
        """
        Obtiene el resumen diario del mercado para todas las acciones.
    
        Args:
            date: Fecha en formato YYYY-MM-DD. Si es None, usa el día anterior.
        
        Returns:
            Dict con los datos de mercado para todas las acciones
        """
        if date is None:
            date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    
        return await self._make_request(
            "GET",
            f"/v2/aggs/grouped/locale/us/market/stocks/{date}",
            params={"adjusted": "true"}
        )