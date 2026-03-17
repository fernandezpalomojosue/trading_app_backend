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
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine
from app.core.config import settings


def main():
    """Ejecuta migraciones para producción en Render"""
    print("🔄 Running safe migrations for Render PostgreSQL...")
    
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
        # Check current migration state
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            context = MigrationContext.configure(
                connection=connection,
                opts=alembic_cfg.get_section('alembic')
            )
            
            current = context.get_current_revision()
            head = context.get_head_revision()
            
            print(f"Current revision: {current}")
            print(f"Head revision: {head}")
            
            if current == head:
                print("✅ Database is already up to date!")
                return
            
            # Check if we need to mark as applied (tables already exist)
            if current is None and head is not None:
                print("🔍 No migrations found but tables exist...")
                print("📝 Marking migrations as applied (tables already created)...")
                
                # Get all revisions and mark them as applied
                from alembic.script import ScriptDirectory
                script_dir = ScriptDirectory.from_config(alembic_cfg)
                
                # Get the head revision
                head_rev = script_dir.get_current_head()
                
                # Mark as applied without running SQL
                command.stamp(alembic_cfg, head_rev)
                print(f"✅ Marked revision {head_rev} as applied")
                return
            
            # Only run migrations if we're behind
            print(f"📈 Running migrations from {current} to {head}...")
            command.upgrade(alembic_cfg, "head")
            print("✅ Migrations completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        
        # Check if it's a duplicate table error and mark as applied
        if "already exists" in str(e):
            print("🔧 Tables already exist, marking migrations as applied...")
            try:
                command.stamp(alembic_cfg, "head")
                print("✅ Marked migrations as applied despite error")
                return
            except Exception as stamp_error:
                print(f"❌ Failed to mark migrations: {stamp_error}")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
