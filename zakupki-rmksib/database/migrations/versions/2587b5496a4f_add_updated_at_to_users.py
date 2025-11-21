"""Add updated_at to users

Revision ID: 2587b5496a4f
Revises: 6000311a8e83
Create Date: 2025-11-06 14:29:59.511149

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2587b5496a4f'
down_revision: Union[str, None] = '6000311a8e83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass



