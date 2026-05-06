"""Add default strategy seed

Revision ID: add_default_strategy_seed
Revises: 16e47539e731
Create Date: 2026-05-06 19:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_default_strategy_seed'
down_revision: Union[str, None] = '16e47539e731'
branch_labels: Union[str, Sequence[str]] = None
depends_on: Union[str, Sequence[str]] = None

def upgrade() -> None:
    op.execute("""
    INSERT INTO strategies (
        id,
        user_id,
        name,
        description,
        is_active,
        dsl_definition,
        dsl_hash,
        version,
        created_at,
        updated_at
    )
    SELECT
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000000',
        'Default Strategy',
        'System default strategy',
        true,
        '{
    "version": 1,
    "action": "buy",
    "root": {
        "type": "AND",
        "children": [
            {
                "type": "condition",
                "left": {"type": "indicator", "name": "RSI", "params": {"period": 14}},
                "operator": "<",
                "right": {"type": "constant", "value": 30}
            },
            {
                "type": "condition",
                "left": {"type": "indicator", "name": "MACD", "params": {"fast": 12, "slow": 26, "signal": 9}},
                "operator": "cross_above",
                "right": {"type": "indicator", "name": "MACD", "params": {"fast": 12, "slow": 26, "signal": 9}}
            },
            {
                "type": "condition",
                "left": {"type": "price", "field": "close"},
                "operator": ">",
                "right": {"type": "indicator", "name": "EMA", "params": {"period": 20}}
            }
        ]
    }
}'::jsonb,
        NULL,
        1,
        now(),
        now()
    WHERE NOT EXISTS (
        SELECT 1 FROM strategies WHERE id = '00000000-0000-0000-0000-000000000001'
    );
    """)

def downgrade() -> None:
    op.execute("""
    DELETE FROM strategies WHERE id = '00000000-0000-0000-0000-000000000001';
    """)
