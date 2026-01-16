# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.base import create_db_and_tables, engine
from app.api.v1.endpoints.routers import api_router
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if settings.ENVIRONMENT == "development":
        create_db_and_tables()
    yield
    # Shutdown
    engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Incluir routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Bienvenido a la API de Trading"}