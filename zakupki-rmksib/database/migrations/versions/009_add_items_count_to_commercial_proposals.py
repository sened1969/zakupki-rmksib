"""add_items_count_to_commercial_proposals

Revision ID: 009
Revises: 008
Create Date: 2025-11-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add items_count column to commercial_proposals table
    op.add_column('commercial_proposals', sa.Column('items_count', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('commercial_proposals', 'items_count')

