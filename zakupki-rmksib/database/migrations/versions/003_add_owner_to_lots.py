"""Add owner_id to lots table

Revision ID: 003
Revises: 002
Create Date: 2025-11-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade() -> None:
    with op.batch_alter_table('lots', schema=None) as batch_op:
        batch_op.add_column(sa.Column('owner_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_lots_owner_id',  # constraint name
            'users',              # remote table
            ['owner_id'],         # local columns (as list)
            ['id']                # remote columns (as list)
        )

def downgrade() -> None:
    with op.batch_alter_table('lots', schema=None) as batch_op:
        batch_op.drop_constraint('fk_lots_owner_id', type_='foreignkey')
        batch_op.drop_column('owner_id')
