"""Add cascade delete to execution_plans.strategy_id

Revision ID: add_cascade_delete_to_execution_plans_strategy_id
Revises: b2c3d4e5f6g7_add_execution_plans_table
Create Date: 2026-05-11 14:38:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_cascade_delete_to_execution_plans_strategy_id'
down_revision = 'merge_all_heads'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add cascade delete to execution_plans.strategy_id foreign key."""
    
    # Drop existing foreign key constraint
    op.drop_constraint(
        'execution_plans_strategy_id_fkey',
        'execution_plans',
        type_='foreignkey'
    )
    
    # Add new constraint with CASCADE DELETE
    op.create_foreign_key(
        'execution_plans_strategy_id_fkey',
        'execution_plans',
        'strategies',
        ['strategy_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Remove cascade delete from execution_plans.strategy_id foreign key."""
    
    # Drop CASCADE constraint
    op.drop_constraint(
        'execution_plans_strategy_id_fkey',
        'execution_plans',
        type_='foreignkey'
    )
    
    # Add back original constraint without CASCADE
    op.create_foreign_key(
        'execution_plans_strategy_id_fkey',
        'execution_plans',
        'strategies',
        ['strategy_id'],
        ['id']
    )
