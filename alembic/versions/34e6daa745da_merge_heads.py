"""merge heads

Revision ID: 34e6daa745da
Revises: 16e47539e731, a1b2c3d4e5f6
Create Date: 2026-04-30 16:09:22.972523

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '34e6daa745da'
down_revision: Union[str, None] = ('16e47539e731', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
