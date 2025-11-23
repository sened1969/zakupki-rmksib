"""Extend user_preferences with email settings and budget

Revision ID: 007
Revises: 005
Create Date: 2024-11-16 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем поля для email настроек и бюджета
    op.add_column('user_preferences', sa.Column('email_password', sa.Text(), nullable=True))
    op.add_column('user_preferences', sa.Column('smtp_provider', sa.String(50), nullable=True))
    op.add_column('user_preferences', sa.Column('budget_min', sa.Integer(), nullable=True))
    op.add_column('user_preferences', sa.Column('budget_max', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('user_preferences', 'budget_max')
    op.drop_column('user_preferences', 'budget_min')
    op.drop_column('user_preferences', 'smtp_provider')
    op.drop_column('user_preferences', 'email_password')
















