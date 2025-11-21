"""add_review_status_to_lots

Revision ID: 010
Revises: 009
Create Date: 2025-11-20 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add review_status column to lots table
    op.add_column('lots', sa.Column('review_status', sa.String(length=50), nullable=True))
    
    # Set default value for existing lots: 'not_viewed'
    op.execute("UPDATE lots SET review_status = 'not_viewed' WHERE review_status IS NULL")


def downgrade() -> None:
    op.drop_column('lots', 'review_status')

