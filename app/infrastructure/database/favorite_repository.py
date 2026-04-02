# app/infrastructure/database/favorite_repository.py
from typing import List, Optional
from uuid import UUID
from sqlmodel import Session, select

from app.application.repositories.favorite_repository import FavoriteRepository
from app.domain.entities.favorite_stock import FavoriteStockEntity
from app.infrastructure.database.models import FavoriteStockSQLModel


class SQLFavoriteStockRepository(FavoriteRepository):
    
    def __init__(self, session: Session):
        self.session = session
    
    async def add_favorite(self, user_id: UUID, symbol: str) -> FavoriteStockEntity:
        """Add a stock to user's favorites"""
        # Check if already exists
        existing = await self.get_user_favorites(user_id)
        if any(f.symbol == symbol.upper() for f in existing):
            raise ValueError(f"Stock {symbol} is already in favorites")
        
        favorite_entity = FavoriteStockEntity(
            user_id=user_id,
            symbol=symbol.upper()
        )
        
        favorite_model = FavoriteStockSQLModel.from_domain_entity(favorite_entity)
        
        self.session.add(favorite_model)
        self.session.commit()
        self.session.refresh(favorite_model)
        
        return favorite_model.to_domain_entity()
    
    async def remove_favorite(self, user_id: UUID, symbol: str) -> Optional[FavoriteStockEntity]:
        """Remove a stock from user's favorites"""
        favorite_model = await self.get_favorite_by_user_and_symbol(user_id, symbol)
        
        if favorite_model:
            self.session.delete(favorite_model)
            self.session.commit()
            return favorite_model.to_domain_entity()
        
        return None
    
    async def get_user_favorites(self, user_id: UUID) -> List[FavoriteStockEntity]:
        """Get all favorite stocks for a user"""
        statement = select(FavoriteStockSQLModel).where(
            FavoriteStockSQLModel.user_id == user_id
        ).order_by(FavoriteStockSQLModel.created_at.desc())
        
        favorite_models = self.session.exec(statement).all()
        
        favorites = []
        for model in favorite_models:
            favorites.append(model.to_domain_entity())
        
        return favorites
    
    async def is_favorite(self, user_id: UUID, symbol: str) -> bool:
        """Check if a stock is in user's favorites"""
        favorite = await self.get_favorite_by_user_and_symbol(user_id, symbol)
        return favorite is not None
    

    
    async def get_all_favorites(self) -> List[str]:
        """Get all unique favorite symbols from all users"""
        statement = select(FavoriteStockSQLModel.symbol).distinct()
        symbols = self.session.exec(statement).all()
        return [symbol.upper() for symbol in symbols]
