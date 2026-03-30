# app/domain/entities/favorite_stock.py
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field, validator
import re


class FavoriteStockEntity(BaseModel):
    """Core favorite stock entity - pure business logic"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(description="User ID who owns this favorite")
    symbol: str = Field(description="Stock symbol (e.g., AAPL, GOOGL)")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Date when stock was added to favorites"
    )
    
    @validator('symbol')
    def symbol_must_be_valid(cls, v):
        """Validate stock symbol format"""
        if not v:
            raise ValueError("Symbol cannot be empty")
        
        # Convert to uppercase and validate format
        symbol = v.upper().strip()
        
        # Basic stock symbol validation (1-5 characters, letters only)
        if not re.match(r'^[A-Z]{1,5}$', symbol):
            raise ValueError("Symbol must be 1-5 uppercase letters")
        
        return symbol
    
    def update_timestamp(self):
        """Update the created_at timestamp"""
        self.created_at = datetime.now(timezone.utc)
    
    def belongs_to_user(self, user_id: uuid.UUID) -> bool:
        """Check if favorite belongs to specific user"""
        return self.user_id == user_id
