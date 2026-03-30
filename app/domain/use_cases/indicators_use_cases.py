from typing import Optional, List
import pandas as pd
#import ta
import pandas_ta as pta
import logging
from datetime import datetime
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

        if not data:
            return []

        df = pd.DataFrame(data)
        df = df.sort_values("t")
        
        # Log date range for debugging
        if len(df) > 0:
            first_ts = df["t"].iloc[0]
            last_ts = df["t"].iloc[-1]
            first_date = datetime.fromtimestamp(first_ts / 1000).strftime('%Y-%m-%d')
            last_date = datetime.fromtimestamp(last_ts / 1000).strftime('%Y-%m-%d')
            logger.info(f"Indicators for {symbol}: requested from {start_date} to {end_date}, got {len(df)} records from {first_date} to {last_date}")
        
        df["close"] = df["c"]

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
        
        results = df[[
            "t", "ema", "sma", "rsi", "macd", "signal", "histogram"
        ]].to_dict(orient="records")
        
        # Replace NaN with None for JSON serialization
        import math
        for record in results:
            for key, value in record.items():
                if isinstance(value, float) and math.isnan(value):
                    record[key] = None
        
        response = results

        await self.cache.set(cache_key, response, ttl=60)

        return response