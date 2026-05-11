"""Final merge of all heads

Revision ID: final_merge_heads
Revises: 37de92450a32, add_cascade_delete_to_execution_plans_strategy_id
Create Date: 2026-05-11 14:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'final_merge_heads'
down_revision: Union[str, None] = ('37de92450a32', 'add_cascade_delete_to_execution_plans_strategy_id')
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Final merge of all migration heads."""
    pass


def downgrade() -> None:
    """Downgrade merged migrations."""
    pass
