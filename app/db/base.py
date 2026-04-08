# app/db/base.py
from sqlmodel import SQLModel,Session,create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.core.config import settings
from app.infrastructure.database.models import (
    UserSQLModel,
    PortfolioHoldingSQLModel, 
    TransactionSQLModel,
    FavoriteStockSQLModel,
    SignalStockSQLModel
)     
from sqlalchemy.orm import sessionmaker

# Para compatibilidad con Alembic
Base = SQLModel.metadata

# Crear el motor de la base de datos
engine = create_engine(
    settings.get_database_url(),  # Use the dynamic database URL
    echo=settings.ECHO_SQL,  # Controlado por configuración
    pool_pre_ping=True,  # Verifica la conexión antes de usarla
    pool_recycle=300,  # Recicla las conexiones cada 5 minutos
)

# Crear el motor de la base de datos asíncrono (para la app)
async_engine = create_async_engine(
    settings.get_database_url().replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.ECHO_SQL,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Crear la sesión local asíncrona
AsyncSessionLocal = sessionmaker(
    class_=AsyncSession, 
    autocommit=False, 
    autoflush=False, 
    bind=async_engine
)

# Mantener la sesión síncrona para compatibilidad
SessionLocal = sessionmaker(class_=Session, autocommit=False, autoflush=False, bind=engine)

from contextlib import asynccontextmanager

@asynccontextmanager
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session

def create_db_and_tables():
    """
    Crea todas las tablas definidas en los modelos SQLModel.
    Solo debe usarse en desarrollo/testing. En producción usar Alembic.
    """
    print("🔧 Creating tables in database (development/testing mode)...")
    
    try:
        # Check if tables already exist before creating
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        print(f"📋 Existing tables: {existing_tables}")
        
        # create_all() is safe - it only creates tables that don't exist
        SQLModel.metadata.create_all(engine)
        
        # Verify tables were created
        new_tables = [t for t in inspector.get_table_names() if t not in existing_tables]
        if new_tables:
            print(f"✅ Created new tables: {new_tables}")
        else:
            print("✅ All tables already exist - no changes made")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise