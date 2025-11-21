"""add_commercial_proposals_table

Revision ID: 008
Revises: a3e1c116fe47
Create Date: 2025-11-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '008'
down_revision: Union[str, None] = 'a3e1c116fe47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create commercial_proposals table
    op.create_table(
        'commercial_proposals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lot_id', sa.Integer(), nullable=True),
        sa.Column('supplier_name', sa.String(length=255), nullable=False),
        sa.Column('supplier_inn', sa.String(length=12), nullable=True),
        sa.Column('proposal_file_path', sa.String(length=500), nullable=True),
        sa.Column('proposal_text', sa.Text(), nullable=True),
        sa.Column('product_price', sa.Float(), nullable=False),
        sa.Column('delivery_cost', sa.Float(), nullable=True),
        sa.Column('other_conditions', sa.Text(), nullable=True),
        sa.Column('supplier_rating', sa.Integer(), nullable=True),
        sa.Column('supplier_reliability_info', sa.Text(), nullable=True),
        sa.Column('integral_rating', sa.Float(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('analyzed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['lot_id'], ['lots.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('commercial_proposals')

