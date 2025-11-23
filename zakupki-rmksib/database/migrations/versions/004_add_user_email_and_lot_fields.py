"""Add user.contact_email and lot.customer/nomenclature

Revision ID: 004
Revises: 003
Create Date: 2024-01-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	# Add contact_email to users
	op.add_column('users', sa.Column('contact_email', sa.String(length=255), nullable=True))
	# Add customer and nomenclature to lots
	op.add_column('lots', sa.Column('customer', sa.String(length=255), nullable=True))
	op.add_column('lots', sa.Column('nomenclature', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
	op.drop_column('lots', 'nomenclature')
	op.drop_column('lots', 'customer')
	op.drop_column('users', 'contact_email')






















