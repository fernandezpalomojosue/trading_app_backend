from typing import Optional, List
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

logger = logging.getLogger(__name__)


class IndicatorsUseCases(IndicatorsService):

    def __init__(self, cache_service):
        self.cache = cache_service

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

        cached = await self.cache.get(cache_key)
        if cached:
            return cached

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

        df["ema"] = pta.ema(df["close"], length=window)
        df["sma"] = pta.sma(df["close"], length=window)
        df["rsi"] = pta.rsi(df["close"], length=window)

        macd = pta.macd(df['close'], fast=fast, slow=slow, signal=signal)

        df['macd'] = macd.iloc[:, 0]
        df['signal'] = macd.iloc[:, 1]
        df['histogram'] = macd.iloc[:, 2]

        df = df.dropna(subset=["ema", "sma", "rsi", "macd", "signal", "histogram"])
        
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
                timestamp=int(row["timestamp"]),
                symbol=symbol,
                ema=safe_float(row["ema"]),
                sma=safe_float(row["sma"]),
                rsi=safe_float(row["rsi"]),
                macd=safe_float(row["macd"]),
                signal=safe_float(row["signal"]),
                histogram=safe_float(row["histogram"]),
                fibonacci_levels={}
            )
            results.append(point)
        
        response = results

        await self.cache.set(cache_key, response, ttl=60)

        return response