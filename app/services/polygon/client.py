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
    
    async def get_market_data(self, market_type: str) -> Dict[str, Any]:
        """Obtiene datos generales de un mercado"""
        return await self._make_request(
            "GET",
            f"/v3/reference/tickers",
            params={
                "market": market_type,
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
    
    async def get_most_active_tickers(self, limit: int = 50) -> List[str]:
        """Devuelve una lista de tickers populares"""
        # Lista de tickers populares (puedes ajustar esta lista según necesites)
        popular_tickers = [
            'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA', 'JPM', 'V', 'JNJ',
            'WMT', 'PG', 'MA', 'UNH', 'HD', 'BAC', 'DIS', 'PYPL', 'ADBE', 'CMCSA',
            'XOM', 'VZ', 'NFLX', 'INTC', 'PFE', 'CSCO', 'KO', 'PEP', 'MRK', 'ABT',
            'T', 'ABBV', 'CVX', 'CRM', 'ACN', 'NKE', 'MCD', 'TMO', 'DHR', 'NEE',
            'TXN', 'HON', 'QCOM', 'UNP', 'LOW', 'ORCL', 'LLY', 'PM', 'AMD', 'COST'
        ]
        return popular_tickers[:min(limit, len(popular_tickers))]
    # app/services/polygon/client.py (add this method to the MassiveClient class)
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

    async def _process_ticker(self, ticker: str) -> Optional[Tuple[Dict, float]]:
        """Procesa un solo ticker y devuelve sus datos"""
        try:
            yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
            data = await self._make_request(
                "GET",
                f"/v1/open-close/{ticker.upper()}/{yesterday}",
                params={"adjusted": "true"}
            )
            
            if not data or data.get('status') != 'OK':
                return None

            open_price = data.get('open', 0)
            close_price = data.get('close', 0)
            change = close_price - open_price
            change_percent = (change / open_price * 100) if open_price != 0 else 0
            
            ticker_data = {
                'symbol': ticker.upper(),
                'price': close_price,
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'volume': data.get('volume', 0),
                'high': data.get('high'),
                'low': data.get('low'),
                'after_hours': data.get('afterHours'),
                'pre_market': data.get('preMarket')
            }
            
            return ticker_data, change_percent
            
        except Exception as e:
            print(f"Error procesando {ticker}: {str(e)}")
            return None
    
    async def get_top_movers(self, tickers: List[str], batch_size: int = 5) -> Dict[str, List[Dict]]:
        """Obtiene los top ganadores, perdedores y más activos en lotes"""
        results = {
            'gainers': [],  # Mayores subidas porcentuales
            'losers': [],   # Mayores bajadas porcentuales
            'actives': []   # Mayores volúmenes
        }
        
        # Procesar los tickers en lotes para respetar el rate limit
        for i in range(0, len(tickers), batch_size):
            batch = tickers[i:i + batch_size]
            # Usar asyncio.gather para procesar el lote actual en paralelo
            batch_results = await asyncio.gather(
                *[self._process_ticker(ticker) for ticker in batch],
                return_exceptions=True
            )
            
            # Procesar resultados del lote actual
            for ticker_result in batch_results:
                if isinstance(ticker_result, Exception) or not ticker_result:
                    continue
                    
                ticker_data, change_percent = ticker_result
                
                # Añadir a activos
                results['actives'].append(ticker_data)
                
                # Clasificar como ganador o perdedor
                if change_percent > 0:
                    results['gainers'].append((ticker_data, change_percent))
                else:
                    results['losers'].append((ticker_data, abs(change_percent)))
            
            # Pequeña pausa entre lotes para respetar el rate limit
            if i + batch_size < len(tickers):
                await asyncio.sleep(1)
        
        # Ordenar y limitar resultados a los 10 primeros
        results['gainers'] = [x[0] for x in sorted(
            results['gainers'],
            key=lambda x: x[1],  # Ordenar por cambio porcentual
            reverse=True
        )[:10]]
        
        results['losers'] = [x[0] for x in sorted(
            results['losers'],
            key=lambda x: x[1],  # Ordenar por cambio porcentual absoluto
            reverse=True
        )[:10]]
        
        results['actives'] = sorted(
            results['actives'],
            key=lambda x: x['volume'],  # Ordenar por volumen
            reverse=True
        )[:10]
        
        return results