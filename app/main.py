# app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import create_db_and_tables, engine
from app.presentation.api.v1.endpoints.routers import api_router
from sqlalchemy import inspect


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de vida de la aplicación.
    - Startup: crea tablas si no existen (verificación automática)
    - Shutdown: cierra conexiones
    """
    print(f"Starting app in {settings.ENVIRONMENT} mode...")
    
    # Check if tables exist, create if missing
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    required_tables = ['users', 'portfolio_holdings', 'transactions']
    
    missing_tables = [table for table in required_tables if table not in existing_tables]
    
    if missing_tables:
        print(f"Missing tables detected: {missing_tables}")
        print("Creating tables...")
        create_db_and_tables()
        print("Tables created successfully!")
    else:
        print(f"All required tables exist: {required_tables}")
    
    yield
    print("Shutting down app...")
    engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
)

# ==============================
# CORS
# ==============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.cors_allow_methods_list,
    allow_headers=settings.cors_allow_headers_list,
)

# ==============================
# Routers
# ==============================
app.include_router(api_router, prefix=settings.API_V1_STR)

# ==============================
# Healthcheck
# ==============================
@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}

# ==============================
# Root
# ==============================
@app.get("/")
async def root():
    return {
        "message": "Bienvenido a la API de Trading",
        "environment": settings.ENVIRONMENT,
    }