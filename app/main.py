# app/main.py
from fastapi import FastAPI
from app.db.base import create_db_and_tables
from app.api.v1.endpoints.routers import api_router

app = FastAPI(
    title="Trading App API",
    description="API para la aplicación de trading",
    version="0.1.0"
)

# Incluir routers
app.include_router(api_router, prefix="/api/v1")

# Crear tablas al iniciar la aplicación
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
async def root():
    return {"message": "Bienvenido a la API de Trading"}