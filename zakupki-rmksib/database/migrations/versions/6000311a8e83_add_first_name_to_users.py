"""Add first_name to users

Revision ID: 6000311a8e83
Revises: 005
Create Date: 2025-11-06 14:22:18.933364

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6000311a8e83'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавить колонку updated_at в таблицу users"""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()))

def downgrade() -> None:
    """Откатить добавление updated_at"""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('updated_at')