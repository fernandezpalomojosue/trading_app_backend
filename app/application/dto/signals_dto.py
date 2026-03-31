#app/application/dto/signals_dto.py
from typing import Optional
from pydantic import BaseModel

class SignalDataPoint(BaseModel):
    timestamp: int
    symbol: str
    signal: Optional[str] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    confidence: Optional[float] = None
    reason: Optional[str] = None