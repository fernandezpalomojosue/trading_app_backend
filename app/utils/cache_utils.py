# app/utils/cache_utils.py
"""
Utilidades para manejo de cache con TTL
"""

import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class TTLCache:
    """Cache con Time To Live (TTL) para métodos asíncronos"""
    
    def __init__(self, ttl_seconds: int = 300):  # 5 minutos por defecto
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    def _generate_key(self, method_name: str, *args, **kwargs) -> str:
        """Genera una clave única para el cache"""
        # Convertir args y kwargs a string para generar clave
        key_parts = [method_name]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return "|".join(key_parts)
    
    async def get(self, method_name: str, *args, **kwargs) -> Optional[Any]:
        """Obtiene valor del cache si no ha expirado"""
        key = self._generate_key(method_name, *args, **kwargs)
        
        async with self._lock:
            if key in self._cache:
                cached_item = self._cache[key]
                if time.time() - cached_item["timestamp"] < self.ttl_seconds:
                    return cached_item["value"]
                else:
                    # Expirado, eliminar
                    del self._cache[key]
        
        return None
    
    async def set(self, method_name: str, value: Any, *args, **kwargs) -> None:
        """Guarda valor en el cache con timestamp"""
        key = self._generate_key(method_name, *args, **kwargs)
        
        async with self._lock:
            self._cache[key] = {
                "value": value,
                "timestamp": time.time()
            }
    
    async def clear(self) -> None:
        """Limpia todo el cache"""
        async with self._lock:
            self._cache.clear()
    
    async def clear_pattern(self, pattern: str) -> None:
        """Limpia entradas que coincidan con un patrón"""
        async with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache"""
        return {
            "total_entries": len(self._cache),
            "ttl_seconds": self.ttl_seconds,
            "keys": list(self._cache.keys())
        }

# Instancia global de cache para datos de mercado
market_cache = TTLCache(ttl_seconds=300)  # 5 minutos

def cached(ttl_seconds: int = 300):
    """Decorador para cachear métodos asíncronos con TTL"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # El primer argumento es 'self', lo ignoramos para la clave
            method_name = f"{func.__module__}.{func.__qualname__}"
            cache_key_args = args[1:] if args else ()  # Ignorar self
            
            # Intentar obtener del cache
            cached_result = await market_cache.get(method_name, *cache_key_args, **kwargs)
            if cached_result is not None:
                return cached_result
            
            # Ejecutar función y guardar en cache
            result = await func(*args, **kwargs)
            await market_cache.set(method_name, result, *cache_key_args, **kwargs)
            
            return result
        
        return wrapper
    return decorator
