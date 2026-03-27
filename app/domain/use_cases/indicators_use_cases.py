from typing import Optional
import pandas as pd
#import ta
import pandas_ta as pta
import logging
from datetime import datetime
from app.application.dto.indicators_dto import CombinedIndicatorsResponse
from app.application.services.indicators_service import IndicatorsService
from app.domain.use_cases.signal_engine_use_cases import SignalEngineUseCases
from app.infrastructure.external.market_client import PolygonMarketClient

logger = logging.getLogger(__name__)


class IndicatorsUseCases(IndicatorsService):

    def __init__(self, market_client: PolygonMarketClient, cache_service, signal_engine: Optional[SignalEngineUseCases] = None):
        self.market_client = market_client
        self.cache = cache_service
        self.signal_engine = signal_engine or SignalEngineUseCases()

    async def get_indicators(
        self,
        symbol: str,
        window: int,
        fast: int,
        slow: int,
        signal: int,
        timespan: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> CombinedIndicatorsResponse:

        cache_key = f"indicators_{symbol}_{window}_{fast}_{slow}_{signal}_{timespan}_{start_date}_{end_date}"

        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        raw_data = await self.market_client.fetch_candlestick_data(
            symbol,
            timespan=timespan,
            multiplier=1,
            start_date=start_date,
            end_date=end_date,
            limit=5000
        )

        if not raw_data:
            return CombinedIndicatorsResponse(symbol=symbol, results=[])

        df = pd.DataFrame(raw_data)
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
            return CombinedIndicatorsResponse(symbol=symbol, results=[])

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

        # Prepare data for signal calculation
        signal_data = df[["rsi", "macd", "signal", "ema", "close"]].to_dict(orient="records")
        
        # Calculate trading signals (returns tuples of signal and reason)
        signal_results = self.signal_engine.calculate_signals(signal_data)
        
        results = df[[
            "t", "ema", "sma", "rsi", "macd", "signal", "histogram"
        ]].to_dict(orient="records")
        
        # Add signals and reasons to results
        for i, (signal, reason) in enumerate(signal_results):
            if i < len(results):
                results[i]["order_signal"] = signal
                results[i]["signal_reason"] = reason
        
        # Replace NaN with None for JSON serialization
        import math
        for record in results:
            for key, value in record.items():
                if isinstance(value, float) and math.isnan(value):
                    record[key] = None
        
        response = CombinedIndicatorsResponse(
            symbol=symbol,
            results=results
        )

        await self.cache.set(cache_key, response.model_dump(), ttl=60)

        return response