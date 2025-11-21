"""add_url_field_to_lots

Revision ID: a3e1c116fe47
Revises: 7e0252659a62
Create Date: 2025-11-18 12:48:05.744884

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3e1c116fe47'
down_revision: Union[str, None] = '7e0252659a62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем поле url для хранения ссылки на страницу лота
    op.add_column('lots', sa.Column('url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('lots', 'url')
