#!/usr/bin/env python3
"""
Script para ejecutar migraciones en Render PostgreSQL
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from alembic.config import Config
from alembic import command


def main():
    """Ejecuta migraciones para producción en Render"""
    print("🔄 Running migrations for Render PostgreSQL...")
    
    # Verificar variables de entorno
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable is required")
        sys.exit(1)
    
    print(f"📊 Database URL: {database_url.split('@')[1] if '@' in database_url else 'Local'}")
    
    # Get alembic.ini path
    alembic_ini_path = Path(__file__).parent.parent / "alembic.ini"
    
    # Create Alembic config
    alembic_cfg = Config(str(alembic_ini_path))
    
    try:
        # Verificar estado actual
        print("🔍 Checking current migration status...")
        command.current(alembic_cfg)
        
        # Run migrations
        print("⬆️  Applying migrations...")
        command.upgrade(alembic_cfg, "head")
        
        # Verificar estado final
        print("✅ Migration status after upgrade:")
        command.current(alembic_cfg)
        
        print("✅ Migrations completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
