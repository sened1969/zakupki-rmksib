"""Add user_preferences table

Revision ID: 005
Revises: 004
Create Date: 2024-01-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	op.create_table(
		'user_preferences',
		sa.Column('id', sa.Integer(), nullable=False),
		sa.Column('user_id', sa.Integer(), nullable=False),
		sa.Column('notify_enabled', sa.Boolean(), nullable=False, server_default='true'),
		sa.Column('customers', postgresql.JSON(astext_type=sa.Text()), nullable=True),
		sa.Column('nomenclature', postgresql.JSON(astext_type=sa.Text()), nullable=True),
		sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
		sa.PrimaryKeyConstraint('id')
	)


def downgrade() -> None:
	op.drop_table('user_preferences')






















