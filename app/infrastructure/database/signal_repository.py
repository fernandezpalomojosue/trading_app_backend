from typing import Optional
from uuid import UUID
from sqlmodel import Session, select
from app.application.dto.signals_dto import SignalDataPoint
from app.application.repositories.signal_repository import SignalRepository
from app.domain.entities.signal_stock import SignalStockEntity
from app.infrastructure.database.models import SignalStockSQLModel

class SQLSignalRepository(SignalRepository):
    
    def __init__(self, session: Session):
        self.session = session
    
    async def save_signal(
        self, 
        symbol: str, 
        signal: SignalDataPoint,
        strategy_id: Optional[UUID] = None
    ) -> SignalStockEntity:
        """Save a signal for a symbol"""
        signal_model = SignalStockSQLModel(
            symbol=symbol,
            signal=signal.signal,
            stop_loss=signal.stop_loss or 0.0,
            take_profit=signal.take_profit or 0.0,
            confidence=signal.confidence or 0.0,
            reason=signal.reason or "",
            strategy_id=strategy_id or signal.strategy_id
        )
        # Let the default_factory handle created_at without timezone
        self.session.add(signal_model)
        self.session.commit()
        self.session.refresh(signal_model)
        return signal_model.to_domain_entity()
    
    async def get_by_symbol(self, symbol: str) -> Optional[SignalStockEntity]:
        """Get signal by symbol"""
        signal_model = self.session.exec(
            select(SignalStockSQLModel)
            .where(SignalStockSQLModel.symbol == symbol)
            .order_by(SignalStockSQLModel.created_at.desc())
        ).first()
        if signal_model:
            return signal_model.to_domain_entity()
        return None
        