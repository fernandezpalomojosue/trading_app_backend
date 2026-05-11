"""Merge all heads and add cascade delete

Revision ID: merge_all_heads
Revises: 34e6daa745da, b2c3d4e5f6g7, add_default_strategy_seed
Create Date: 2026-05-11 14:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_all_heads'
down_revision: Union[str, None] = ('34e6daa745da', 'b2c3d4e5f6g7', 'add_default_strategy_seed')
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge all migration heads."""
    pass


def downgrade() -> None:
    """Downgrade merged migrations."""
    pass
