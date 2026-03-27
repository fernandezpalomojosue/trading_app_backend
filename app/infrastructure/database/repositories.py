# app/infrastructure/database/repositories.py
from typing import Optional, List
from uuid import UUID
from sqlmodel import Session, select
from datetime import datetime, timezone

from app.domain.entities.user import UserEntity
from app.domain.use_cases.user_use_cases import UserRepository
from app.infrastructure.database.models import UserSQLModel, FavoriteStockSQLModel
from app.domain.repositories.favorite_stock_repository import FavoriteStockRepository
from app.domain.entities.favorite_stock import FavoriteStockEntity


class SQLUserRepository(UserRepository):
    
    def __init__(self, session: Session):
        self.session = session
    
    async def create_user(self, user: UserEntity, hashed_password: str) -> UserEntity:
        """Create a new user in the database"""
        user_model = UserSQLModel.from_domain_entity(user)
        user_model.hashed_password = hashed_password
        
        self.session.add(user_model)
        self.session.commit()
        self.session.refresh(user_model)
        
        return user_model.to_domain_entity()
    
    async def get_user_by_email(self, email: str) -> Optional[UserEntity]:
        """Get user by email"""
        statement = select(UserSQLModel).where(UserSQLModel.email == email)
        user_model = self.session.exec(statement).first()
        
        if user_model:
            return user_model.to_domain_entity()
        return None
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[UserEntity]:
        """Get user by ID"""
        statement = select(UserSQLModel).where(UserSQLModel.id == user_id)
        user_model = self.session.exec(statement).first()
        
        if user_model:
            return user_model.to_domain_entity()
        return None
    
    async def update_user(self, user: UserEntity) -> UserEntity:
        """Update user in database"""
        statement = select(UserSQLModel).where(UserSQLModel.id == user.id)
        user_model = self.session.exec(statement).first()
        
        if not user_model:
            raise ValueError("User not found")
        
        # Update fields
        user_model.username = user.username
        user_model.full_name = user.full_name
        user_model.is_active = user.is_active
        user_model.is_verified = user.is_verified
        user_model.is_superuser = user.is_superuser
        user_model.balance = user.balance
        user_model.updated_at = user.updated_at
        
        self.session.commit()
        self.session.refresh(user_model)
        
        return user_model.to_domain_entity()
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Delete user from database"""
        statement = select(UserSQLModel).where(UserSQLModel.id == user_id)
        user_model = self.session.exec(statement).first()
        
        if user_model:
            self.session.delete(user_model)
            self.session.commit()
            return True
        return False
    
    async def user_exists(self, email: str) -> bool:
        """Check if user exists by email"""
        statement = select(UserSQLModel).where(UserSQLModel.email == email)
        user_model = self.session.exec(statement).first()
        return user_model is not None
    
    async def verify_password(self, email: str, password: str) -> bool:
        """Verify user password"""
        user_model = self.get_user_with_password(email)
        if not user_model:
            return False
        
        from app.infrastructure.security.password_service import PasslibPasswordService
        password_service = PasslibPasswordService()
        return password_service.verify_password(password, user_model.hashed_password)
    
    def get_user_with_password(self, email: str) -> Optional[UserSQLModel]:
        """Get user model with password (for authentication)"""
        statement = select(UserSQLModel).where(UserSQLModel.email == email)
        return self.session.exec(statement).first()


# Portfolio Repository Implementation
from app.domain.use_cases.portfolio_use_cases import PortfolioRepository
from app.domain.entities.portfolio import PortfolioHolding, Transaction
from app.infrastructure.database.models import PortfolioHoldingSQLModel, TransactionSQLModel


class SQLPortfolioRepository(PortfolioRepository):
    
    def __init__(self, session: Session):
        self.session = session
    
    async def get_user_holdings(self, user_id: UUID) -> List[PortfolioHolding]:
        """Get all holdings for a user"""
        statement = select(PortfolioHoldingSQLModel).where(PortfolioHoldingSQLModel.user_id == user_id)
        holdings_models = self.session.exec(statement).all()
        
        holdings = []
        for model in holdings_models:
            holding = PortfolioHolding(
                id=model.id,
                user_id=model.user_id,
                symbol=model.symbol,
                quantity=model.quantity,
                average_price=model.average_price,
                current_price=model.current_price,
                total_value=model.total_value,
                unrealized_pnl=model.unrealized_pnl,
                pnl_percentage=model.pnl_percentage,
                created_at=model.created_at,
                updated_at=model.updated_at
            )
            holdings.append(holding)
        
        return holdings
    
    async def get_user_transactions(self, user_id: UUID) -> List[Transaction]:
        """Get all transactions for a user"""
        statement = select(TransactionSQLModel).where(TransactionSQLModel.user_id == user_id).order_by(TransactionSQLModel.created_at.desc())
        transaction_models = self.session.exec(statement).all()
        
        transactions = []
        for model in transaction_models:
            transaction = Transaction(
                id=model.id,
                user_id=model.user_id,
                symbol=model.symbol,
                transaction_type=model.transaction_type,
                quantity=model.quantity,
                price=model.price,
                total_amount=model.total_amount,
                created_at=model.created_at
            )
            transactions.append(transaction)
        
        return transactions
    
    async def get_holding_by_symbol(self, user_id: UUID, symbol: str) -> Optional[PortfolioHolding]:
        """Get holding by symbol for a user"""
        statement = select(PortfolioHoldingSQLModel).where(
            PortfolioHoldingSQLModel.user_id == user_id,
            PortfolioHoldingSQLModel.symbol == symbol
        )
        model = self.session.exec(statement).first()
        
        if not model:
            return None
        
        return PortfolioHolding(
            id=model.id,
            user_id=model.user_id,
            symbol=model.symbol,
            quantity=model.quantity,
            average_price=model.average_price,
            current_price=model.current_price,
            total_value=model.total_value,
            unrealized_pnl=model.unrealized_pnl,
            pnl_percentage=model.pnl_percentage,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    async def create_holding(self, holding: PortfolioHolding) -> PortfolioHolding:
        """Create a new holding"""
        holding_model = PortfolioHoldingSQLModel(
            id=holding.id,
            user_id=holding.user_id,
            symbol=holding.symbol,
            quantity=holding.quantity,
            average_price=holding.average_price,
            current_price=holding.current_price,
            total_value=holding.total_value,
            unrealized_pnl=holding.unrealized_pnl,
            pnl_percentage=holding.pnl_percentage,
            created_at=holding.created_at,
            updated_at=holding.updated_at
        )
        
        self.session.add(holding_model)
        self.session.commit()
        self.session.refresh(holding_model)
        
        return holding
    
    async def update_holding(self, holding: PortfolioHolding) -> PortfolioHolding:
        """Update an existing holding"""
        statement = select(PortfolioHoldingSQLModel).where(PortfolioHoldingSQLModel.id == holding.id)
        holding_model = self.session.exec(statement).first()
        
        if holding_model:
            holding_model.quantity = holding.quantity
            holding_model.average_price = holding.average_price
            holding_model.current_price = holding.current_price
            holding_model.total_value = holding.total_value
            holding_model.unrealized_pnl = holding.unrealized_pnl
            holding_model.pnl_percentage = holding.pnl_percentage
            holding_model.updated_at = holding.updated_at
            
            self.session.commit()
            self.session.refresh(holding_model)
        
        return holding
    
    async def delete_holding(self, holding_id: UUID) -> bool:
        """Delete a holding"""
        statement = select(PortfolioHoldingSQLModel).where(PortfolioHoldingSQLModel.id == holding_id)
        holding_model = self.session.exec(statement).first()
        
        if holding_model:
            self.session.delete(holding_model)
            self.session.commit()
            return True
        
        return False

    async def is_a_holding(self, user_id: UUID, symbol: str) ->bool:
        statement = select(PortfolioHoldingSQLModel).where(PortfolioHoldingSQLModel.user_id == user_id, PortfolioHoldingSQLModel.symbol == symbol)
        holding_model = self.session.exec(statement).first()
        
        return holding_model is not None
    
    async def create_transaction(self, transaction: Transaction) -> Transaction:
        """Create a new transaction"""
        transaction_model = TransactionSQLModel(
            id=transaction.id,
            user_id=transaction.user_id,
            symbol=transaction.symbol,
            transaction_type=transaction.transaction_type,
            quantity=transaction.quantity,
            price=transaction.price,
            total_amount=transaction.total_amount,
            created_at=transaction.created_at
        )
        
        self.session.add(transaction_model)
        self.session.commit()
        self.session.refresh(transaction_model)
        
        return transaction
    
    async def update_user_balance(self, user_id: UUID, new_balance: float) -> bool:
        """Update user balance"""
        statement = select(UserSQLModel).where(UserSQLModel.id == user_id)
        user_model = self.session.exec(statement).first()
        
        if user_model:
            user_model.balance = new_balance
            user_model.updated_at = datetime.now(timezone.utc)
            self.session.commit()
            return True
        
        return False
    
    async def get_user_balance(self, user_id: UUID) -> float:
        """Get user balance"""
        statement = select(UserSQLModel).where(UserSQLModel.id == user_id)
        user_model = self.session.exec(statement).first()
        
        if user_model:
            return user_model.balance
        
        return 0.0


# Favorite Stock Repository Implementation
class SQLFavoriteStockRepository(FavoriteStockRepository):
    
    def __init__(self, session: Session):
        self.session = session
    
    async def add_favorite(self, user_id: UUID, symbol: str) -> FavoriteStockEntity:
        """Add a stock to user's favorites"""
        # Check if already exists
        existing = await self.get_favorite_by_user_and_symbol(user_id, symbol)
        if existing:
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
    
    async def get_favorite_by_user_and_symbol(self, user_id: UUID, symbol: str) -> Optional[FavoriteStockSQLModel]:
        """Get specific favorite by user and symbol"""
        statement = select(FavoriteStockSQLModel).where(
            FavoriteStockSQLModel.user_id == user_id,
            FavoriteStockSQLModel.symbol == symbol.upper()
        )
        return self.session.exec(statement).first()