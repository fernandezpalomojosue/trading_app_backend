from typing import Optional
import pandas as pd
import ta
from app.application.services.indicators_service import IndicatorsService
from app.infrastructure.external.market_client import PolygonMarketClient


class IndicatorsUseCases(IndicatorsService):

    def __init__(self, market_client: PolygonMarketClient, cache_service):
        self.market_client = market_client
        self.cache = cache_service

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
    ) -> dict:

        cache_key = f"indicators_{symbol}_{window}_{fast}_{slow}_{signal}_{timespan}_{start_date}_{end_date}_{limit}"

        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        raw_data = await self.market_client.fetch_candlestick_data(
            symbol,
            timespan=timespan,
            multiplier=1,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        if not raw_data:
            return {"symbol": symbol, "results": []}

        df = pd.DataFrame(raw_data)
        df = df.sort_values("t")
        df["close"] = df["c"]

        # Validación mínima
        if len(df) < max(window, slow):
            return {"symbol": symbol, "results": []}

        # =====================
        # INDICADORES
        # =====================

        df["ema"] = ta.trend.EMAIndicator(df["close"], window=window).ema_indicator()
        df["sma"] = ta.trend.SMAIndicator(df["close"], window=window).sma_indicator()
        df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=window).rsi()

        macd = ta.trend.MACD(
            df["close"],
            window_fast=fast,
            window_slow=slow,
            window_sign=signal
        )

        df["macd"] = macd.macd()
        df["signal"] = macd.macd_signal()
        df["histogram"] = macd.macd_diff()

        df = df.dropna(subset=["ema", "sma", "rsi", "macd"])

        results = df[[
            "t", "ema", "sma", "rsi", "macd", "signal", "histogram"
        ]].to_dict(orient="records")

        response = {
            "symbol": symbol,
            "results": results
        }

        await self.cache.set(cache_key, response, ttl=60)

        return response