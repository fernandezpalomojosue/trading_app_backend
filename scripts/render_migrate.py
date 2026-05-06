#!/usr/bin/env python3
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from alembic.config import Config
from alembic import command


def main():
    print("🔄 Running migrations...")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL is required")
        sys.exit(1)

    print(f"📊 DB: {database_url.split('@')[1]}")

    alembic_ini_path = Path(__file__).parent.parent / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini_path))

    try:
        # Check for multiple heads first
        print("🔍 Checking migration heads...")
        from alembic.command import heads
        head_revisions = heads(alembic_cfg)
        
        if len(head_revisions) > 1:
            print(f"⚠️  Found {len(head_revisions)} migration heads, merging...")
            from alembic.command import merge
            revision_ids = [rev.revision for rev in head_revisions]
            merge_revision = merge(alembic_cfg, *revision_ids, message="Auto-merge multiple heads")
            print(f"✅ Created merge migration: {merge_revision.revision}")
        
        # Now run the upgrade
        print("🚀 Applying migrations...")
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrations applied successfully!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        
        # Provide helpful error message for common issues
        if "Multiple head revisions" in str(e):
            print("💡 Tip: Try running 'alembic merge heads' first")
        elif "SSL connection" in str(e):
            print("💡 Tip: Check database connectivity and SSL configuration")
        elif "connection" in str(e).lower():
            print("💡 Tip: Verify DATABASE_URL and network connectivity")
            
        sys.exit(1)


if __name__ == "__main__":
    main()