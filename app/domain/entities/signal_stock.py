from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone


class SignalStockEntity(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    symbol: str = Field(description="Stock symbol (e.g., AAPL, GOOGL)")
    signal: str = Field(description="Signal type: BUY, SELL, or HOLD")
    stop_loss: float = Field(description="Stop loss price")
    take_profit: float = Field(description="Take profit price")
    confidence: float = Field(description="Confidence level (0-1)")
    reason: str = Field(description="Reason for the signal")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Update timestamp")