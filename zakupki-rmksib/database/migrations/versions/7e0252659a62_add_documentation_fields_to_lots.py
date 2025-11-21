"""add_documentation_fields_to_lots

Revision ID: 7e0252659a62
Revises: 794880f5e35b
Create Date: 2025-11-17 19:04:46.724219

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e0252659a62'
down_revision: Union[str, None] = '794880f5e35b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем поля для документации в таблицу lots
    op.add_column('lots', sa.Column('documentation_path', sa.String(length=500), nullable=True))
    op.add_column('lots', sa.Column('documentation_text', sa.Text(), nullable=True))
    op.add_column('lots', sa.Column('documentation_analyzed', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('lots', sa.Column('source', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('lots', 'source')
    op.drop_column('lots', 'documentation_analyzed')
    op.drop_column('lots', 'documentation_text')
    op.drop_column('lots', 'documentation_path')








