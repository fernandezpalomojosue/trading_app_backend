from app.application.repositories.market_repository import MarketRepository
from app.application.services.indicators_service import IndicatorsService
from app.application.services.signal_engine_service import SignalEngineService
from app.application.repositories.signal_repository import SignalRepository
from app.application.repositories.cache_repository import CacheRepository

class SignalOrchestrator:
    """Orchestrates the signal generation process"""
    
    def __init__(self, market_client: MarketRepository, indicator_service: IndicatorsService, signal_engine_service: SignalEngineService, cache_client: CacheRepository, signal_repository: SignalRepository):
        self.market_client = market_client
        self.indicator_service = indicator_service
        self.signal_engine_service = signal_engine_service
        self.cache_client = cache_client
        self.signal_repository = signal_repository
    async def generate_signal(self, symbol: str, timespan: str, start_date: str, end_date: str, indicators_window=30, indicators_fast=12, indicators_slow=26, indicators_signal=9):
        print(f"DEBUG: Starting generate_signal for {symbol}")
        
        print(f"DEBUG: About to call market_client.fetch_candlestick_data for {symbol}")
        data = await self.market_client.fetch_candlestick_data(symbol, timespan, 1, 100, start_date, end_date)
        print(f"DEBUG: Successfully got candlestick data for {symbol}: {len(data)} records")

        print(f"DEBUG: About to call indicator_service.get_indicators for {symbol}")
        indicators = await self.indicator_service.get_indicators(symbol, data=data, window=indicators_window, fast=indicators_fast, slow=indicators_slow, signal=indicators_signal, timespan=timespan, start_date=start_date, end_date=end_date, limit=100)
        print(f"DEBUG: Successfully got indicators for {symbol}: {len(indicators)} indicators")
        
        print(f"DEBUG: About to call signal_engine_service.calculate_signals for {symbol}")
        signals = self.signal_engine_service.calculate_single_signal(symbol, indicators[-1],indicators[-2])
        print(f"DEBUG: Successfully calculated signals for {symbol}: {len(signals)} signals")

        last_signal = signals[-1]
        print(f"DEBUG: Got last signal for {symbol}: {last_signal}")
        
        print(f"DEBUG: About to call signal_repository.save_signal for {symbol}")
        self.signal_repository.save_signal(symbol, last_signal)
        print(f"DEBUG: Successfully saved signal to database for {symbol}")

        print(f"DEBUG: About to call cache_client.set for {symbol}")
        cache_result = await self.cache_client.set(f"signal_{symbol}", last_signal, ttl=60)
        print(f"DEBUG: Cache set result for {symbol}: {cache_result}")
        if cache_result is not True:
            print(f"Warning: Failed to cache signal for {symbol}")
        
        print(f"DEBUG: Completed generate_signal for {symbol}")
        return last_signal
        