"""merge execution plans and default strategy seed

Revision ID: 37de92450a32
Revises: 3e2001dc7b6b, add_default_strategy_seed
Create Date: 2026-05-06 15:31:39.481785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37de92450a32'
down_revision: Union[str, None] = ('3e2001dc7b6b', 'add_default_strategy_seed')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
