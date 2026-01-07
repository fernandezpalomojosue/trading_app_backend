# app/services/polygon/config.py
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener la API key
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

# Exportar la variable
__all__ = ['POLYGON_API_KEY']