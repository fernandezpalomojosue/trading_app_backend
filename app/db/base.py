# app/db/base.py
from sqlmodel import SQLModel, create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Crear el motor de la base de datos
engine = create_engine(
    settings.DATABASE_URL,
    echo=True,  # Muestra las consultas SQL en la consola
    pool_pre_ping=True,  # Verifica la conexión antes de usarla
    pool_recycle=300,  # Recicla las conexiones cada 5 minutos
)

# Crear la sesión local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    with SessionLocal() as session:
        yield session

def create_db_and_tables():
    """Crea todas las tablas definidas en los modelos SQLModel."""
    from sqlmodel import SQLModel
    from app.models.user import User  # Importar para que SQLModel lo registre
    
    print("Creando tablas en la base de datos...")
    SQLModel.metadata.create_all(engine)
    print("¡Tablas creadas exitosamente!")