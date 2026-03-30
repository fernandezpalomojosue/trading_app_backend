from sqlmodel import Session
from app.application.repositories.signal_repository import SignalRepository
from app.domain.entities.signal_stock import SignalStockEntity
from app.infrastructure.database.models import SignalStockSQLModel

class SQLSignalRepository(SignalRepository):
    
    def __init__(self, session: Session):
        self.session = session
    
    async def save_signal(self, symbol: str, signal: dict) -> SignalStockEntity:
        """Save a signal for a symbol"""
        signal_model = SignalStockSQLModel(
            symbol=symbol,
            signal=signal.get("signal"),
            stop_loss=signal.get("stop_loss"),
            take_profit=signal.get("take_profit"),
            confidence=signal.get("confidence"),
            reason=signal.get("reason")
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
        