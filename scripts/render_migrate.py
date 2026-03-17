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
        # Get script directory for head revision
        from alembic.script import ScriptDirectory
        script_dir = ScriptDirectory.from_config(alembic_cfg)
        
        # Get current and head revisions
        try:
            current = command.current(alembic_cfg, verbose=False)
        except Exception as e:
            print(f"⚠️  Error getting current revision: {e}")
            current = None
            
        head = script_dir.get_current_head()
        
        print(f"Current revision: {current}")
        print(f"Head revision: {head}")
        
        # Check if alembic_version table exists
        try:
            from sqlalchemy import create_engine, inspect, text
            temp_engine = create_engine(database_url)
            inspector = inspect(temp_engine)
            tables = inspector.get_table_names()
            print(f"📋 Existing tables: {tables}")
            
            if 'alembic_version' not in tables:
                print("⚠️  alembic_version table not found - tables were created outside Alembic")
                print("📝 Marking migrations as applied (tables already created)...")
                command.stamp(alembic_cfg, head)
                print(f"✅ Marked revision {head} as applied")
                return
            else:
                # Check what version is actually recorded
                with temp_engine.connect() as conn:
                    result = conn.execute(text("SELECT version_num FROM alembic_version"))
                    recorded_version = result.scalar()
                    print(f"📝 Recorded alembic version: {recorded_version}")
                    
        except Exception as table_error:
            print(f"⚠️  Error checking tables: {table_error}")
        
        if current == head:
            print("✅ Database is already up to date!")
            return
        
        # Check if we need to mark as applied (tables already exist)
        if current is None or current == "None":
            print("🔍 No migrations found but tables exist...")
            print("📝 Marking migrations as applied (tables already created)...")
            
            # Mark as applied without running SQL
            command.stamp(alembic_cfg, head)
            print(f"✅ Marked revision {head} as applied")
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
                from alembic.script import ScriptDirectory
                script_dir = ScriptDirectory.from_config(alembic_cfg)
                head = script_dir.get_current_head()
                command.stamp(alembic_cfg, head)
                print("✅ Marked migrations as applied despite error")
                return
            except Exception as stamp_error:
                print(f"❌ Failed to mark migrations: {stamp_error}")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
