"""Merge execution_plans and strategy_id migrations

Revision ID: 3e2001dc7b6b
Revises: 34e6daa745da, b2c3d4e5f6g7
Create Date: 2026-05-06 12:05:37.342042

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e2001dc7b6b'
down_revision: Union[str, None] = ('34e6daa745da', 'b2c3d4e5f6g7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
