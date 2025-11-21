"""merge heads

Revision ID: 794880f5e35b
Revises: 007, 2587b5496a4f
Create Date: 2025-11-17 17:31:19.261478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '794880f5e35b'
down_revision: Union[str, None] = ('007', '2587b5496a4f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass








