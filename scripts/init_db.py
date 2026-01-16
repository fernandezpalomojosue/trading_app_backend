#!/usr/bin/env python3
"""
Script para inicializar la base de datos.
Uso: python scripts/init_db.py
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import create_db_and_tables
from app.core.config import settings

def main():
    """Inicializar las tablas de la base de datos."""
    print(f"Inicializando base de datos para entorno: {settings.ENVIRONMENT}")
    print(f"Database URL: {settings.DATABASE_URL}")
    
    try:
        create_db_and_tables()
        print("✅ Tablas creadas exitosamente")
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
