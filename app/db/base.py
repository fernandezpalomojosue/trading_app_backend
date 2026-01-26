# app/db/base.py
from sqlmodel import SQLModel,Session,create_engine
from app.core.config import settings
from app.infrastructure.database.models import UserSQLModel     
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

# Crear la sesión local
SessionLocal = sessionmaker(class_=Session, autocommit=False, autoflush=False, bind=engine)

def get_session():
    with SessionLocal() as session:
        yield session

def create_db_and_tables():
    """Crea todas las tablas definidas en los modelos SQLModel."""
    
    print("Creando tablas en la base de datos...")
    SQLModel.metadata.create_all(engine)
    print("¡Tablas creadas exitosamente!")