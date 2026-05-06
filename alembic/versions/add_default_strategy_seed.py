"""Add default strategy seed

Revision ID: add_default_strategy_seed
Revises: 16e47539e731
Create Date: 2026-05-06 19:10:00.000000

"""
from alembic import op

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
        '{"conditions":[{"indicator":"rsi","operator":"<","value":30}],"action":"buy"}'::jsonb,
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
