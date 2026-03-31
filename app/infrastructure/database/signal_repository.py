from sqlmodel import Session
from app.application.dto.signals_dto import SignalDataPoint
from app.application.repositories.signal_repository import SignalRepository
from app.domain.entities.signal_stock import SignalStockEntity
from app.infrastructure.database.models import SignalStockSQLModel

class SQLSignalRepository(SignalRepository):
    
    def __init__(self, session: Session):
        self.session = session
    
    async def save_signal(self, symbol: str, signal: SignalDataPoint) -> SignalStockEntity:
        """Save a signal for a symbol"""
        signal_model = SignalStockSQLModel(
            symbol=symbol,
            signal=signal.signal,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            confidence=signal.confidence,
            reason=signal.reason
        )
        self.session.add(signal_model)
        self.session.commit()
        self.session.refresh(signal_model)
        return SignalStockEntity(
            id=signal_model.id,
            symbol=signal_model.symbol,
            signal=signal_model.signal,
            stop_loss=signal_model.stop_loss,
            take_profit=signal_model.take_profit,
            confidence=signal_model.confidence,
            reason=signal_model.reason
        )
    
    async def get_by_symbol(self, symbol: str) -> SignalStockEntity:
        """Get signal by symbol"""
        signal_model = self.session.get(SignalStockSQLModel, symbol)
        if signal_model:
            return SignalStockEntity(
                id=signal_model.id,
                symbol=signal_model.symbol,
                signal=signal_model.signal,
                stop_loss=signal_model.stop_loss,
                take_profit=signal_model.take_profit,
                confidence=signal_model.confidence,
                reason=signal_model.reason
            )
        return None
        