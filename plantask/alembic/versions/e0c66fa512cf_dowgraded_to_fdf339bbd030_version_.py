"""Dowgraded to 'fdf339bbd030' version because of mismatch issues

Revision ID: e0c66fa512cf
Revises: 2a08dcf7f8f9
Create Date: 2025-04-10 12:33:54.527688

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e0c66fa512cf'
down_revision: Union[str, None] = '2a08dcf7f8f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
