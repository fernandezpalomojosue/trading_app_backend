# app/services/polygon/client.py
from datetime import datetime
from typing import Dict, List, Optional, Union
import httpx
from pydantic import BaseModel
from .config import POLYGON_API_KEY

class MassiveClient:
    """Cliente para interactuar con la API de Massive.com"""
    
    BASE_URL = "https://api.massive.com/v3"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or POLYGON_API_KEY
        if not self.api_key:
            raise ValueError("Se requiere una API key para Massive.com")
        self._client = None
    
    @property
    def client(self):
        """Obtiene una instancia del cliente HTTP, creándola si es necesario"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient()
        return self._client
    
    async def _make_request(
        self, 
        method: str,
        endpoint: str, 
        params: Optional[Dict] = None
    ) -> Dict:
        """Realiza una petición a la API de Massive.com"""
        if params is None:
            params = {}
            
        # Agregar la API key a los parámetros
        params["apiKey"] = self.api_key
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = await self.client.request(method, url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error en la petición a {url}: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Respuesta del servidor: {e.response.text}")
            raise
    
    async def get_tickers(
        self,
        market: str = "stocks",
        active: bool = True,
        limit: int = 100,
        sort: str = "ticker",
        order: str = "asc"
    ) -> Dict:
        """
        Obtiene una lista de tickers que coinciden con los criterios de búsqueda.
        
        Args:
            market: Tipo de mercado (stocks, crypto, fx, etc.)
            active: Si es True, solo devuelve activos que cotizan actualmente
            limit: Número máximo de resultados a devolver
            sort: Campo por el que ordenar los resultados
            order: Orden de los resultados (asc o desc)
        """
        params = {
            "market": market,
            "active": str(active).lower(),
            "limit": limit,
            "sort": sort,
            "order": order
        }
        return await self._make_request("GET", "/reference/tickers", params=params)
    
    # Implementación del patrón de contexto
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Cierra la sesión del cliente HTTP si está abierto"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None