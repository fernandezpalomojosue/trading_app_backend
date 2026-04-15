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
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrations applied successfully!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()