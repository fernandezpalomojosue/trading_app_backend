from typing import Optional, List, Dict
import pandas as pd
#import ta
import pandas_ta as pta
import logging
import sys
from datetime import datetime

# Configure logging to output to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
from app.application.dto.indicators_dto import IndicatorDataPoint
from app.application.services.indicators_service import IndicatorsService
from app.domain.use_cases.signal_engine_use_cases import SignalEngineUseCases
from app.infrastructure.external.market_client import PolygonMarketClient
from app.application.repositories.cache_repository import CacheRepository
from app.domain.services.fibonacci_service import FibonacciService

logger = logging.getLogger(__name__)


class IndicatorsUseCases(IndicatorsService):

    def __init__(self, cache_service):
        self.cache = cache_service
        self.fibonacci_service = FibonacciService()

    async def get_indicators(
        self,
        symbol: str,
        data: List[dict],
        window: int,
        fast: int,
        slow: int,
        signal: int,
        timespan: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[IndicatorDataPoint]:

        cache_key = f"indicators_{symbol}_{window}_{fast}_{slow}_{signal}_{timespan}_{start_date}_{end_date}"
        print(f"DEBUG: About to call cache.get for {symbol} with key: {cache_key}")

        cached = await self.cache.get(cache_key)
        print(f"DEBUG: Cache get result for {symbol}: {type(cached)} - {cached is not None}")
        if cached:
            print(f"DEBUG: Using cached indicators for {symbol}")
            # Convert cached dictionaries back to IndicatorDataPoint objects
            return [
                IndicatorDataPoint(
                    timestamp=item.get('timestamp'),
                    symbol=item.get('symbol'),
                    close_price=item.get('close_price'),
                    ema=item.get('ema'),
                    sma=item.get('sma'),
                    rsi=item.get('rsi'),
                    macd=item.get('macd'),
                    macd_signal=item.get('signal'),
                    histogram=item.get('histogram'),
                    fibonacci_levels=item.get('fibonacci_levels', {})
                )
                for item in cached
            ]

        if not data or not isinstance(data, list) or len(data) == 0:
            print(f"🔴 NO DATA: {data}")
            logger.info(f"No data provided or invalid data format: {data}")
            return []

        print(f"📊 PROCESSING: {len(data)} data points for {symbol}")
        logger.info(f"Processing {len(data)} data points for {symbol}")
        print(f"📋 SAMPLE DATA: {data[:2] if len(data) > 0 else 'No data'}")
        logger.debug(f"Sample data: {data[:2] if len(data) > 0 else 'No data'}")
        
        try:
            df = pd.DataFrame(data)
            logger.info(f"DataFrame created with columns: {list(df.columns)}")
        except (ValueError, TypeError) as e:
            logger.error(f"Error creating DataFrame: {e}")
            logger.error(f"Data type: {type(data)}")
            logger.error(f"Data content: {data}")
            return []
        df = df.sort_values("t")
        
        # Log date range for debugging
        if len(df) > 0:
            first_ts = df["t"].iloc[0]
            last_ts = df["t"].iloc[-1]
            first_date = datetime.fromtimestamp(first_ts / 1000).strftime('%Y-%m-%d')
            last_date = datetime.fromtimestamp(last_ts / 1000).strftime('%Y-%m-%d')
            logger.info(f"Indicators for {symbol}: requested from {start_date} to {end_date}, got {len(df)} records from {first_date} to {last_date}")
        
        df["close"] = df["c"]
        df["timestamp"] = df["t"]

        # Validación mínima
        if len(df) < max(window, slow):
            return []

        # =====================
        # INDICADORES
        # =====================
        
        # Calculate each indicator using separate functions
        df = self._calculate_ema(df, window)
        df = self._calculate_sma(df, window)
        df = self._calculate_rsi(df, window)
        df = self._calculate_macd(df, fast, slow, signal)
        
        # Calculate Fibonacci retracement levels
        # Convert DataFrame to list of dictionaries for Fibonacci service
        data_list = df.to_dict('records')
        fibonacci_levels = await self._calculate_fibonacci_levels(data_list, symbol)
        
        # Remove rows with NaN values in indicators
        df = df.dropna(subset=["ema", "sma", "rsi", "macd", "macd_signal", "histogram"])
        
        # Convert to IndicatorDataPoint objects
        results = []
        import math
        for _, row in df.iterrows():
            # Handle NaN values
            def safe_float(value):
                if isinstance(value, float) and math.isnan(value):
                    return None
                return value
            
            point = IndicatorDataPoint(
                timestamp=int(row["t"]),
                symbol=symbol,
                ema=safe_float(row["ema"]),
                sma=safe_float(row["sma"]),
                rsi=safe_float(row["rsi"]),
                macd=safe_float(row["macd"]),
                macd_signal=safe_float(row["macd_signal"]),
                histogram=safe_float(row["histogram"]),
                close_price=safe_float(row["c"]), 
                fibonacci_levels=fibonacci_levels
            )
            results.append(point)
        
        # Cache as dictionaries for FastAPI serialization, but return objects for internal use
        cache_data = [point.model_dump() for point in results]
        print(f"DEBUG: About to call cache.set for {symbol} with {len(cache_data)} items")

        cache_result = await self.cache.set(cache_key, cache_data, ttl=60)
        print(f"DEBUG: Cache set result for {symbol}: {type(cache_result)} - {cache_result}")

        return results

    def _calculate_ema(self, df: pd.DataFrame, window: int) -> pd.DataFrame:
        """Calculate Exponential Moving Average (EMA)"""
        df["ema"] = pta.ema(df["close"], length=window)
        return df

    def _calculate_sma(self, df: pd.DataFrame, window: int) -> pd.DataFrame:
        """Calculate Simple Moving Average (SMA)"""
        df["sma"] = pta.sma(df["close"], length=window)
        return df

    def _calculate_rsi(self, df: pd.DataFrame, window: int) -> pd.DataFrame:
        """Calculate Relative Strength Index (RSI)"""
        df["rsi"] = pta.rsi(df["close"], length=window)
        return df

    def _calculate_macd(self, df: pd.DataFrame, fast: int, slow: int, signal: int) -> pd.DataFrame:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        macd = pta.macd(df['close'], fast=fast, slow=slow, signal=signal)
        
        df['macd'] = macd.iloc[:, 0]
        df['macd_signal'] = macd.iloc[:, 1]
        df['histogram'] = macd.iloc[:, 2]
        
        return df

    async def _calculate_fibonacci_levels(self, data: List[Dict], symbol: str) -> Dict[str, float]:
        """
        Calculate Fibonacci retracement levels with caching support
        
        Args:
            data: List of dictionaries with OHLC data
            symbol: Stock symbol for cache key
            
        Returns:
            Dictionary of Fibonacci levels
        """
        # Generate cache key for Fibonacci data
        if data:
            timestamps = [item['t'] for item in data]
            cache_key = f"fibonacci_{symbol}_{min(timestamps)}_{max(timestamps)}"
        else:
            cache_key = f"fibonacci_{symbol}_empty"
        
        # Try to get cached Fibonacci levels
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info(f"Using cached Fibonacci levels for {symbol}")
            # Extract levels from cached data structure
            if isinstance(cached, dict) and 'levels' in cached:
                return cached['levels']
            elif isinstance(cached, dict):
                # Direct levels dictionary
                return cached
            else:
                # Handle unexpected cache format
                logger.warning(f"Unexpected cache format for {symbol}: {type(cached)}")
                return {}
        
        # Calculate new Fibonacci levels
        fibonacci_levels, high_ts, low_ts = self.fibonacci_service.calculate_fibonacci_levels(data)
        
        if not fibonacci_levels:
            logger.warning(f"Could not calculate Fibonacci levels for {symbol}")
            return {}
        
        # Cache the result with metadata
        cache_data = {
            'levels': fibonacci_levels,
            'high_ts': high_ts,
            'low_ts': low_ts
        }
        self.cache.set(cache_key, cache_data, ttl=86400)  # 24 hours
        
        logger.info(f"Calculated Fibonacci levels for {symbol}: {list(fibonacci_levels.keys())}")
        return fibonacci_levels