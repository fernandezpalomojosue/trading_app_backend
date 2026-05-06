# app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import create_db_and_tables, engine
from app.presentation.api.v1.endpoints.routers import api_router
from app.core.logging_config import get_logger
from sqlalchemy import inspect

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de vida de la aplicación.
    - Startup: crea tablas si no existen (verificación automática)
    - Shutdown: cierra conexiones
    """
    logger.info(
        "Application startup initiated",
        component="main",
        environment=settings.ENVIRONMENT
    )
    
    # Check if tables exist, create if missing
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    required_tables = [
        "users", "strategies", "signals", "favorite_stocks",
        "user_sessions", "market_data", "indicators_cache"
    ]
    
    missing_tables = [table for table in required_tables if table not in existing_tables]
    
    if missing_tables:
        logger.warning(
            "Missing database tables detected",
            component="main",
            missing_tables=missing_tables,
            required_tables=required_tables
        )
        logger.info(
            "Creating database tables",
            component="main",
            tables_to_create=missing_tables
        )
        create_db_and_tables()
        logger.info(
            "Database tables created successfully",
            component="main",
            created_tables=missing_tables
        )
    else:
        logger.info(
            "All required database tables exist",
            component="main",
            existing_tables=existing_tables
        )
    
    yield
    
    logger.info(
        "Application shutdown initiated",
        component="main"
    )
    engine.dispose()
    logger.info(
        "Application shutdown completed",
        component="main"
    )


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