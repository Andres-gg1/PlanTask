"""merge heads

Revision ID: 3671a3978151
Revises: ac6a92ad8604, bb447ffd756a
Create Date: 2025-05-26 00:43:47.761378

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3671a3978151'
down_revision: Union[str, None] = ('ac6a92ad8604', 'bb447ffd756a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
