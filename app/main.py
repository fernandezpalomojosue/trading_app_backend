# app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import create_db_and_tables, engine
from app.api.v1.endpoints.routers import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de vida de la aplicación.
    - Startup: crea tablas si no existen (idempotente)
    - Shutdown: cierra conexiones
    """
    print(f"Starting app in {settings.ENVIRONMENT} mode...")
    create_db_and_tables()
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
@app.get("/health", tags=["Health"])
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
